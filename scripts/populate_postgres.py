"""
PostgreSQL Population Script for Workflow Mining Agent.
AI Builder Cup 2026.

Populates a PostgreSQL instance (Cloud SQL or local) with:
1. The canonical workflow_mining schema (9 tables).
2. All 3,000 synthetic tickets from data/synthetic_tickets_3000.csv.
3. Normalized and deduplicated tickets via 02_postgres_ingest_and_dedupe.sql.
"""

import os
import sys
import argparse
import logging
from urllib.parse import urlparse
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("populate_postgres")


def parse_args():
    parser = argparse.ArgumentParser(description="Populate PostgreSQL with Workflow Mining dataset")
    parser.add_argument("--host", default=os.getenv("PGHOST", "localhost"), help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=int(os.getenv("PGPORT", "5432")), help="PostgreSQL port")
    parser.add_argument("--dbname", default=os.getenv("PGDATABASE", "workflow_mining"), help="Database name")
    parser.add_argument("--user", default=os.getenv("PGUSER", "workflow_user"), help="Database user")
    parser.add_argument("--password", default=os.getenv("PGPASSWORD", ""), help="Database password")
    parser.add_argument("--sslmode", default=os.getenv("PGSSLMODE", "prefer"), help="SSL mode (disable, allow, prefer, require)")
    parser.add_argument("--csv", default=None, help="Path to synthetic_tickets_3000.csv")
    parser.add_argument("--url", default=os.getenv("DATABASE_URL", None), help="Full postgres connection URI")
    parser.add_argument("--from-terraform", action="store_true", help="Auto-read connection info from Terraform staging output")
    return parser.parse_args()


def get_connection_params(args):
    """Resolve connection parameters from CLI, URL, or Terraform."""
    if args.from_terraform:
        import subprocess
        import json
        tf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Workflow-Mining-Infra", "environments", "staging"))
        if os.path.exists(tf_dir):
            try:
                res = subprocess.run(["terraform", "output", "-json"], cwd=tf_dir, capture_output=True, text=True, check=True)
                outputs = json.loads(res.stdout)
                host = outputs.get("postgres_public_ip", {}).get("value")
                dbname = outputs.get("postgres_database_name", {}).get("value", "workflow_mining")
                user = outputs.get("postgres_user", {}).get("value", "workflow_user")
                password = outputs.get("postgres_password", {}).get("value", "")
                if host and password:
                    logger.info("Retrieved Cloud SQL connection parameters from Terraform staging output:")
                    logger.info(f"  Host: {host}")
                    logger.info(f"  Database: {dbname}")
                    logger.info(f"  User: {user}")
                    return {
                        "host": host,
                        "port": 5432,
                        "dbname": dbname,
                        "user": user,
                        "password": password,
                        "sslmode": "require"
                    }
            except Exception as e:
                logger.warning(f"Could not read from Terraform outputs: {e}")

    if args.url:
        parsed = urlparse(args.url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "dbname": parsed.path.lstrip("/") or "workflow_mining",
            "user": parsed.username or "workflow_user",
            "password": parsed.password or "",
            "sslmode": args.sslmode
        }

    return {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
        "sslmode": args.sslmode
    }


def execute_sql_file(conn, filepath):
    """Read and execute a .sql script."""
    logger.info(f"Executing SQL script: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def populate_raw_tickets(conn, csv_path):
    """Load tickets from CSV and bulk-insert into workflow_mining.raw_tickets."""
    logger.info(f"Reading synthetic dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Read {len(df)} records from CSV.")

    records = []
    for _, row in df.iterrows():
        records.append((
            row["ticket_id"],
            row["ticket_id"],
            "tenant_demo_sandbox",
            row["title"],
            row.get("description") if pd.notna(row.get("description")) else None,
            row.get("category") if pd.notna(row.get("category")) else "General IT",
            row.get("priority") if pd.notna(row.get("priority")) else "Medium",
            row["created_at"],
            row["resolved_at"] if pd.notna(row.get("resolved_at")) else None,
            row.get("assignee") if pd.notna(row.get("assignee")) else "Unassigned",
            row.get("resolution_notes") if pd.notna(row.get("resolution_notes")) else None,
            row.get("status") if pd.notna(row.get("status")) else "Closed",
            row.get("workflow_ground_truth") if pd.notna(row.get("workflow_ground_truth")) else None,
            float(row["handling_minutes_ground_truth"]) if pd.notna(row.get("handling_minutes_ground_truth")) else None,
            "synthetic_batch_3000"
        ))

    insert_query = """
    INSERT INTO workflow_mining.raw_tickets (
        raw_id,
        ticket_id,
        tenant_id,
        title,
        description,
        category,
        priority,
        created_at,
        resolved_at,
        assignee,
        resolution_notes,
        status,
        workflow_ground_truth,
        handling_minutes_ground_truth,
        ingestion_batch_id
    ) VALUES %s
    ON CONFLICT (ticket_id) DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        category = EXCLUDED.category,
        priority = EXCLUDED.priority,
        created_at = EXCLUDED.created_at,
        resolved_at = EXCLUDED.resolved_at,
        assignee = EXCLUDED.assignee,
        resolution_notes = EXCLUDED.resolution_notes,
        status = EXCLUDED.status,
        workflow_ground_truth = EXCLUDED.workflow_ground_truth,
        handling_minutes_ground_truth = EXCLUDED.handling_minutes_ground_truth;
    """

    with conn.cursor() as cur:
        execute_values(cur, insert_query, records, page_size=500)
    conn.commit()
    logger.info(f"Successfully inserted/updated {len(records)} tickets in workflow_mining.raw_tickets.")


def verify_database(conn):
    """Run validation checks on raw and normalized tables."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM workflow_mining.raw_tickets;")
        raw_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM workflow_mining.normalized_tickets;")
        norm_count = cur.fetchone()[0]

        cur.execute("""
            SELECT eval_ground_truth_workflow, COUNT(*), ROUND(AVG(estimated_active_handling_minutes)::numeric, 1)
            FROM workflow_mining.normalized_tickets
            GROUP BY eval_ground_truth_workflow
            ORDER BY COUNT(*) DESC;
        """)
        workflow_breakdown = cur.fetchall()

    logger.info("=================================================================")
    logger.info("DATABASE POPULATION VERIFICATION REPORT")
    logger.info("=================================================================")
    logger.info(f"Total Raw Tickets Ingested:        {raw_count}")
    logger.info(f"Total Normalized Tickets Processed: {norm_count}")
    logger.info("-----------------------------------------------------------------")
    logger.info("Workflow Distribution in PostgreSQL:")
    for wf, count, avg_mins in workflow_breakdown:
        logger.info(f"  {wf:<30} Count: {count:<5} Avg Mins: {avg_mins}")
    logger.info("=================================================================")


def main():
    args = parse_args()
    params = get_connection_params(args)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    schema_sql = os.path.join(base_dir, "sql", "postgres", "01_postgres_schema.sql")
    dedupe_sql = os.path.join(base_dir, "sql", "postgres", "02_postgres_ingest_and_dedupe.sql")
    csv_path = args.csv or os.path.join(base_dir, "data", "synthetic_tickets_3000.csv")

    if not os.path.exists(csv_path):
        logger.error(f"Synthetic ticket CSV not found at: {csv_path}")
        sys.exit(1)

    logger.info(f"Connecting to PostgreSQL at {params['host']}:{params['port']}, DB='{params['dbname']}'...")
    try:
        conn = psycopg2.connect(**params)
        logger.info("Connected to PostgreSQL successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    try:
        # Step 1: DDL schema creation
        execute_sql_file(conn, schema_sql)

        # Step 2: Ingest 3,000 raw tickets
        populate_raw_tickets(conn, csv_path)

        # Step 3: Run normalization & deduplication SQL
        execute_sql_file(conn, dedupe_sql)

        # Step 4: Verification
        verify_database(conn)
        logger.info("PostgreSQL database successfully initialized and populated!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
