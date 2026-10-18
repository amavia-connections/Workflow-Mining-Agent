"""
Repository layer for ticket storage, ingestion, and deterministic SQL analytics.
Supports PostgreSQL (Cloud SQL, Supabase, Neon, etc.) via DATABASE_URL with automatic schema creation,
and SQLite for standalone deterministic local mode.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, unquote
import pandas as pd

from backend.config import settings, is_cloud_mode_ready
from backend.models.ticket import Ticket, TicketIngestionResult

import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class TicketRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(settings.DATA_DIR, "workflow_mining.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.is_cloud = is_cloud_mode_ready()
        
        # Determine PostgreSQL vs SQLite
        # If running pytest or automated tests, use fast local SQLite to keep tests deterministic and sub-second
        is_test_env = "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        db_url = getattr(settings, "DATABASE_URL", "") or os.environ.get("DATABASE_URL", "")
        self.is_postgres = False
        self.pg_config = {}
        
        if not is_test_env and PSYCOPG2_AVAILABLE and (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
            try:
                parsed = urlparse(db_url)
                self.pg_config = {
                    "dbname": parsed.path.lstrip("/"),
                    "user": parsed.username,
                    "password": unquote(parsed.password) if parsed.password else None,
                    "host": parsed.hostname,
                    "port": parsed.port or 5432,
                    "connect_timeout": 6
                }
                # Probe connection
                test_conn = psycopg2.connect(**self.pg_config)
                test_conn.close()
                self.is_postgres = True
                print(f"[Database] Connected to PostgreSQL at {self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['dbname']}")
            except Exception as e:
                print(f"[Database Warning] Could not connect to PostgreSQL ({e}). Falling back to SQLite.")
                self.is_postgres = False

        self._init_db()

    def _get_connection(self):
        """Returns active database connection (PostgreSQL or SQLite)."""
        if self.is_postgres:
            return psycopg2.connect(**self.pg_config)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _format_query(self, query: str) -> str:
        """Adapts parameter placeholders: '?' for SQLite, '%s' for PostgreSQL."""
        if self.is_postgres:
            return query.replace("?", "%s")
        return query

    def _init_db(self):
        """Initializes tables across PostgreSQL or SQLite."""
        conn = self._get_connection()
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

        # 3. Discovered Workflows
        cur.execute("""
            CREATE TABLE IF NOT EXISTS discovered_workflows (
                workflow_id TEXT PRIMARY KEY,
                tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
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
                metrics_json TEXT,
                created_at TEXT
            )
        """)

        # 4. Workflow Metrics
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
                tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
                dataset_name TEXT,
                total_tickets_processed INTEGER,
                workflows_discovered_count INTEGER,
                total_potential_annual_savings REAL,
                top_recommended_workflow_id TEXT,
                status TEXT,
                message TEXT,
                progress INTEGER,
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
                tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
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
        """Parses, validates, and ingests a CSV dataset of service tickets."""
        df = pd.read_csv(file_path)
        total_records = len(df)
        valid_records = 0
        invalid_records = 0
        errors = []
        preview = []
        
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
            
            gt_wf = str(row["workflow_ground_truth"]) if "workflow_ground_truth" in df.columns and pd.notna(row.get("workflow_ground_truth")) else None
            gt_mins = float(row["handling_minutes_ground_truth"]) if "handling_minutes_ground_truth" in df.columns and pd.notna(row.get("handling_minutes_ground_truth")) else None
            
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
                title, desc, res_notes,
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

        self._upsert_ticket_rows(rows_to_insert)

        return TicketIngestionResult(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            errors=errors,
            preview=preview,
            dataset_name=dataset_name
        )

    def ingest_ticket_records(self, ticket_dicts: List[Dict[str, Any]], dataset_name: str = "Connector Sync", tenant_id: str = "tenant_demo_sandbox") -> TicketIngestionResult:
        """Ingests a list of normalized and sanitized ticket dictionaries directly into PostgreSQL or SQLite."""
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
                title, desc, res_notes,
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
            self._upsert_ticket_rows(rows_to_insert)

        return TicketIngestionResult(
            total_records=len(ticket_dicts),
            valid_records=valid_records,
            invalid_records=len(ticket_dicts) - valid_records,
            preview=preview,
            dataset_name=dataset_name
        )

    def _upsert_ticket_rows(self, rows_to_insert: List[Tuple]):
        """Executes database UPSERT for raw and normalized tickets across PostgreSQL or SQLite."""
        if not rows_to_insert:
            return

        conn = self._get_connection()
        cur = conn.cursor()
        now_iso = datetime.utcnow().isoformat()

        if self.is_postgres:
            raw_sql = """
                INSERT INTO raw_tickets (
                    ticket_id, tenant_id, title, description, category, priority, created_at, resolved_at, assignee, resolution_notes, status, workflow_ground_truth, handling_minutes_ground_truth, ingested_at
                ) VALUES %s
                ON CONFLICT (ticket_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    priority = EXCLUDED.priority,
                    created_at = EXCLUDED.created_at,
                    resolved_at = EXCLUDED.resolved_at,
                    assignee = EXCLUDED.assignee,
                    resolution_notes = EXCLUDED.resolution_notes,
                    status = EXCLUDED.status,
                    ingested_at = EXCLUDED.ingested_at;
            """
            norm_sql = """
                INSERT INTO normalized_tickets (
                    ticket_id, tenant_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, assignee, estimated_active_handling_minutes, status, eval_ground_truth_workflow, eval_ground_truth_minutes, normalized_at
                ) VALUES %s
                ON CONFLICT (ticket_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    normalized_title = EXCLUDED.normalized_title,
                    normalized_description = EXCLUDED.normalized_description,
                    normalized_resolution_notes = EXCLUDED.normalized_resolution_notes,
                    combined_text = EXCLUDED.combined_text,
                    category = EXCLUDED.category,
                    priority = EXCLUDED.priority,
                    created_at = EXCLUDED.created_at,
                    resolved_at = EXCLUDED.resolved_at,
                    assignee = EXCLUDED.assignee,
                    estimated_active_handling_minutes = EXCLUDED.estimated_active_handling_minutes,
                    status = EXCLUDED.status,
                    normalized_at = EXCLUDED.normalized_at;
            """
            raw_params = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]) for r in rows_to_insert]
            norm_params = [(r[0], r[1], r[14], r[15], r[16], r[17], r[4], r[5], r[6], r[7], r[8], r[18], r[10], r[11], r[12], now_iso) for r in rows_to_insert]
            execute_values(cur, raw_sql, raw_params)
            execute_values(cur, norm_sql, norm_params)
        else:
            raw_sql = """
                INSERT OR REPLACE INTO raw_tickets 
                (ticket_id, tenant_id, title, description, category, priority, created_at, resolved_at, assignee, resolution_notes, status, workflow_ground_truth, handling_minutes_ground_truth, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            norm_sql = """
                INSERT OR REPLACE INTO normalized_tickets
                (ticket_id, tenant_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, assignee, estimated_active_handling_minutes, status, eval_ground_truth_workflow, eval_ground_truth_minutes, normalized_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            raw_params = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]) for r in rows_to_insert]
            norm_params = [(r[0], r[1], r[14], r[15], r[16], r[17], r[4], r[5], r[6], r[7], r[8], r[18], r[10], r[11], r[12], now_iso) for r in rows_to_insert]
            cur.executemany(raw_sql, raw_params)
            cur.executemany(norm_sql, norm_params)

        conn.commit()
        conn.close()

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
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()
        
        query = "SELECT * FROM normalized_tickets WHERE 1=1"
        params = []
        
        if tenant_id:
            cur.execute(self._format_query("SELECT COUNT(*) FROM normalized_tickets WHERE tenant_id = ?"), (tenant_id,))
            res_val = cur.fetchone()
            count_val = res_val["count"] if (self.is_postgres and isinstance(res_val, dict)) else (res_val[0] if res_val else 0)
            if count_val == 0:
                cur.execute("SELECT COUNT(*) FROM normalized_tickets")
                res_all = cur.fetchone()
                total_any = res_all["count"] if (self.is_postgres and isinstance(res_all, dict)) else (res_all[0] if res_all else 0)
                if total_any > 0:
                    cur.execute(self._format_query("UPDATE normalized_tickets SET tenant_id = ?"), (tenant_id,))
                    cur.execute(self._format_query("UPDATE raw_tickets SET tenant_id = ?"), (tenant_id,))
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
            query += " AND (LOWER(normalized_title) LIKE ? OR LOWER(normalized_description) LIKE ?)"
            params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
            
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cur.execute(self._format_query(count_query), params)
        res_cnt = cur.fetchone()
        total = res_cnt["count"] if (self.is_postgres and isinstance(res_cnt, dict)) else (res_cnt[0] if res_cnt else 0)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(self._format_query(query), params)
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
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(self._format_query("UPDATE normalized_tickets SET tenant_id = ? WHERE tenant_id != ?"), (target_tenant, target_tenant))
        cur.execute(self._format_query("UPDATE raw_tickets SET tenant_id = ? WHERE tenant_id != ?"), (target_tenant, target_tenant))
        conn.commit()
        conn.close()

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()
        cur.execute(self._format_query("SELECT * FROM normalized_tickets WHERE ticket_id = ?"), (ticket_id,))
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
        """Retrieves tickets for semantic clustering without ground-truth fields."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()
        if tenant_id:
            cur.execute(self._format_query("SELECT COUNT(*) FROM normalized_tickets WHERE tenant_id = ?"), (tenant_id,))
            res_val = cur.fetchone()
            count_val = res_val["count"] if (self.is_postgres and isinstance(res_val, dict)) else (res_val[0] if res_val else 0)
            if count_val == 0:
                cur.execute("SELECT COUNT(*) FROM normalized_tickets")
                res_all = cur.fetchone()
                total_any = res_all["count"] if (self.is_postgres and isinstance(res_all, dict)) else (res_all[0] if res_all else 0)
                if total_any > 0:
                    cur.execute(self._format_query("UPDATE normalized_tickets SET tenant_id = ?"), (tenant_id,))
                    cur.execute(self._format_query("UPDATE raw_tickets SET tenant_id = ?"), (tenant_id,))
                    conn.commit()

            cur.execute(self._format_query("""
                SELECT ticket_id, normalized_title, normalized_description, normalized_resolution_notes, combined_text, category, priority, created_at, resolved_at, estimated_active_handling_minutes, tenant_id
                FROM normalized_tickets
                WHERE tenant_id = ?
            """), (tenant_id,))
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
        if not assignments:
            return
        conn = self._get_connection()
        cur = conn.cursor()
        sql = self._format_query("""
            UPDATE normalized_tickets
            SET predicted_workflow_id = ?, similarity_score = ?
            WHERE ticket_id = ?
        """)
        cur.executemany(sql, [(wf_id, score, t_id) for t_id, wf_id, score in assignments])
        conn.commit()
        conn.close()

    def clear_all_tickets_and_runs(self, tenant_id: Optional[str] = None):
        """Purges tickets and discovery runs so the system functions as a fresh live installation."""
        conn = self._get_connection()
        cur = conn.cursor()
        if tenant_id:
            cur.execute(self._format_query("DELETE FROM raw_tickets WHERE tenant_id = ?"), (tenant_id,))
            cur.execute(self._format_query("DELETE FROM normalized_tickets WHERE tenant_id = ?"), (tenant_id,))
            cur.execute(self._format_query("DELETE FROM discovered_workflows WHERE tenant_id = ?"), (tenant_id,))
            cur.execute(self._format_query("DELETE FROM automation_specifications WHERE tenant_id = ?"), (tenant_id,))
            cur.execute(self._format_query("DELETE FROM analysis_runs WHERE tenant_id = ?"), (tenant_id,))
        else:
            cur.execute("DELETE FROM raw_tickets")
            cur.execute("DELETE FROM normalized_tickets")
            cur.execute("DELETE FROM discovered_workflows")
            cur.execute("DELETE FROM workflow_metrics")
            cur.execute("DELETE FROM automation_specifications")
            cur.execute("DELETE FROM analysis_runs")
        conn.commit()
        conn.close()

    # =========================================================================
    # Persistent Workflow Discovery & Specification Storage (Never Resets)
    # =========================================================================

    def save_workflows(self, workflows: List[Any], run_id: str, tenant_id: str = "tenant_demo_sandbox"):
        """Persists discovered workflows and their deterministic metrics into PostgreSQL or SQLite."""
        if not workflows:
            return
        conn = self._get_connection()
        cur = conn.cursor()
        now_iso = datetime.utcnow().isoformat()

        if self.is_postgres:
            upsert_sql = """
                INSERT INTO discovered_workflows (
                    workflow_id, tenant_id, run_id, workflow_name, description, category, common_trigger,
                    typical_resolution_steps, required_inputs_and_systems, common_exceptions, suggested_automation_approach,
                    confidence_score, confidence_explanation, implementation_complexity, complexity_score,
                    representative_ticket_ids, cluster_size, metrics_json, created_at
                ) VALUES %s
                ON CONFLICT (workflow_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    run_id = EXCLUDED.run_id,
                    workflow_name = EXCLUDED.workflow_name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    common_trigger = EXCLUDED.common_trigger,
                    typical_resolution_steps = EXCLUDED.typical_resolution_steps,
                    required_inputs_and_systems = EXCLUDED.required_inputs_and_systems,
                    common_exceptions = EXCLUDED.common_exceptions,
                    suggested_automation_approach = EXCLUDED.suggested_automation_approach,
                    confidence_score = EXCLUDED.confidence_score,
                    confidence_explanation = EXCLUDED.confidence_explanation,
                    implementation_complexity = EXCLUDED.implementation_complexity,
                    complexity_score = EXCLUDED.complexity_score,
                    representative_ticket_ids = EXCLUDED.representative_ticket_ids,
                    cluster_size = EXCLUDED.cluster_size,
                    metrics_json = EXCLUDED.metrics_json,
                    created_at = EXCLUDED.created_at;
            """
        else:
            upsert_sql = """
                INSERT OR REPLACE INTO discovered_workflows (
                    workflow_id, tenant_id, run_id, workflow_name, description, category, common_trigger,
                    typical_resolution_steps, required_inputs_and_systems, common_exceptions, suggested_automation_approach,
                    confidence_score, confidence_explanation, implementation_complexity, complexity_score,
                    representative_ticket_ids, cluster_size, metrics_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        rows = []
        for w in workflows:
            w_dict = w.model_dump(mode="json") if hasattr(w, "model_dump") else (w if isinstance(w, dict) else {})
            metrics_str = json.dumps(w_dict.get("metrics", {}))
            rows.append((
                w_dict.get("workflow_id"),
                tenant_id,
                run_id,
                w_dict.get("workflow_name"),
                w_dict.get("description"),
                w_dict.get("category", "IT Support"),
                w_dict.get("common_trigger", ""),
                json.dumps(w_dict.get("typical_resolution_steps", [])),
                json.dumps(w_dict.get("required_inputs_and_systems", [])),
                json.dumps(w_dict.get("common_exceptions", [])),
                w_dict.get("suggested_automation_approach", ""),
                float(w_dict.get("confidence_score", 0.8)),
                w_dict.get("confidence_explanation", ""),
                w_dict.get("implementation_complexity", "Medium"),
                float(w_dict.get("complexity_score", 0.4)),
                json.dumps(w_dict.get("representative_ticket_ids", [])),
                int(w_dict.get("cluster_size", 0)),
                metrics_str,
                now_iso
            ))

        if self.is_postgres:
            execute_values(cur, upsert_sql, rows)
        else:
            cur.executemany(upsert_sql, rows)
        conn.commit()
        conn.close()

    def get_discovered_workflows(self, run_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves persisted workflows from database."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()

        query = "SELECT * FROM discovered_workflows WHERE 1=1"
        params = []
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)

        query += " ORDER BY workflow_id ASC"
        cur.execute(self._format_query(query), params)
        raw_rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        results = []
        for r in raw_rows:
            try:
                metrics = json.loads(r.get("metrics_json", "{}")) if r.get("metrics_json") else {}
                steps = json.loads(r.get("typical_resolution_steps", "[]")) if r.get("typical_resolution_steps") else []
                systems = json.loads(r.get("required_inputs_and_systems", "[]")) if r.get("required_inputs_and_systems") else []
                exceptions = json.loads(r.get("common_exceptions", "[]")) if r.get("common_exceptions") else []
                rep_ids = json.loads(r.get("representative_ticket_ids", "[]")) if r.get("representative_ticket_ids") else []
                
                results.append({
                    "workflow_id": r.get("workflow_id"),
                    "workflow_name": r.get("workflow_name"),
                    "description": r.get("description"),
                    "category": r.get("category"),
                    "common_trigger": r.get("common_trigger"),
                    "typical_resolution_steps": steps,
                    "required_inputs_and_systems": systems,
                    "common_exceptions": exceptions,
                    "suggested_automation_approach": r.get("suggested_automation_approach"),
                    "confidence_score": r.get("confidence_score"),
                    "confidence_explanation": r.get("confidence_explanation"),
                    "implementation_complexity": r.get("implementation_complexity"),
                    "complexity_score": r.get("complexity_score"),
                    "representative_ticket_ids": rep_ids,
                    "cluster_size": r.get("cluster_size"),
                    "metrics": metrics,
                    "created_at": r.get("created_at")
                })
            except Exception as e:
                print(f"[Warning] Error parsing persisted workflow {r.get('workflow_id')}: {e}")

        return results

    def save_automation_spec(self, spec: Any, tenant_id: str = "tenant_demo_sandbox"):
        """Persists drafted specification into PostgreSQL or SQLite."""
        conn = self._get_connection()
        cur = conn.cursor()
        now_iso = datetime.utcnow().isoformat()

        spec_dict = spec.model_dump(mode="json") if hasattr(spec, "model_dump") else (spec if isinstance(spec, dict) else {})
        spec_json_str = json.dumps(spec_dict)
        draft_id = spec_dict.get("draft_id")
        wf_id = spec_dict.get("workflow_id")
        run_id = spec_dict.get("run_id", "LIVE-RUN")
        appr_status = spec_dict.get("approval_status", "PENDING_REVIEW")
        reviewer = spec_dict.get("reviewer_name")
        comments = spec_dict.get("reviewer_comments")
        reviewed_at = spec_dict.get("reviewed_at")

        if self.is_postgres:
            upsert_sql = """
                INSERT INTO automation_specifications (
                    draft_id, tenant_id, workflow_id, run_id, spec_json, approval_status, reviewer_name, reviewer_comments, reviewed_at, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (draft_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    workflow_id = EXCLUDED.workflow_id,
                    run_id = EXCLUDED.run_id,
                    spec_json = EXCLUDED.spec_json,
                    approval_status = EXCLUDED.approval_status,
                    reviewer_name = EXCLUDED.reviewer_name,
                    reviewer_comments = EXCLUDED.reviewer_comments,
                    reviewed_at = EXCLUDED.reviewed_at;
            """
        else:
            upsert_sql = """
                INSERT OR REPLACE INTO automation_specifications (
                    draft_id, tenant_id, workflow_id, run_id, spec_json, approval_status, reviewer_name, reviewer_comments, reviewed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        cur.execute(upsert_sql, (draft_id, tenant_id, wf_id, run_id, spec_json_str, appr_status, reviewer, comments, reviewed_at, now_iso))
        conn.commit()
        conn.close()

    def get_automation_spec(self, draft_id: str = "any", tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves persisted specification JSON."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()

        if draft_id in ["any", "latest", "default"]:
            query = "SELECT * FROM automation_specifications WHERE 1=1"
            params = []
            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)
            query += " ORDER BY created_at DESC LIMIT 1"
        else:
            query = "SELECT * FROM automation_specifications WHERE draft_id = ?"
            params = [draft_id]
            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)

        cur.execute(self._format_query(query), params)
        row = cur.fetchone()
        conn.close()

        if not row:
            return None
        d = dict(row)
        try:
            return json.loads(d.get("spec_json", "{}"))
        except Exception:
            return None

    def save_analysis_run(self, run_id: str, run_data: Dict[str, Any], tenant_id: str = "tenant_demo_sandbox"):
        """Persists analysis run metadata and status."""
        conn = self._get_connection()
        cur = conn.cursor()
        now_iso = datetime.utcnow().isoformat()

        if self.is_postgres:
            upsert_sql = """
                INSERT INTO analysis_runs (
                    run_id, tenant_id, dataset_name, total_tickets_processed, workflows_discovered_count,
                    total_potential_annual_savings, top_recommended_workflow_id, status, message, progress,
                    model_name, clustering_method, started_at, completed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    dataset_name = EXCLUDED.dataset_name,
                    total_tickets_processed = EXCLUDED.total_tickets_processed,
                    workflows_discovered_count = EXCLUDED.workflows_discovered_count,
                    total_potential_annual_savings = EXCLUDED.total_potential_annual_savings,
                    top_recommended_workflow_id = EXCLUDED.top_recommended_workflow_id,
                    status = EXCLUDED.status,
                    message = EXCLUDED.message,
                    progress = EXCLUDED.progress,
                    completed_at = EXCLUDED.completed_at;
            """
        else:
            upsert_sql = """
                INSERT OR REPLACE INTO analysis_runs (
                    run_id, tenant_id, dataset_name, total_tickets_processed, workflows_discovered_count,
                    total_potential_annual_savings, top_recommended_workflow_id, status, message, progress,
                    model_name, clustering_method, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        cur.execute(upsert_sql, (
            run_id,
            tenant_id,
            run_data.get("dataset_name", "Live Tickets"),
            int(run_data.get("total_tickets_processed", 0)),
            int(run_data.get("workflows_discovered_count", 0)),
            float(run_data.get("total_potential_annual_savings", 0.0)),
            run_data.get("top_recommended_workflow_id"),
            run_data.get("status", "RUNNING"),
            run_data.get("message", ""),
            int(run_data.get("progress", 0)),
            run_data.get("model_name", "publishers/google/models/gemini-3.8-flash"),
            run_data.get("clustering_method", "K-Means + Vertex AI Embeddings"),
            run_data.get("started_at", now_iso),
            run_data.get("completed_at")
        ))
        conn.commit()
        conn.close()

    def get_analysis_run(self, run_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves persisted analysis run status."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor) if self.is_postgres else conn.cursor()
        query = "SELECT * FROM analysis_runs WHERE run_id = ?"
        params = [run_id]
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        cur.execute(self._format_query(query), params)
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
