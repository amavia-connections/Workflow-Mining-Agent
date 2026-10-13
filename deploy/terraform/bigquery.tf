# Google BigQuery Multi-Tenant Dataset & Partitioned Tables

resource "google_bigquery_dataset" "workflow_mining_dataset" {
  dataset_id                  = "workflow_mining_${var.environment}"
  friendly_name               = "Workflow Mining Enterprise Data Warehouse"
  description                 = "Stores sanitized ITSM/DevOps tickets, vector cluster centroids, and deterministic financial calculations"
  location                    = var.region
  default_table_expiration_ms = var.retention_days * 86400000

  labels = {
    env        = var.environment
    managed_by = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

# Table 1: Service Tickets Table (Day-partitioned by created_at)
resource "google_bigquery_table" "service_tickets" {
  dataset_id = google_bigquery_dataset.workflow_mining_dataset.dataset_id
  table_id   = "service_tickets"

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["tenant_id", "category", "priority"]

  schema = jsonencode([
    {"name": "ticket_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "tenant_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "title", "type": "STRING", "mode": "REQUIRED"},
    {"name": "description", "type": "STRING", "mode": "NULLABLE"},
    {"name": "category", "type": "STRING", "mode": "NULLABLE"},
    {"name": "priority", "type": "STRING", "mode": "NULLABLE"},
    {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "resolved_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
    {"name": "assignee", "type": "STRING", "mode": "NULLABLE"},
    {"name": "resolution_notes", "type": "STRING", "mode": "NULLABLE"},
    {"name": "estimated_active_handling_minutes", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "cluster_id", "type": "STRING", "mode": "NULLABLE"}
  ])
}

# Table 2: Immutable Governance Audit Logs Table
resource "google_bigquery_table" "compliance_audit_logs" {
  dataset_id = google_bigquery_dataset.workflow_mining_dataset.dataset_id
  table_id   = "compliance_audit_logs"

  time_partitioning {
    type  = "DAY"
    field = "timestamp_utc"
  }

  clustering = ["tenant_id", "action_type", "role"]

  schema = jsonencode([
    {"name": "log_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "tenant_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "timestamp_utc", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "actor_identity", "type": "STRING", "mode": "REQUIRED"},
    {"name": "role", "type": "STRING", "mode": "REQUIRED"},
    {"name": "action_type", "type": "STRING", "mode": "REQUIRED"},
    {"name": "resource_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "details", "type": "STRING", "mode": "NULLABLE"},
    {"name": "audit_hash", "type": "STRING", "mode": "REQUIRED"}
  ])
}
