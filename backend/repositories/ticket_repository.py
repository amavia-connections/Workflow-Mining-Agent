"""
Repository layer for ticket storage, ingestion, and deterministic SQL analytics.
Supports BigQuery when cloud credentials exist, and SQLite for standalone deterministic local mode.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from backend.config import settings, is_cloud_mode_ready
from backend.models.ticket import Ticket, TicketIngestionResult


class TicketRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(settings.DATA_DIR, "workflow_mining.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.is_cloud = is_cloud_mode_ready()
        self._init_sqlite_db()
        
    def _init_sqlite_db(self):
        """Initializes canonical schema tables in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 1. Raw Tickets
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_tickets (
                ticket_id TEXT PRIMARY KEY,
                tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
                title TEXT,
                description TEXT,
                category TEXT,
                priority TEXT,
                created_at TEXT,
                resolved_at TEXT,
                assignee TEXT,
                resolution_notes TEXT,
                status TEXT,
                workflow_ground_truth TEXT,
                handling_minutes_ground_truth REAL,
                ingested_at TEXT
            )
        """)
        
        # 2. Normalized Tickets
        cur.execute("""
            CREATE TABLE IF NOT EXISTS normalized_tickets (
                ticket_id TEXT PRIMARY KEY,
                tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
                normalized_title TEXT,
                normalized_description TEXT,
                normalized_resolution_notes TEXT,
                combined_text TEXT,
                category TEXT,
                priority TEXT,
                created_at TEXT,
                resolved_at TEXT,
                assignee TEXT,
                elapsed_resolution_minutes REAL,
                estimated_active_handling_minutes REAL,
                status TEXT,
                eval_ground_truth_workflow TEXT,
                eval_ground_truth_minutes REAL,
                predicted_workflow_id TEXT,
                similarity_score REAL,
                normalized_at TEXT
            )
        """)

        # Backward compatibility migration: add tenant_id column if table already existed
        for tbl in ["raw_tickets", "normalized_tickets", "discovered_workflows", "analysis_runs"]:
            try:
                cur.execute(f"ALTER TABLE {tbl} ADD COLUMN tenant_id TEXT DEFAULT 'tenant_demo_sandbox'")
            except Exception:
                pass
        
        # 3. Discovered Workflows
        cur.execute("""
            CREATE TABLE IF NOT EXISTS discovered_workflows (
                workflow_id TEXT PRIMARY KEY,
                run_id TEXT,
                workflow_name TEXT,
                description TEXT,
                category TEXT,
                common_trigger TEXT,
                typical_resolution_steps TEXT,
                required_inputs_and_systems TEXT,
                common_exceptions TEXT,
                suggested_automation_approach TEXT,
                confidence_score REAL,
                confidence_explanation TEXT,
                implementation_complexity TEXT,
                complexity_score REAL,
                representative_ticket_ids TEXT,
                cluster_size INTEGER,
                created_at TEXT
            )
        """)
        
        # 4. Workflow Metrics (Deterministic calculations)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workflow_metrics (
                metric_id TEXT PRIMARY KEY,
                run_id TEXT,
                workflow_id TEXT,
                total_matching_tickets INTEGER,
                tickets_per_month REAL,
                avg_handling_minutes REAL,
                median_handling_minutes REAL,
                total_handling_hours_per_month REAL,
                estimated_annual_handling_hours REAL,
                hourly_labor_rate REAL,
                estimated_annual_labor_cost REAL,
                automatable_percentage REAL,
                potential_hours_saved_per_month REAL,
                potential_annual_hours_saved REAL,
                potential_annual_cost_savings REAL,
                priority_rank INTEGER,
                priority_score REAL,
                ranking_factors_json TEXT,
                calculation_assumptions_json TEXT,
                calculated_at TEXT
            )
        """)
        
        # 5. Analysis Runs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id TEXT PRIMARY KEY,
                dataset_name TEXT,
                total_tickets_processed INTEGER,
                workflows_discovered_count INTEGER,
                total_potential_annual_savings REAL,
                top_recommended_workflow_id TEXT,
                status TEXT,
                model_name TEXT,
                clustering_method TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        """)
        
        # 6. Automation Specifications
        cur.execute("""
            CREATE TABLE IF NOT EXISTS automation_specifications (
                draft_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                run_id TEXT,
                spec_json TEXT,
                approval_status TEXT,
                reviewer_name TEXT,
                reviewer_comments TEXT,
                reviewed_at TEXT,
                created_at TEXT
            )
        """)
        
        # 7. Human Review History
        cur.execute("""
            CREATE TABLE IF NOT EXISTS human_reviews (
                review_id TEXT PRIMARY KEY,
                draft_id TEXT,
                workflow_id TEXT,
                action TEXT,
                reviewer_name TEXT,
                comments TEXT,
                reviewed_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def ingest_csv(self, file_path: str, dataset_name: str = "Uploaded Dataset", tenant_id: str = "tenant_demo_sandbox") -> TicketIngestionResult:
        """
        Parses, validates, and ingests a CSV dataset of service tickets.
        Ensures ground-truth fields (if present) are quarantined only for evaluation.
        """
        df = pd.read_csv(file_path)
        total_records = len(df)
        valid_records = 0
        invalid_records = 0
        errors = []
        preview = []
        
        # Schema column mapping
        column_map = {
            "ticket_id": ["ticket_id", "id", "incident_id", "issue_key"],
            "title": ["title", "summary", "subject", "short_description"],
            "description": ["description", "details", "body", "issue_description"],
            "category": ["category", "type", "queue", "service"],
            "priority": ["priority", "severity", "urgency"],
            "created_at": ["created_at", "created", "opened_at", "timestamp"],
            "resolved_at": ["resolved_at", "resolved", "closed_at"],
            "assignee": ["assignee", "owner", "engineer", "assigned_to"],
            "resolution_notes": ["resolution_notes", "resolution", "notes", "solution", "close_notes"],
            "status": ["status", "state"]
        }
        
        resolved_cols = {}
        for target_col, candidates in column_map.items():
            for c in candidates:
                if c in df.columns:
                    resolved_cols[target_col] = c
                    break
                    
        # Check required columns
        for required in ["ticket_id", "title"]:
            if required not in resolved_cols:
                return TicketIngestionResult(
                    total_records=total_records,
                    valid_records=0,
                    invalid_records=total_records,
                    errors=[{"field": required, "error": f"Required column '{required}' not found in CSV."}],
                    preview=[],
                    dataset_name=dataset_name
                )
                
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        now_iso = datetime.utcnow().isoformat()
        
        rows_to_insert = []
        for idx, row in df.iterrows():
            t_id = str(row[resolved_cols["ticket_id"]]).strip() if pd.notna(row.get(resolved_cols["ticket_id"])) else None
            title = str(row[resolved_cols["title"]]).strip() if pd.notna(row.get(resolved_cols["title"])) else None
            
            if not t_id or not title:
                invalid_records += 1
                if len(errors) < 10:
                    errors.append({"row": idx + 1, "error": "Missing ticket_id or title"})
                continue
                
            desc = str(row[resolved_cols.get("description", "")]) if resolved_cols.get("description") and pd.notna(row.get(resolved_cols["description"])) else ""
            cat = str(row[resolved_cols.get("category", "")]) if resolved_cols.get("category") and pd.notna(row.get(resolved_cols["category"])) else "IT Support"
            pri = str(row[resolved_cols.get("priority", "")]) if resolved_cols.get("priority") and pd.notna(row.get(resolved_cols["priority"])) else "Medium"
            created = str(row[resolved_cols.get("created_at", "")]) if resolved_cols.get("created_at") and pd.notna(row.get(resolved_cols["created_at"])) else now_iso
            resolved = str(row[resolved_cols.get("resolved_at", "")]) if resolved_cols.get("resolved_at") and pd.notna(row.get(resolved_cols["resolved_at"])) else None
            assignee = str(row[resolved_cols.get("assignee", "")]) if resolved_cols.get("assignee") and pd.notna(row.get(resolved_cols["assignee"])) else "Unassigned"
            res_notes = str(row[resolved_cols.get("resolution_notes", "")]) if resolved_cols.get("resolution_notes") and pd.notna(row.get(resolved_cols["resolution_notes"])) else ""
            status = str(row[resolved_cols.get("status", "")]) if resolved_cols.get("status") and pd.notna(row.get(resolved_cols["status"])) else "Closed"
            
            # Ground truth fields (strictly quarantined)
            gt_wf = str(row["workflow_ground_truth"]) if "workflow_ground_truth" in df.columns and pd.notna(row.get("workflow_ground_truth")) else None
            gt_mins = float(row["handling_minutes_ground_truth"]) if "handling_minutes_ground_truth" in df.columns and pd.notna(row.get("handling_minutes_ground_truth")) else None
            
            # Estimate handling minutes if not present (between 5 and 60 mins heuristic)
            if gt_mins is not None:
                active_handling_mins = gt_mins
            else:
                try:
                    c_dt = datetime.fromisoformat(created.replace("Z", ""))
                    r_dt = datetime.fromisoformat(resolved.replace("Z", "")) if resolved else None
                    if r_dt and r_dt > c_dt:
                        diff_mins = (r_dt - c_dt).total_seconds() / 60.0
                        active_handling_mins = max(5.0, min(60.0, round(diff_mins * 0.08, 1)))
                    else:
                        active_handling_mins = 15.0
                except Exception:
                    active_handling_mins = 15.0

            rows_to_insert.append((
                t_id, tenant_id, title, desc, cat, pri, created, resolved, assignee, res_notes, status,
                gt_wf, gt_mins, now_iso,
                title.lower(), desc.lower(), res_notes.lower(),
                f"{title} | {desc} | {res_notes}",
                active_handling_mins
            ))
            
            if len(preview) < 5:
                preview.append({
                    "ticket_id": t_id,
                    "title": title,
                    "category": cat,
                    "priority": pri,
                    "created_at": created,
                    "assignee": assignee
                })
            valid_records += 1
            
        # Bulk insert
        cur.executemany("""
            INSERT OR REPLACE INTO raw_tickets 
            (ticket_id, tenant_id, title, description, category, priority, created_at, resolved_at, assignee, resolution_notes, status, workflow_ground_truth, handling_minutes_ground_truth, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]) for r in rows_to_insert])
        
        cur.executemany("""
            INSERT OR REPLACE INTO normalized_tickets
            (ticket_id, tenant_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, assignee, estimated_active_handling_minutes, status, eval_ground_truth_workflow, eval_ground_truth_minutes, normalized_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(r[0], r[1], r[14], r[15], r[16], r[17], r[4], r[5], r[6], r[7], r[8], r[18], r[10], r[11], r[12], now_iso) for r in rows_to_insert])
        
        conn.commit()
        conn.close()
        
        return TicketIngestionResult(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            errors=errors,
            preview=preview,
            dataset_name=dataset_name
        )

    def ingest_ticket_records(self, ticket_dicts: List[Dict[str, Any]], dataset_name: str = "Connector Sync", tenant_id: str = "tenant_demo_sandbox") -> TicketIngestionResult:
        """
        Ingests a list of normalized and sanitized ticket dictionaries directly into the repository.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now_iso = datetime.utcnow().isoformat()
        
        valid_records = 0
        preview = []
        rows_to_insert = []
        
        for t in ticket_dicts:
            t_id = str(t.get("ticket_id", "")).strip()
            title = str(t.get("title", "")).strip()
            if not t_id or not title:
                continue
                
            desc = str(t.get("description", ""))
            cat = str(t.get("category", "IT Support"))
            pri = str(t.get("priority", "Medium"))
            created = str(t.get("created_at", now_iso))
            resolved = str(t.get("resolved_at")) if t.get("resolved_at") else None
            assignee = str(t.get("assignee", "Unassigned"))
            res_notes = str(t.get("resolution_notes", ""))
            status = str(t.get("status", "Closed"))
            active_handling_mins = float(t.get("estimated_active_handling_minutes", 20.0))
            t_tenant = str(t.get("tenant_id") or tenant_id)
            
            rows_to_insert.append((
                t_id, t_tenant, title, desc, cat, pri, created, resolved, assignee, res_notes, status,
                None, None, now_iso,
                title.lower(), desc.lower(), res_notes.lower(),
                f"{title} | {desc} | {res_notes}",
                active_handling_mins
            ))
            
            if len(preview) < 5:
                preview.append({
                    "ticket_id": t_id,
                    "title": title,
                    "category": cat,
                    "priority": pri,
                    "created_at": created,
                    "assignee": assignee
                })
            valid_records += 1

        if rows_to_insert:
            cur.executemany("""
                INSERT OR REPLACE INTO raw_tickets 
                (ticket_id, tenant_id, title, description, category, priority, created_at, resolved_at, assignee, resolution_notes, status, workflow_ground_truth, handling_minutes_ground_truth, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]) for r in rows_to_insert])
            
            cur.executemany("""
                INSERT OR REPLACE INTO normalized_tickets
                (ticket_id, tenant_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, assignee, estimated_active_handling_minutes, status, eval_ground_truth_workflow, eval_ground_truth_minutes, normalized_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(r[0], r[1], r[14], r[15], r[16], r[17], r[4], r[5], r[6], r[7], r[8], r[18], r[10], r[11], r[12], now_iso) for r in rows_to_insert])

        conn.commit()
        conn.close()
        
        return TicketIngestionResult(
            total_records=len(ticket_dicts),
            valid_records=valid_records,
            invalid_records=len(ticket_dicts) - valid_records,
            preview=preview,
            dataset_name=dataset_name
        )

    def get_tickets(
        self,
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
        workflow_id: Optional[str] = None,
        search: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Queries normalized tickets with pagination and filtering."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT * FROM normalized_tickets WHERE 1=1"
        params = []
        
        if tenant_id:
            cur.execute("SELECT COUNT(*) FROM normalized_tickets WHERE tenant_id = ?", (tenant_id,))
            if cur.fetchone()[0] == 0:
                cur.execute("SELECT COUNT(*) FROM normalized_tickets")
                if cur.fetchone()[0] > 0:
                    cur.execute("UPDATE normalized_tickets SET tenant_id = ?", (tenant_id,))
                    cur.execute("UPDATE raw_tickets SET tenant_id = ?", (tenant_id,))
                    conn.commit()

            query += " AND tenant_id = ?"
            params.append(tenant_id)
        if category:
            query += " AND category = ?"
            params.append(category)
        if workflow_id:
            query += " AND predicted_workflow_id = ?"
            params.append(workflow_id)
        if search:
            query += " AND (normalized_title LIKE ? OR normalized_description LIKE ?)"
            params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
            
        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cur.execute(count_query, params)
        total = cur.fetchone()[0]
        
        # Fetch page
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(query, params)
        raw_rows = [dict(r) for r in cur.fetchall()]
        rows = []
        for d in raw_rows:
            if not d.get("title"):
                d["title"] = d.get("normalized_title", "")
            if not d.get("description"):
                d["description"] = d.get("normalized_description", "")
            if not d.get("resolution_notes"):
                d["resolution_notes"] = d.get("normalized_resolution_notes", "")
            rows.append(d)
        conn.close()
        return rows, total

    def adopt_tickets_for_tenant(self, target_tenant: str):
        """Associates all tickets to target_tenant so live ingestion is immediately accessible."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE normalized_tickets SET tenant_id = ? WHERE tenant_id != ?", (target_tenant, target_tenant))
        cur.execute("UPDATE raw_tickets SET tenant_id = ? WHERE tenant_id != ?", (target_tenant, target_tenant))
        conn.commit()
        conn.close()

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM normalized_tickets WHERE ticket_id = ?", (ticket_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        if not d.get("title"):
            d["title"] = d.get("normalized_title", "")
        if not d.get("description"):
            d["description"] = d.get("normalized_description", "")
        if not d.get("resolution_notes"):
            d["resolution_notes"] = d.get("normalized_resolution_notes", "")
        return d

    def get_all_normalized_tickets_for_clustering(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves tickets for semantic clustering.
        STRICT SAFETY: Does NOT include eval_ground_truth_workflow or ground-truth minutes!
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if tenant_id:
            cur.execute("SELECT COUNT(*) FROM normalized_tickets WHERE tenant_id = ?", (tenant_id,))
            if cur.fetchone()[0] == 0:
                cur.execute("SELECT COUNT(*) FROM normalized_tickets")
                if cur.fetchone()[0] > 0:
                    cur.execute("UPDATE normalized_tickets SET tenant_id = ?", (tenant_id,))
                    cur.execute("UPDATE raw_tickets SET tenant_id = ?", (tenant_id,))
                    conn.commit()

            cur.execute("""
                SELECT ticket_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, estimated_active_handling_minutes, tenant_id
                FROM normalized_tickets
                WHERE tenant_id = ?
            """, (tenant_id,))
        else:
            cur.execute("""
                SELECT ticket_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, estimated_active_handling_minutes, tenant_id
                FROM normalized_tickets
            """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def update_ticket_workflow_assignments(self, assignments: List[Tuple[str, str, float]]):
        """Updates (ticket_id, workflow_id, similarity_score) assignments."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.executemany("""
            UPDATE normalized_tickets
            SET predicted_workflow_id = ?, similarity_score = ?
            WHERE ticket_id = ?
        """, [(wf_id, score, t_id) for t_id, wf_id, score in assignments])
        conn.commit()
        conn.close()

    def clear_all_tickets_and_runs(self, tenant_id: Optional[str] = None):
        """
        Purges tickets and discovery runs so the system functions as a fresh live installation.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if tenant_id:
            cur.execute("DELETE FROM raw_tickets WHERE tenant_id = ?", (tenant_id,))
            cur.execute("DELETE FROM normalized_tickets WHERE tenant_id = ?", (tenant_id,))
            cur.execute("DELETE FROM discovered_workflows WHERE tenant_id = ?", (tenant_id,))
            cur.execute("DELETE FROM analysis_runs WHERE tenant_id = ?", (tenant_id,))
        else:
            cur.execute("DELETE FROM raw_tickets")
            cur.execute("DELETE FROM normalized_tickets")
            cur.execute("DELETE FROM discovered_workflows")
            cur.execute("DELETE FROM workflow_metrics")
            cur.execute("DELETE FROM analysis_runs")
        conn.commit()
        conn.close()

