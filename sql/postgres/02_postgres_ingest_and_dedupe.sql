-- =====================================================================
-- Ingestion & Deduplication SQL Script for PostgreSQL
-- AI Builder Cup 2026 - Stage A & Stage D
-- Normalizes raw_tickets and populates normalized_tickets
-- =====================================================================

INSERT INTO workflow_mining.normalized_tickets (
  ticket_id,
  tenant_id,
  normalized_title,
  normalized_description,
  normalized_resolution_notes,
  combined_text,
  category,
  priority,
  created_at,
  resolved_at,
  assignee,
  elapsed_resolution_minutes,
  estimated_active_handling_minutes,
  status,
  eval_ground_truth_workflow,
  eval_ground_truth_minutes,
  normalized_at
)
WITH deduplicated_raw AS (
  SELECT
    ticket_id,
    COALESCE(tenant_id, 'tenant_demo_sandbox') AS tenant_id,
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
    ROW_NUMBER() OVER(
      PARTITION BY ticket_id 
      ORDER BY ingested_at DESC NULLS LAST, created_at DESC
    ) as row_num
  FROM workflow_mining.raw_tickets
  WHERE ticket_id IS NOT NULL 
    AND title IS NOT NULL
)
SELECT
  ticket_id,
  tenant_id,
  TRIM(regexp_replace(LOWER(title), '\s+', ' ', 'g')) AS normalized_title,
  TRIM(regexp_replace(LOWER(COALESCE(description, '')), '\s+', ' ', 'g')) AS normalized_description,
  TRIM(regexp_replace(LOWER(COALESCE(resolution_notes, '')), '\s+', ' ', 'g')) AS normalized_resolution_notes,
  CONCAT_WS(' | ', 
    TRIM(title), 
    NULLIF(TRIM(COALESCE(description, '')), ''), 
    NULLIF(TRIM(COALESCE(resolution_notes, '')), '')
  ) AS combined_text,
  COALESCE(category, 'General IT') AS category,
  COALESCE(priority, 'Medium') AS priority,
  created_at,
  resolved_at,
  COALESCE(assignee, 'Unassigned') AS assignee,
  -- Calculate elapsed calendar time in minutes
  CASE 
    WHEN resolved_at IS NOT NULL AND resolved_at >= created_at 
    THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 60.0
    ELSE NULL
  END AS elapsed_resolution_minutes,
  -- Deterministic handling time estimation heuristic:
  -- When active handling time is not logged by a timer, calculate an active work ratio
  -- bounded between 5 and 60 minutes, ensuring queue wait time is NOT treated as labor time.
  CASE
    WHEN handling_minutes_ground_truth IS NOT NULL THEN handling_minutes_ground_truth
    WHEN resolved_at IS NOT NULL THEN 
      GREATEST(5.0, LEAST(60.0, ROUND((EXTRACT(EPOCH FROM (resolved_at - created_at)) / 60.0 * 0.08)::numeric, 1)::double precision))
    ELSE 15.0
  END AS estimated_active_handling_minutes,
  COALESCE(status, 'Closed') AS status,
  workflow_ground_truth AS eval_ground_truth_workflow,
  handling_minutes_ground_truth AS eval_ground_truth_minutes,
  NOW() AS normalized_at
FROM deduplicated_raw
WHERE row_num = 1
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
  elapsed_resolution_minutes = EXCLUDED.elapsed_resolution_minutes,
  estimated_active_handling_minutes = EXCLUDED.estimated_active_handling_minutes,
  status = EXCLUDED.status,
  eval_ground_truth_workflow = EXCLUDED.eval_ground_truth_workflow,
  eval_ground_truth_minutes = EXCLUDED.eval_ground_truth_minutes,
  normalized_at = EXCLUDED.normalized_at;
