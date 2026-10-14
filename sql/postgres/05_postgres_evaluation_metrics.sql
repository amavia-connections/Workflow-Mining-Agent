-- =====================================================================
-- Evaluation Framework SQL Script for PostgreSQL
-- AI Builder Cup 2026 - Stage F
--
-- Compares discovered clusters and assignments against hidden ground truth.
-- Ground truth labels are strictly isolated and evaluated here only.
-- =====================================================================

WITH cluster_ground_truth_matrix AS (
  SELECT
    a.workflow_id AS discovered_cluster_id,
    w.workflow_name,
    t.eval_ground_truth_workflow,
    COUNT(t.ticket_id) AS ticket_overlap_count,
    SUM(t.estimated_active_handling_minutes) / 60.0 AS predicted_handling_hours,
    SUM(t.eval_ground_truth_minutes) / 60.0 AS ground_truth_handling_hours
  FROM workflow_mining.ticket_workflow_assignments a
  JOIN workflow_mining.normalized_tickets t
    ON a.ticket_id = t.ticket_id
  JOIN workflow_mining.discovered_workflows w
    ON a.workflow_id = w.workflow_id
  WHERE a.run_id = :run_id
    AND t.eval_ground_truth_workflow != 'ONE_OFF'
  GROUP BY a.workflow_id, w.workflow_name, t.eval_ground_truth_workflow
),

-- Determine best-match alignment between discovered cluster and planted workflow
best_cluster_matches AS (
  SELECT
    discovered_cluster_id,
    workflow_name,
    eval_ground_truth_workflow,
    ticket_overlap_count,
    predicted_handling_hours,
    ground_truth_handling_hours,
    ROW_NUMBER() OVER(
      PARTITION BY eval_ground_truth_workflow 
      ORDER BY ticket_overlap_count DESC
    ) as best_match_rank
  FROM cluster_ground_truth_matrix
),

planted_totals AS (
  SELECT
    eval_ground_truth_workflow,
    COUNT(ticket_id) AS total_planted_tickets,
    SUM(eval_ground_truth_minutes) / 60.0 AS total_planted_hours
  FROM workflow_mining.normalized_tickets
  WHERE eval_ground_truth_workflow != 'ONE_OFF'
  GROUP BY eval_ground_truth_workflow
),

discovered_totals AS (
  SELECT
    a.workflow_id,
    COUNT(a.ticket_id) AS total_assigned_tickets
  FROM workflow_mining.ticket_workflow_assignments a
  WHERE a.run_id = :run_id
  GROUP BY a.workflow_id
),

-- Compute Precision, Recall, and F1 per workflow
workflow_metrics_eval AS (
  SELECT
    b.eval_ground_truth_workflow,
    b.discovered_cluster_id,
    b.workflow_name,
    b.ticket_overlap_count AS true_positives,
    (d.total_assigned_tickets - b.ticket_overlap_count) AS false_positives,
    (p.total_planted_tickets - b.ticket_overlap_count) AS false_negatives,
    b.predicted_handling_hours,
    p.total_planted_hours,
    ABS(b.predicted_handling_hours - p.total_planted_hours) AS absolute_hours_error,
    CASE WHEN d.total_assigned_tickets = 0 THEN 0.0 ELSE b.ticket_overlap_count::double precision / d.total_assigned_tickets END AS precision_score,
    CASE WHEN p.total_planted_tickets = 0 THEN 0.0 ELSE b.ticket_overlap_count::double precision / p.total_planted_tickets END AS recall_score
  FROM best_cluster_matches b
  JOIN planted_totals p ON b.eval_ground_truth_workflow = p.eval_ground_truth_workflow
  JOIN discovered_totals d ON b.discovered_cluster_id = d.workflow_id
  WHERE b.best_match_rank = 1
)

SELECT
  COUNT(DISTINCT eval_ground_truth_workflow) AS detected_planted_workflows,
  6 AS total_planted_workflows,
  ROUND((CASE WHEN 6 = 0 THEN 0.0 ELSE (COUNT(DISTINCT eval_ground_truth_workflow)::double precision / 6.0) * 100.0 END)::numeric, 1)::double precision AS coverage_percentage,
  ROUND(AVG(precision_score)::numeric, 4)::double precision AS macro_precision,
  ROUND(AVG(recall_score)::numeric, 4)::double precision AS macro_recall,
  ROUND(
    (CASE 
      WHEN (AVG(precision_score) + AVG(recall_score)) = 0 THEN 0.0 
      ELSE 2.0 * (AVG(precision_score) * AVG(recall_score)) / (AVG(precision_score) + AVG(recall_score)) 
    END)::numeric, 
    4
  )::double precision AS macro_f1_score,
  ROUND(SUM(total_planted_hours)::numeric, 2)::double precision AS total_ground_truth_hours,
  ROUND(SUM(predicted_handling_hours)::numeric, 2)::double precision AS total_predicted_hours,
  ROUND(
    (CASE 
      WHEN SUM(total_planted_hours) = 0 THEN 0.0 
      ELSE ABS(SUM(predicted_handling_hours) - SUM(total_planted_hours)) / SUM(total_planted_hours) * 100.0 
    END)::numeric, 
    2
  )::double precision AS total_percentage_error
FROM workflow_metrics_eval;
