"""
Enterprise Compliance Audit Trail Service.
AI Builder Cup 2026.

Maintains an immutable, cryptographically hashed audit log of all
governance decisions, data syncs, DLP redactions, and export activities.
"""
import os
import sqlite3
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from backend.config import settings
from backend.models.connector import AuditLogEntry, UserPersona


class AuditService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(settings.DATA_DIR, "workflow_mining.db")
        self._init_table()

    def _init_table(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_audit_logs (
                log_id TEXT PRIMARY KEY,
                timestamp_utc TEXT,
                actor_identity TEXT,
                role TEXT,
                action_type TEXT,
                resource_id TEXT,
                details TEXT,
                audit_hash TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_event(
        self,
        actor_identity: str,
        role: str,
        action_type: str,
        resource_id: str,
        details: str = ""
    ) -> AuditLogEntry:
        """
        Creates an immutable audit event with a cryptographic SHA-256 integrity hash.
        """
        log_id = f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
        ts = datetime.utcnow().isoformat()
        
        # Compute SHA-256 digest over entry attributes
        raw_signature = f"{log_id}:{ts}:{actor_identity}:{role}:{action_type}:{resource_id}:{details}"
        audit_hash = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

        entry = AuditLogEntry(
            log_id=log_id,
            timestamp_utc=ts,
            actor_identity=actor_identity,
            role=UserPersona(role) if role in [p.value for p in UserPersona] else UserPersona.ANALYST,
            action_type=action_type,
            resource_id=resource_id,
            details=details,
            audit_hash=audit_hash
        )

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compliance_audit_logs 
            (log_id, timestamp_utc, actor_identity, role, action_type, resource_id, details, audit_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry.log_id, entry.timestamp_utc, entry.actor_identity, entry.role.value, entry.action_type, entry.resource_id, entry.details, entry.audit_hash))
        conn.commit()
        conn.close()

        return entry

    def get_logs(self, limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """Returns paginated audit logs ordered newest first."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM compliance_audit_logs")
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT * FROM compliance_audit_logs 
            ORDER BY timestamp_utc DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        return rows, total


# Singleton instance for platform-wide audit logging
audit_service = AuditService()
