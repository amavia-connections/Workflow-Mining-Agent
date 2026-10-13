"""
Deterministic Quantification Service.
AI Builder Cup 2026 - Stage D.

CORE PRINCIPLE:
AI identifies and explains patterns; deterministic SQL/analytics calculates the numbers.
No metric, hour count, or dollar savings is ever fabricated by an LLM.
"""

from datetime import datetime
from typing import List, Dict, Any, Tuple
import numpy as np

from backend.models.workflow import WorkflowMetrics


class QuantificationService:
    def __init__(self, hourly_labor_rate: float = 65.0, default_automatable_pct: float = 0.75):
        self.hourly_labor_rate = hourly_labor_rate
        self.default_automatable_pct = default_automatable_pct

    def calculate_cluster_metrics(
        self,
        workflow_id: str,
        cluster_tickets: List[Dict[str, Any]],
        confidence_score: float,
        complexity_score: float
    ) -> WorkflowMetrics:
        """
        Calculates all quantitative metrics for a workflow cluster deterministically.
        """
        total_tickets = len(cluster_tickets)
        if total_tickets == 0:
            return self._empty_metrics()

        # Extract handling minutes (using estimated active handling minutes, bounded from calendar timestamps)
        handling_minutes_list = [
            float(t.get("estimated_active_handling_minutes", 15.0))
            for t in cluster_tickets
        ]
        
        avg_handling_minutes = round(float(np.mean(handling_minutes_list)), 1)
        median_handling_minutes = round(float(np.median(handling_minutes_list)), 1)
        total_handling_minutes_sum = float(np.sum(handling_minutes_list))
        
        # Calculate date span in months
        created_dates = []
        for t in cluster_tickets:
            c_str = t.get("created_at")
            if c_str:
                try:
                    c_dt = datetime.fromisoformat(c_str.replace("Z", "+00:00"))
                    if c_dt.tzinfo is not None:
                        c_dt = c_dt.replace(tzinfo=None)
                    created_dates.append(c_dt)
                except Exception:
                    pass
                    
        if created_dates:
            min_date = min(created_dates)
            max_date = max(created_dates)
            # Span in fractional months (approx 30.4 days per month)
            days_span = max(1, (max_date - min_date).days)
            span_months = max(1.0, round(days_span / 30.416, 2))
        else:
            span_months = 3.0  # Default 90 day window
            
        tickets_per_month = round(total_tickets / span_months, 1)
        
        # Handling hours per month = SUM(handling minutes) / 60 / span_months
        total_handling_hours_per_month = round((total_handling_minutes_sum / 60.0) / span_months, 2)
        
        # Annual handling hours = monthly hours * 12
        estimated_annual_handling_hours = round(total_handling_hours_per_month * 12.0, 2)
        
        # Annual labor cost = annual hours * hourly rate
        estimated_annual_labor_cost = round(estimated_annual_handling_hours * self.hourly_labor_rate, 2)
        
        # Potential savings after automation
        potential_hours_saved_per_month = round(total_handling_hours_per_month * self.default_automatable_pct, 2)
        potential_annual_hours_saved = round(estimated_annual_handling_hours * self.default_automatable_pct, 2)
        potential_annual_cost_savings = round(potential_annual_hours_saved * self.hourly_labor_rate, 2)
        
        assumptions = [
            f"Configured labor cost rate: ${self.hourly_labor_rate:.2f}/hour (fully loaded IT engineer cost)",
            f"Estimated automatable percentage: {int(self.default_automatable_pct * 100)}% based on standard runbook feasibility",
            "Active employee labor time estimated excluding inactive calendar queue wait time",
            f"Observed recurrence window: {span_months:.1f} months across analyzed dataset"
        ]
        
        return WorkflowMetrics(
            total_matching_tickets=total_tickets,
            tickets_per_month=tickets_per_month,
            avg_handling_minutes=avg_handling_minutes,
            median_handling_minutes=median_handling_minutes,
            total_handling_hours_per_month=total_handling_hours_per_month,
            estimated_annual_handling_hours=estimated_annual_handling_hours,
            hourly_labor_rate=self.hourly_labor_rate,
            estimated_annual_labor_cost=estimated_annual_labor_cost,
            automatable_percentage=self.default_automatable_pct,
            potential_hours_saved_per_month=potential_hours_saved_per_month,
            potential_annual_hours_saved=potential_annual_hours_saved,
            potential_annual_cost_savings=potential_annual_cost_savings,
            priority_rank=1,
            priority_score=50.0,
            ranking_factors={},
            calculation_assumptions=assumptions
        )

    def rank_workflows(self, workflows_with_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applies transparent, explainable multi-factor prioritization ranking across workflows.
        
        Formula:
          Score (0-100) =
            (Norm Savings * 40%) +
            (Norm Recurrence * 25%) +
            (Confidence * 20%) +
            ((1 - Complexity) * 15%)
        """
        if not workflows_with_metrics:
            return []
            
        all_savings = [w["metrics"].potential_annual_hours_saved for w in workflows_with_metrics]
        all_freq = [w["metrics"].tickets_per_month for w in workflows_with_metrics]
        
        max_savings = max(all_savings) if all_savings else 1.0
        min_savings = min(all_savings) if all_savings else 0.0
        max_freq = max(all_freq) if all_freq else 1.0
        min_freq = min(all_freq) if all_freq else 0.0
        
        scored = []
        for w in workflows_with_metrics:
            metrics: WorkflowMetrics = w["metrics"]
            conf = float(w.get("confidence_score", 0.8))
            comp = float(w.get("complexity_score", 0.4))
            
            # 1. Savings factor (0.0 to 1.0)
            norm_savings = (metrics.potential_annual_hours_saved - min_savings) / (max_savings - min_savings) if max_savings > min_savings else 1.0
            
            # 2. Recurrence factor (0.0 to 1.0)
            norm_freq = (metrics.tickets_per_month - min_freq) / (max_freq - min_freq) if max_freq > min_freq else 1.0
            
            # 3. Confidence factor (0.0 to 1.0)
            norm_conf = max(0.0, min(1.0, conf))
            
            # 4. Simplicity factor (1 - complexity score)
            simplicity = max(0.0, min(1.0, 1.0 - comp))
            
            composite_score = round(
                (norm_savings * 40.0) +
                (norm_freq * 25.0) +
                (norm_conf * 20.0) +
                (simplicity * 15.0),
                2
            )
            
            factors = {
                "savings_contribution_40pct": round(norm_savings * 40.0, 2),
                "recurrence_contribution_25pct": round(norm_freq * 25.0, 2),
                "confidence_contribution_20pct": round(norm_conf * 20.0, 2),
                "simplicity_contribution_15pct": round(simplicity * 15.0, 2),
                "composite_priority_score": composite_score
            }
            
            metrics.priority_score = composite_score
            metrics.ranking_factors = factors
            scored.append(w)
            
        # Sort descending by priority score
        scored.sort(key=lambda x: x["metrics"].priority_score, reverse=True)
        
        # Assign 1-indexed ranks
        for idx, w in enumerate(scored):
            w["metrics"].priority_rank = idx + 1
            
        return scored

    def _empty_metrics(self) -> WorkflowMetrics:
        return WorkflowMetrics(
            total_matching_tickets=0,
            tickets_per_month=0.0,
            avg_handling_minutes=0.0,
            median_handling_minutes=0.0,
            total_handling_hours_per_month=0.0,
            estimated_annual_handling_hours=0.0,
            hourly_labor_rate=self.hourly_labor_rate,
            estimated_annual_labor_cost=0.0,
            automatable_percentage=self.default_automatable_pct,
            potential_hours_saved_per_month=0.0,
            potential_annual_hours_saved=0.0,
            potential_annual_cost_savings=0.0,
            priority_rank=1,
            priority_score=0.0,
            ranking_factors={},
            calculation_assumptions=["No tickets found in cluster."]
        )
