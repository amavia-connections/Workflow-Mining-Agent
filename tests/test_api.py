"""
API Contract and Integration Tests for FastAPI Application.
AI Builder Cup 2026.
"""

import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.app import app
from backend.models.automation import ApprovalStatus

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_mode" in data


def test_dashboard_summary_endpoint():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_tickets_analyzed" in data
    assert "workflows_discovered_count" in data
    assert "total_monthly_handling_hours" in data
    assert "top_opportunities" in data
    assert len(data["top_opportunities"]) > 0


def test_get_tickets_endpoint():
    response = client.get("/api/tickets?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 10


def test_get_workflows_endpoint():
    response = client.get("/api/workflows")
    assert response.status_code == 200
    workflows = response.json()
    assert isinstance(workflows, list)
    assert len(workflows) > 0
    # Top workflow has rank 1
    assert workflows[0]["metrics"]["priority_rank"] == 1


def test_automation_draft_and_review_workflow():
    # 1. Fetch workflows to get ID
    wf_res = client.get("/api/workflows")
    assert wf_res.status_code == 200
    workflows = wf_res.json()
    top_wf_id = workflows[0]["workflow_id"]
    
    # 2. Draft specification
    draft_res = client.post(f"/api/automations/draft?workflow_id={top_wf_id}")
    assert draft_res.status_code == 200
    spec = draft_res.json()
    draft_id = spec["draft_id"]
    assert spec["approval_status"] == ApprovalStatus.PENDING_REVIEW.value
    assert "SAFETY BOUNDARY" in spec["safety_boundary_notice"]
    
    # 3. Review specification (Approve)
    review_res = client.post(f"/api/automations/{draft_id}/review", json={
        "action": ApprovalStatus.APPROVED.value,
        "reviewer_name": "Senior Cloud SRE",
        "comments": "Reviewed runbook and verified rollback strategy."
    })
    assert review_res.status_code == 200
    reviewed_spec = review_res.json()
    assert reviewed_spec["approval_status"] == ApprovalStatus.APPROVED.value
    assert reviewed_spec["reviewer_name"] == "Senior Cloud SRE"
    
    # 4. Export Markdown
    export_res = client.get(f"/api/exports/automation/{draft_id}?format=markdown")
    assert export_res.status_code == 200
    assert "Automation Specification:" in export_res.text
    assert "MANDATORY SAFETY BOUNDARY" in export_res.text


def test_evaluation_endpoint():
    summary = client.get("/api/dashboard/summary").json()
    run_id = summary["active_run_id"]
    eval_res = client.get(f"/api/evaluation/{run_id}")
    assert eval_res.status_code == 200
    report = eval_res.json()
    assert "detection_metrics" in report
    assert "time_metrics" in report
    assert report["detection_metrics"]["coverage_percentage"] > 0
    assert report["leakage_verification"]["leakage_detected"] is False


def test_explain_workflow_step_endpoint():
    payload = {
        "workflow_name": "Canary Traffic Shifting",
        "step_number": 1,
        "step_name": "Drain ingress traffic to test stage",
        "target_system": "Kubernetes Ingress / Envoy",
        "action_description": "Gradually shift traffic away from failing pods",
        "evidence_source_note": "Extracted from deployment runbook"
    }
    res = client.post("/api/workflows/explain-step", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["step_number"] == 1
    assert data["step_name"] == "Drain ingress traffic to test stage"
    assert "why_needed" in data and len(data["why_needed"]) > 20
    assert "how_to_improve" in data and len(data["how_to_improve"]) > 20
    assert "safeguards" in data and len(data["safeguards"]) > 10
    assert "time_savings" in data
    assert isinstance(data["automation_tooling"], list)
    assert len(data["automation_tooling"]) > 0

