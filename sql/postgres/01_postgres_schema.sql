-- =====================================================================
-- PostgreSQL Data Model Schema for Workflow Mining Agent
-- AI Builder Cup 2026 - Production PostgreSQL DDL
-- Compatible with PostgreSQL 13+ (tested on Cloud SQL PostgreSQL 15)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS workflow_mining;

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Raw Ingested Tickets
CREATE TABLE IF NOT EXISTS workflow_mining.raw_tickets (
  raw_id TEXT,
  ticket_id TEXT PRIMARY KEY,
  tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
  title TEXT NOT NULL,
  description TEXT,
  category TEXT,
  priority TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  resolved_at TIMESTAMPTZ,
  assignee TEXT,
  resolution_notes TEXT,
  status TEXT DEFAULT 'Closed',
  -- Isolated ground truth fields (for evaluation only)
  workflow_ground_truth TEXT,
  handling_minutes_ground_truth DOUBLE PRECISION,
  ingestion_batch_id TEXT,
  ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_tickets_created_at ON workflow_mining.raw_tickets (created_at);
CREATE INDEX IF NOT EXISTS idx_raw_tickets_tenant ON workflow_mining.raw_tickets (tenant_id);

-- 2. Cleaned and Normalized Tickets
CREATE TABLE IF NOT EXISTS workflow_mining.normalized_tickets (
  ticket_id TEXT PRIMARY KEY,
  tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
  normalized_title TEXT,
  normalized_description TEXT,
  normalized_resolution_notes TEXT,
  combined_text TEXT,
  category TEXT,
  priority TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  resolved_at TIMESTAMPTZ,
  assignee TEXT,
  elapsed_resolution_minutes DOUBLE PRECISION,
  estimated_active_handling_minutes DOUBLE PRECISION NOT NULL,
  status TEXT DEFAULT 'Closed',
  predicted_workflow_id TEXT,
  similarity_score DOUBLE PRECISION,
  -- Retained purely for Stage F evaluation join
  eval_ground_truth_workflow TEXT,
  eval_ground_truth_minutes DOUBLE PRECISION,
  normalized_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_norm_tickets_category ON workflow_mining.normalized_tickets (category);
CREATE INDEX IF NOT EXISTS idx_norm_tickets_priority ON workflow_mining.normalized_tickets (priority);
CREATE INDEX IF NOT EXISTS idx_norm_tickets_created_at ON workflow_mining.normalized_tickets (created_at);

-- 3. Discovered Workflows
CREATE TABLE IF NOT EXISTS workflow_mining.discovered_workflows (
  workflow_id TEXT PRIMARY KEY,
  run_id TEXT,
  tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
  workflow_name TEXT NOT NULL,
  description TEXT,
  category TEXT,
  common_trigger TEXT,
  typical_resolution_steps TEXT[],
  required_inputs_and_systems TEXT[],
  common_exceptions TEXT[],
  suggested_automation_approach TEXT,
  confidence_score DOUBLE PRECISION,
  confidence_explanation TEXT,
  implementation_complexity TEXT,
  complexity_score DOUBLE PRECISION,
  representative_ticket_ids TEXT[],
  cluster_size INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflows_run_id ON workflow_mining.discovered_workflows (run_id);

-- 4. Ticket to Discovered Workflow Assignments
CREATE TABLE IF NOT EXISTS workflow_mining.ticket_workflow_assignments (
  run_id TEXT NOT NULL,
  ticket_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  cluster_distance DOUBLE PRECISION,
  assignment_confidence DOUBLE PRECISION,
  is_representative_sample BOOLEAN DEFAULT FALSE,
  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (run_id, ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_workflow ON workflow_mining.ticket_workflow_assignments (workflow_id);

-- 5. Deterministic Workflow Metrics (Computed purely via SQL)
CREATE TABLE IF NOT EXISTS workflow_mining.workflow_metrics (
  metric_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  workflow_id TEXT NOT NULL,
  total_matching_tickets BIGINT,
  tickets_per_month DOUBLE PRECISION,
  avg_handling_minutes DOUBLE PRECISION,
  median_handling_minutes DOUBLE PRECISION,
  total_handling_hours_per_month DOUBLE PRECISION,
  estimated_annual_handling_hours DOUBLE PRECISION,
  hourly_labor_rate DOUBLE PRECISION,
  estimated_annual_labor_cost DOUBLE PRECISION,
  automatable_percentage DOUBLE PRECISION,
  potential_hours_saved_per_month DOUBLE PRECISION,
  potential_annual_hours_saved DOUBLE PRECISION,
  potential_annual_cost_savings DOUBLE PRECISION,
  priority_rank BIGINT,
  priority_score DOUBLE PRECISION,
  ranking_factors_json JSONB,
  calculation_assumptions_json JSONB,
  calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_run_workflow ON workflow_mining.workflow_metrics (run_id, workflow_id);

-- 6. Analysis Runs
CREATE TABLE IF NOT EXISTS workflow_mining.analysis_runs (
  run_id TEXT PRIMARY KEY,
  tenant_id TEXT DEFAULT 'tenant_demo_sandbox',
  dataset_name TEXT,
  total_tickets_processed BIGINT,
  workflows_discovered_count BIGINT,
  total_potential_annual_savings DOUBLE PRECISION,
  top_recommended_workflow_id TEXT,
  status TEXT DEFAULT 'COMPLETED',
  model_name TEXT,
  clustering_method TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- 7. Automation Specifications Drafted by Agent
CREATE TABLE IF NOT EXISTS workflow_mining.automation_specifications (
  draft_id TEXT PRIMARY KEY,
  run_id TEXT,
  workflow_id TEXT,
  workflow_name TEXT,
  business_objective TEXT,
  problem_statement TEXT,
  specification_json JSONB,
  pseudocode_markdown TEXT,
  evidence_ticket_ids TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Human Review & Approval Records
CREATE TABLE IF NOT EXISTS workflow_mining.human_reviews (
  review_id TEXT PRIMARY KEY,
  draft_id TEXT,
  workflow_id TEXT,
  approval_status TEXT DEFAULT 'PENDING_REVIEW',
  reviewer_name TEXT,
  reviewer_comments TEXT,
  is_demo_user BOOLEAN DEFAULT TRUE,
  reviewed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Evaluation Results (Stage F Ground Truth Validation)
CREATE TABLE IF NOT EXISTS workflow_mining.evaluation_results (
  eval_id TEXT PRIMARY KEY,
  run_id TEXT,
  planted_workflows_total BIGINT,
  planted_workflows_detected BIGINT,
  coverage_percentage DOUBLE PRECISION,
  precision DOUBLE PRECISION,
  recall DOUBLE PRECISION,
  f1_score DOUBLE PRECISION,
  ground_truth_total_hours DOUBLE PRECISION,
  predicted_total_hours DOUBLE PRECISION,
  percentage_error DOUBLE PRECISION,
  checklist_quality_percentage DOUBLE PRECISION,
  leakage_detected BOOLEAN DEFAULT FALSE,
  evaluated_at TIMESTAMPTZ DEFAULT NOW()
);
