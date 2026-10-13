"""
Enterprise Workflow Mining & Commercial SaaS Test Suite.
AI Builder Cup 2026.

Verifies:
1. Custom webhook payload ingestion & HMAC-SHA256 signature validation.
2. Field mapping parser resilience on non-standard/missing keys.
3. DevOps & SRE synthetic ticket generation (all 10 planted workflows).
4. Multi-target exporter outputs (ServiceNow, Jira, GitHub Actions, Ansible, Python, Executive Memo).
5. Role-Based Access Control (RBAC) governance enforcement on approval decisions.
"""
import os
import sys
import json
import hmac
import hashlib
import pytest
from starlette.testclient import TestClient

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.app import app
from backend.models.automation import (
    AutomationSpecification,
    AutomationStep,
    HumanApprovalGate,
    ApprovalStatus,
    ReviewRequest
)
from backend.data.synthetic_generator import generate_synthetic_dataset
from backend.connectors.field_mapper import FieldMapper
from backend.services.export_service import ExportService

client = TestClient(app)


def _create_sample_spec() -> AutomationSpecification:
    """Helper fixture to create a valid specification for exporter testing."""
    return AutomationSpecification(
        draft_id="SPEC-TEST-DEV-01",
        workflow_id="WF-01",
        workflow_name="Kubernetes CrashLoopBackOff Remediation",
        business_objective="Eliminate repetitive SRE pod triage and memory limit adjustments.",
        problem_statement="Pods repeatedly OOMKilled during burst traffic causing 15 min outages.",
        trigger_conditions=["Prometheus alert KubePodCrashLooping triggers"],
        required_input_fields=["namespace", "pod_name", "container_name"],
        systems_and_apis_involved=["Kubernetes API", "Prometheus", "Helm"],
        preconditions=["Namespace exists", "Helm chart repository reachable"],
        ordered_steps=[
            AutomationStep(
                step_number=1,
                step_name="Inspect Pod Crash Logs",
                target_system_or_api="Kubernetes API",
                action_description="Execute kubectl logs --previous to capture exit code 137.",
                is_grounded_in_evidence=True,
                evidence_source_note="Ticket INC-1029 notes: checked logs for OOMKilled"
            ),
            AutomationStep(
                step_number=2,
                step_name="Bump Memory Limit in Helm Values",
                target_system_or_api="GitOps Repo",
                action_description="Increase container memory limit from 512Mi to 1Gi via PR.",
                is_grounded_in_evidence=True,
                evidence_source_note="Ticket INC-1030 notes: updated values.yaml limit"
            )
        ],
        decision_rules=["If exit code is 137, bump memory limit by 50%"],
        exception_handling=["If node memory pressure > 90%, cordon node"],
        human_approval_gate=HumanApprovalGate(
            required=True,
            approval_role="SRE Tech Lead",
            justification="Production Helm chart changes require peer sign-off"
        ),
        security_and_permission_requirements=["ClusterRole pod-view", "Git write access"],
        retry_strategy_and_idempotency="Max 3 retries with 10s exponential backoff",
        logging_and_audit_requirements=["Log all kubectl commands to Cloud Audit Logs"],
        rollback_and_recovery_strategy="Revert Git commit and trigger ArgoCD sync",
        testing_strategy_and_acceptance_criteria=["Pod restart count remains 0 for 15 mins"],
        estimated_implementation_complexity="Medium",
        estimated_annual_hours_saved=120.5,
        dependencies_and_unresolved_assumptions=["Assume ArgoCD agent is healthy"],
        pseudocode_or_workflow_definition="# Step 1\nkubectl logs\n# Step 2\ngit commit",
        evidence_ticket_ids=["INC-1029", "INC-1030"],
        approval_status=ApprovalStatus.PENDING_REVIEW
    )


def test_custom_webhook_hmac_signature_validation():
    """Validates that valid HMAC-SHA256 signature is accepted and invalid signature is rejected."""
    secret = "whsec_live_9918237461928374abcdef"
    payload = {
        "ticket_id": "CUSTOM-WH-991",
        "title": "Database connection pool exhausted",
        "description": "PostgreSQL max_connections reached by app-workers.",
        "resolution_notes": "Restarted connection pooler pgbouncer. Cleaned idle connections.",
        "category": "Database Infrastructure",
        "priority": "Critical",
        "estimated_active_handling_minutes": 35.0
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    # 1. Test with valid signature
    res_valid = client.post(
        "/api/connectors/custom/webhook",
        content=body_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": f"sha256={valid_sig}"}
    )
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["status"] == "success"
    assert data["ingested_count"] == 1

    # 2. Test with forged/invalid signature
    res_invalid = client.post(
        "/api/connectors/custom/webhook",
        content=body_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=invalid_hash_value_12345"}
    )
    assert res_invalid.status_code == 401
    assert "Invalid HMAC" in res_invalid.json()["detail"]


def test_field_mapper_resilience_on_nonstandard_keys():
    """Validates field mapper gracefully handles missing, empty, or non-standard payloads."""
    mapper = FieldMapper()

    # Minimal payload with missing fields
    sparse_jira = {"id": "JIRA-MIN-1", "fields": {}}
    res_jira = mapper.map_jira_issue(sparse_jira)
    assert res_jira["ticket_id"] == "JIRA-MIN-1"
    assert res_jira["title"] == "Untitled Jira Issue"
    assert res_jira["category"] == "IT Support"
    assert res_jira["estimated_active_handling_minutes"] > 0

    # ServiceNow record with string duration and empty description
    sparse_snow = {
        "number": "INC9999",
        "short_description": "Disk alert",
        "time_worked": "1200"
    }
    res_snow = mapper.map_servicenow_record(sparse_snow)
    assert res_snow["ticket_id"] == "INC9999"
    assert res_snow["title"] == "Disk alert"
    assert res_snow["estimated_active_handling_minutes"] == 20.0  # 1200 / 60


def test_devops_synthetic_dataset_generation():
    """Validates generation of all 10 planted workflows (6 ITSM + 4 DevOps/SRE)."""
    tickets, manifest = generate_synthetic_dataset(num_tickets=400, seed=42, include_devops=True)

    assert len(tickets) == 400
    workflows = manifest["workflows"]
    assert len(workflows) == 10

    # Check that DevOps/SRE workflows are present
    assert "WF_CICD_FLAKY_TEST" in workflows
    assert "WF_K8S_CRASHLOOP_OOM" in workflows
    assert "WF_TERRAFORM_LOCK" in workflows
    assert "WF_DB_MIGRATION_LOCK" in workflows

    # Verify tickets have non-empty titles and handling times
    for t in tickets[:20]:
        assert len(t["title"]) > 5
        assert t["handling_minutes_ground_truth"] > 0


def test_exporter_outputs_against_schema_templates():
    """Validates that all multi-target exporters generate valid formatted payloads."""
    spec = _create_sample_spec()

    # 1. ServiceNow Flow Designer (JSON)
    snow_flow_json = ExportService.export_servicenow_flow(spec)
    snow_data = json.loads(snow_flow_json)
    assert "flow_spec_test_dev_01" in snow_data["sys_id"]
    assert len(snow_data["actions"]) == 2
    assert snow_data["table"] == "incident"

    # 2. Jira Automation Rule (JSON)
    jira_rule_json = ExportService.export_jira_automation_rule(spec)
    jira_data = json.loads(jira_rule_json)
    assert "[Mining Agent]" in jira_data["name"]
    assert jira_data["state"] == "DISABLED"
    assert len(jira_data["actions"]) == 2

    # 3. GitHub Actions Workflow (YAML)
    gha_yaml = ExportService.export_github_actions_yaml(spec)
    assert "name: \"[Remediation] Kubernetes CrashLoopBackOff Remediation\"" in gha_yaml
    assert "uses: actions/checkout@v4" in gha_yaml
    assert "Inspect Pod Crash Logs" in gha_yaml

    # 4. Ansible Playbook (YAML)
    ansible_yaml = ExportService.export_ansible_playbook_yaml(spec)
    assert "hosts: all" in ansible_yaml
    assert "Step 1 - Inspect Pod Crash Logs" in ansible_yaml

    # 5. Python Script Boilerplate
    py_code = ExportService.export_python_script(spec)
    assert "def verify_preconditions() -> bool:" in py_code
    assert "def execute_remediation() -> bool:" in py_code
    assert "kubectl logs" in py_code

    # 6. CFO/CIO Executive Business Case (HTML)
    biz_html = ExportService.export_executive_business_case(spec)
    assert "Executive Automation Business Case" in biz_html
    assert "CONFIDENTIAL &bull; EXECUTIVE MEMO" in biz_html
    assert "120.5 hrs" in biz_html


def test_rbac_governance_enforcement():
    """Validates that Analyst or Viewer cannot approve specifications, while Approver can."""
    from backend.api.app import automation_specs_cache
    spec = _create_sample_spec()
    automation_specs_cache[spec.draft_id] = spec

    # 1. Attempt approval as Analyst -> MUST FAIL with 403 Forbidden
    analyst_review = {
        "action": "APPROVED",
        "reviewer_name": "Junior Analyst",
        "reviewer_role": "ITSM / DevOps Analyst",
        "comments": "Looks good from my side."
    }
    res_analyst = client.post(f"/api/automations/{spec.draft_id}/review", json=analyst_review)
    assert res_analyst.status_code == 403
    assert "RBAC Permission Denied" in res_analyst.json()["detail"]

    # 2. Attempt approval as Governance Approver -> MUST SUCCEED
    approver_review = {
        "action": "APPROVED",
        "reviewer_name": "SRE Governance Lead",
        "reviewer_role": "Governance Approver",
        "comments": "Approved for staging deployment."
    }
    res_approver = client.post(f"/api/automations/{spec.draft_id}/review", json=approver_review)
    assert res_approver.status_code == 200
    data = res_approver.json()
    assert data["approval_status"] == "APPROVED"
    assert data["reviewer_name"] == "SRE Governance Lead"


def test_compliance_audit_log_endpoint():
    """Validates that audit events are recorded and queryable with SHA-256 signatures."""
    res = client.get("/api/audit-logs?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    first_log = data["items"][0]
    assert "audit_hash" in first_log
    assert len(first_log["audit_hash"]) == 64  # SHA-256 hex string length


def test_pdf_export_endpoint():
    """Validates that executive business case PDF is generated with valid %PDF- magic bytes."""
    from backend.api.app import automation_specs_cache
    spec = _create_sample_spec()
    automation_specs_cache[spec.draft_id] = spec

    res = client.get(f"/api/exports/automation/{spec.draft_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-")  # Valid PDF binary signature
    assert len(res.content) > 1000  # Non-empty rendered document


def test_notification_dispatch_endpoints():
    """Validates Slack Block Kit and Microsoft Teams webhook notification payload builders."""
    # 1. Slack test dispatch
    res_slack = client.post("/api/notifications/test", json={"platform": "slack"})
    assert res_slack.status_code == 200
    slack_data = res_slack.json()
    assert slack_data["status"] in ["simulated", "dispatched"]
    assert "blocks" in slack_data["payload_preview"]

    # 2. Teams test dispatch
    res_teams = client.post("/api/notifications/test", json={"platform": "teams"})
    assert res_teams.status_code == 200
    teams_data = res_teams.json()
    assert teams_data["status"] in ["simulated", "dispatched"]
    assert teams_data["payload_preview"]["@type"] == "MessageCard"


def test_task_queue_and_rate_limiter_engine():
    """Validates Option B: token-bucket rate limiter and asynchronous task queue engine."""
    # 1. Enqueue ingestion task
    task_payload = {
        "task_type": "INGESTION_SYNC",
        "connector_id": "servicenow-enterprise-01",
        "payload": {"range_days": 30},
        "priority": "HIGH"
    }
    res_enq = client.post("/api/queue/enqueue", json=task_payload)
    assert res_enq.status_code == 200
    task_data = res_enq.json()
    assert "task_id" in task_data
    assert task_data["status"] == "QUEUED"

    # 2. Check queue metrics & rate limiter status
    res_stat = client.get("/api/queue/status")
    assert res_stat.status_code == 200
    metrics = res_stat.json()
    assert "rate_limiter" in metrics
    assert metrics["rate_limiter"]["capacity"] == 50.0
    assert metrics["total_tasks_enqueued"] >= 1

    # 3. Drain batch through rate limiter
    res_drain = client.post("/api/queue/drain?batch_size=3")
    assert res_drain.status_code == 200
    drain_data = res_drain.json()
    assert drain_data["processed_count"] >= 1


def test_multi_tenant_isolation_and_saml_sso():
    """Validates Option D: multi-tenant tenant directory, tenant switching, and SAML 2.0 SSO exchange."""
    # 1. List enterprise tenants
    res_tenants = client.get("/api/tenants")
    assert res_tenants.status_code == 200
    t_data = res_tenants.json()
    assert len(t_data["tenants"]) >= 4
    tenant_ids = [t["tenant_id"] for t in t_data["tenants"]]
    assert "tenant_acme_global" in tenant_ids
    assert "tenant_apex_bank" in tenant_ids

    # 2. Switch tenant context
    res_switch = client.post("/api/tenants/switch", json={"tenant_id": "tenant_apex_bank"})
    assert res_switch.status_code == 200
    assert res_switch.json()["name"] == "Apex Financial Group"

    # 3. Initiate SAML 2.0 AuthnRequest
    res_saml_req = client.post("/api/auth/saml/login", json={"idp_name": "Microsoft Entra ID"})
    assert res_saml_req.status_code == 200
    saml_req_data = res_saml_req.json()
    assert "saml_request_xml" in saml_req_data
    assert "AuthnRequest" in saml_req_data["saml_request_xml"]

    # 4. Complete SAML assertion verification & get enterprise session
    login_payload = {
        "idp_name": "Microsoft Entra ID",
        "email": "lead.sre@apexbank.corp",
        "role": "Governance Approver",
        "tenant_id": "tenant_apex_bank"
    }
    res_callback = client.post("/api/auth/saml/callback", json=login_payload)
    assert res_callback.status_code == 200
    session_data = res_callback.json()
    assert session_data["email"] == "lead.sre@apexbank.corp"
    assert session_data["role"] == "Governance Approver"
    assert "Role-GovernanceApprover" in session_data["saml_groups"]

    # 5. Verify active enterprise session endpoint
    res_sess = client.get("/api/auth/session")
    assert res_sess.status_code == 200
    assert res_sess.json()["session"]["tenant_id"] == "tenant_apex_bank"


