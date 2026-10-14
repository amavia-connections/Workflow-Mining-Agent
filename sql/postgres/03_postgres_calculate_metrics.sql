-- =====================================================================
-- Deterministic Workflow Metrics Calculation in PostgreSQL
-- AI Builder Cup 2026 - Stage D
--
-- CORE PRINCIPLE:
-- AI identifies and explains patterns; deterministic SQL calculates the numbers.
-- No metric or dollar amount is ever invented by Gemini.
-- =====================================================================

-- Parameters:
-- :run_id: TEXT
-- :hourly_labor_rate: DOUBLE PRECISION (default: 65.00)
-- :default_automatable_pct: DOUBLE PRECISION (default: 0.75)

WITH workflow_tickets AS (
  SELECT
    a.run_id,
    a.workflow_id,
    t.ticket_id,
    t.created_at,
    t.estimated_active_handling_minutes,
    EXTRACT(YEAR FROM t.created_at) as t_year,
    EXTRACT(MONTH FROM t.created_at) as t_month
  FROM workflow_mining.ticket_workflow_assignments a
  JOIN workflow_mining.normalized_tickets t
    ON a.ticket_id = t.ticket_id
  WHERE a.run_id = :run_id
),

-- 1. Date Span & Monthly Frequency
workflow_date_span AS (
  SELECT
    workflow_id,
    COUNT(DISTINCT CONCAT(t_year::text, '-', t_month::text)) AS active_months_count,
    GREATEST(
      1.0, 
      (DATE_PART('year', AGE(MAX(created_at), MIN(created_at))) * 12 + DATE_PART('month', AGE(MAX(created_at), MIN(created_at)))) + 1.0
    ) AS span_months
  FROM workflow_tickets
  GROUP BY workflow_id
),

-- 2. Aggregations & Handling Statistics
workflow_stats AS (
  SELECT
    wt.workflow_id,
    COUNT(wt.ticket_id) AS total_matching_tickets,
    ROUND(AVG(wt.estimated_active_handling_minutes)::numeric, 1)::double precision AS avg_handling_minutes,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wt.estimated_active_handling_minutes)::numeric, 1)::double precision AS median_handling_minutes,
    SUM(wt.estimated_active_handling_minutes) AS total_handling_minutes_sum
  FROM workflow_tickets wt
  GROUP BY wt.workflow_id
)

INSERT INTO workflow_mining.workflow_metrics (
  metric_id,
  run_id,
  workflow_id,
  total_matching_tickets,
  tickets_per_month,
  avg_handling_minutes,
  median_handling_minutes,
  total_handling_hours_per_month,
  estimated_annual_handling_hours,
  hourly_labor_rate,
  estimated_annual_labor_cost,
  automatable_percentage,
  potential_hours_saved_per_month,
  potential_annual_hours_saved,
  potential_annual_cost_savings,
  calculated_at
)
SELECT
  gen_random_uuid()::text AS metric_id,
  :run_id AS run_id,
  ws.workflow_id,
  ws.total_matching_tickets,
  ROUND((ws.total_matching_tickets / d.span_months)::numeric, 1)::double precision AS tickets_per_month,
  ws.avg_handling_minutes,
  ws.median_handling_minutes,
  ROUND(((ws.total_handling_minutes_sum / 60.0) / d.span_months)::numeric, 2)::double precision AS total_handling_hours_per_month,
  ROUND((((ws.total_handling_minutes_sum / 60.0) / d.span_months) * 12.0)::numeric, 2)::double precision AS estimated_annual_handling_hours,
  :hourly_labor_rate AS hourly_labor_rate,
  ROUND(((((ws.total_handling_minutes_sum / 60.0) / d.span_months) * 12.0) * :hourly_labor_rate)::numeric, 2)::double precision AS estimated_annual_labor_cost,
  :default_automatable_pct AS automatable_percentage,
  ROUND((((ws.total_handling_minutes_sum / 60.0) / d.span_months) * :default_automatable_pct)::numeric, 2)::double precision AS potential_hours_saved_per_month,
  ROUND(((((ws.total_handling_minutes_sum / 60.0) / d.span_months) * 12.0) * :default_automatable_pct)::numeric, 2)::double precision AS potential_annual_hours_saved,
  ROUND((((((ws.total_handling_minutes_sum / 60.0) / d.span_months) * 12.0) * :default_automatable_pct) * :hourly_labor_rate)::numeric, 2)::double precision AS potential_annual_cost_savings,
  NOW() AS calculated_at
FROM workflow_stats ws
JOIN workflow_date_span d ON ws.workflow_id = d.workflow_id;
