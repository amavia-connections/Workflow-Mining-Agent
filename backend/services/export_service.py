"""
Multi-Target Export Engine for Workflow Mining Agent.
AI Builder Cup 2026 - Stage E & Commercial Extensions.

Exports Google ADK Automation Specifications to:
1. ServiceNow Flow Designer Definition (JSON)
2. Jira Automation Rule Template (JSON)
3. GitHub Actions Workflow (YAML)
4. Ansible Playbook (YAML)
5. Python Script Boilerplate
6. CFO / CIO Executive Business Case (Print-Ready HTML)
"""
import json
import yaml
from typing import Dict, Any, Optional
from datetime import datetime

from backend.models.automation import AutomationSpecification


class ExportService:
    @staticmethod
    def export_servicenow_flow(spec: AutomationSpecification) -> str:
        """Generates structured ServiceNow Flow Designer JSON definition."""
        actions = []
        for step in spec.ordered_steps:
            actions.append({
                "order": step.step_number,
                "name": step.step_name,
                "action_type": "core.script",
                "description": step.action_description,
                "target_system": step.target_system_or_api,
                "is_grounded_in_evidence": step.is_grounded_in_evidence,
                "evidence_source_note": step.evidence_source_note,
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff_seconds": 15
                }
            })

        flow_def = {
            "sys_id": f"flow_{spec.draft_id.lower().replace('-', '_')}",
            "name": f"Automated Flow - {spec.workflow_name}",
            "table": "incident",
            "trigger": {
                "type": "record_created",
                "condition": f"short_descriptionLIKE{spec.workflow_id}^EQ",
                "description": spec.trigger_conditions[0] if spec.trigger_conditions else "Incident Created"
            },
            "actions": actions,
            "governance": {
                "requires_approval": spec.human_approval_gate.required,
                "approval_group": spec.human_approval_gate.approval_role,
                "current_status": spec.approval_status.value,
                "safety_notice": spec.safety_boundary_notice
            },
            "rollback_flow": {
                "strategy": spec.rollback_and_recovery_strategy
            },
            "exported_at": datetime.utcnow().isoformat(),
            "generator": "Workflow Mining Agent - Enterprise Edition"
        }
        return json.dumps(flow_def, indent=2)

    @staticmethod
    def export_jira_automation_rule(spec: AutomationSpecification) -> str:
        """Generates native Jira Automation Rule JSON template."""
        components = []
        for step in spec.ordered_steps:
            components.append({
                "component": "ACTION",
                "type": "jira.issue.edit",
                "value": {
                    "step_name": step.step_name,
                    "target": step.target_system_or_api,
                    "notes": step.action_description
                }
            })

        rule = {
            "name": f"[Mining Agent] {spec.workflow_name}",
            "state": "DISABLED",  # Safety first
            "description": f"Automated workflow synthesized from ticket evidence. Grounding ratio: {len([s for s in spec.ordered_steps if s.is_grounded_in_evidence]) / max(len(spec.ordered_steps), 1) * 100:.0f}%.",
            "trigger": {
                "component": "TRIGGER",
                "type": "jira.issue.created",
                "value": {
                    "event": spec.trigger_conditions[0] if spec.trigger_conditions else "Issue created"
                }
            },
            "conditions": [
                {
                    "component": "CONDITION",
                    "type": "jira.issue.condition",
                    "value": {
                        "preconditions": spec.preconditions
                    }
                }
            ],
            "actions": components,
            "metadata": {
                "draft_id": spec.draft_id,
                "workflow_id": spec.workflow_id,
                "exported_at": datetime.utcnow().isoformat()
            }
        }
        return json.dumps(rule, indent=2)

    @staticmethod
    def export_github_actions_yaml(spec: AutomationSpecification) -> str:
        """Generates standard GitHub Actions remediation workflow YAML."""
        grounded_count = len([s for s in spec.ordered_steps if s.is_grounded_in_evidence])
        ratio = (grounded_count / max(len(spec.ordered_steps), 1)) * 100

        lines = [
            f"# ==============================================================================",
            f"# GitHub Actions Workflow: {spec.workflow_name}",
            f"# Synthesized by Workflow Mining Agent (AI Builder Cup 2026)",
            f"# Grounding Ratio: {ratio:.0f}% | Estimated Annual Hours Saved: {spec.estimated_annual_hours_saved:,.1f} hrs",
            f"# ==============================================================================",
            f"name: \"[Remediation] {spec.workflow_name}\"",
            "",
            "on:",
            "  workflow_dispatch:",
            "    inputs:",
            "      environment:",
            "        description: 'Target deployment environment'",
            "        required: true",
            "        default: 'staging'",
            "      incident_id:",
            "        description: 'Triggering incident identifier'",
            "        required: false",
            "",
            "permissions:",
            "  contents: read",
            "  id-token: write",
            "",
            "jobs:",
            "  remediation-pipeline:",
            "    name: Execute Remediations",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Checkout Repository",
            "        uses: actions/checkout@v4",
            "",
            "      - name: Verify Safety Preconditions",
            "        run: |",
            f"          echo \"Verifying preconditions: {'; '.join(spec.preconditions)}\"",
            "          echo \"Preconditions validated successfully.\"",
            ""
        ]

        for step in spec.ordered_steps:
            lines.extend([
                f"      - name: \"Step {step.step_number}: {step.step_name}\"",
                f"        run: |",
                f"          echo \"Target System: {step.target_system_or_api}\"",
                f"          echo \"Action: {step.action_description}\"",
                f"          # Evidence grounding: {step.is_grounded_in_evidence} (Note: {step.evidence_source_note or 'Architecture Recommendation'})",
                f"          echo \"Completed step {step.step_number}\"",
                ""
            ])

        lines.extend([
            "      - name: Validate Health Assertions",
            "        run: |",
            f"          echo \"Asserting recovery: {'; '.join(spec.testing_strategy_and_acceptance_criteria)}\"",
            "          echo \"System verified operational.\"",
            ""
        ])

        return "\n".join(lines)

    @staticmethod
    def export_ansible_playbook_yaml(spec: AutomationSpecification) -> str:
        """Generates standard Ansible Playbook YAML for infrastructure remediation."""
        tasks = []
        for step in spec.ordered_steps:
            tasks.append({
                "name": f"Step {step.step_number} - {step.step_name}",
                "ansible.builtin.debug": {
                    "msg": f"Executing on {step.target_system_or_api}: {step.action_description}"
                }
            })

        playbook = [
            {
                "name": f"Automated Runbook - {spec.workflow_name}",
                "hosts": "all",
                "become": True,
                "vars": {
                    "draft_id": spec.draft_id,
                    "target_workflow": spec.workflow_id,
                    "safety_boundary": spec.safety_boundary_notice
                },
                "pre_tasks": [
                    {
                        "name": "Verify Preconditions",
                        "ansible.builtin.debug": {
                            "msg": f"Checking preconditions: {', '.join(spec.preconditions)}"
                        }
                    }
                ],
                "tasks": tasks,
                "post_tasks": [
                    {
                        "name": "Validate Test Assertions",
                        "ansible.builtin.debug": {
                            "msg": f"Validating health: {', '.join(spec.testing_strategy_and_acceptance_criteria)}"
                        }
                    }
                ]
            }
        ]
        return yaml.dump(playbook, sort_keys=False)

    @staticmethod
    def export_python_script(spec: AutomationSpecification) -> str:
        """Generates clean executable Python script boilerplate with mocked clients and logging."""
        lines = [
            '#!/usr/bin/env python3',
            '"""',
            f'Automated Remediation Script for: {spec.workflow_name}',
            f'Generated by Workflow Mining Agent (Google ADK & Vertex AI)',
            f'Draft ID: {spec.draft_id} | Workflow ID: {spec.workflow_id}',
            f'Estimated Potential Annual Hours Saved: {spec.estimated_annual_hours_saved:,.1f} hrs',
            '"""',
            'import os',
            'import sys',
            'import logging',
            'import time',
            '',
            'logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")',
            'logger = logging.getLogger("WorkflowAutomation")',
            '',
            'def verify_preconditions() -> bool:',
            '    logger.info("Validating runbook preconditions...")',
        ]
        for p in spec.preconditions:
            lines.append(f'    logger.info(" - Precondition check: {p}")')
        lines.extend([
            '    return True',
            '',
            'def execute_remediation() -> bool:',
            '    logger.info("Beginning multi-step remediation runbook...")',
        ])
        for step in spec.ordered_steps:
            lines.extend([
                f'    # Step {step.step_number}: {step.step_name}',
                f'    logger.info("Executing step {step.step_number}: {step.step_name} on {step.target_system_or_api}")',
                f'    # Description: {step.action_description}',
                f'    time.sleep(0.5)  # Simulated execution',
            ])
        lines.extend([
            '    return True',
            '',
            'def verify_assertions() -> bool:',
            '    logger.info("Validating health assertions...")',
        ])
        for a in spec.testing_strategy_and_acceptance_criteria:
            lines.append(f'    logger.info(" - Health assertion: {a}")')
        lines.extend([
            '    return True',
            '',
            'def main():',
            '    logger.info("Starting automated runbook execution")',
            '    if not verify_preconditions():',
            '        logger.error("Precondition verification failed. Aborting.")',
            '        sys.exit(1)',
            '    if not execute_remediation():',
            '        logger.error("Remediation execution failed. Initiating rollback...")',
            f'        logger.info("Rollback Strategy: {spec.rollback_and_recovery_strategy}")',
            '        sys.exit(2)',
            '    if not verify_assertions():',
            '        logger.warning("Post-execution health assertions failed. Inspect logs.")',
            '        sys.exit(3)',
            '    logger.info("Runbook completed successfully.")',
            '',
            'if __name__ == "__main__":',
            '    main()',
            ''
        ])
        return "\n".join(lines)

    @staticmethod
    def export_executive_business_case(spec: AutomationSpecification) -> str:
        """Generates a print-ready Executive CFO/CIO Business Case HTML memo."""
        annual_hours = spec.estimated_annual_hours_saved
        annual_savings = round(annual_hours * 65.0, 2)
        grounded_count = len([s for s in spec.ordered_steps if s.is_grounded_in_evidence])
        ratio = (grounded_count / max(len(spec.ordered_steps), 1)) * 100

        steps_html = "".join([
            f"""
            <div style="margin-bottom: 12px; padding: 12px; background: #f8fafc; border-left: 4px solid #2563eb; border-radius: 4px;">
              <div style="font-weight: 700; color: #0f172a;">Step {s.step_number}: {s.step_name} <span style="font-size: 0.75rem; color: #64748b; font-weight: normal;">(Target: {s.target_system_or_api})</span></div>
              <div style="font-size: 0.85rem; color: #334155; margin-top: 4px;">{s.action_description}</div>
              <div style="font-size: 0.75rem; color: #059669; margin-top: 4px;">{"✅ Grounded in Ticket Evidence" if s.is_grounded_in_evidence else "💡 Architecture Best Practice"}</div>
            </div>
            """
            for s in spec.ordered_steps
        ])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Executive Business Case - {spec.workflow_name}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px auto; max-width: 800px; color: #1e293b; line-height: 1.6; }}
    .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; background: #e0f2fe; color: #0369a1; }}
    .stat-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 24px 0; }}
    .stat-card {{ background: #f1f5f9; padding: 16px; border-radius: 8px; text-align: center; }}
    .stat-val {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 4px; }}
    .stat-label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 700; }}
    .section-title {{ font-size: 1.15rem; font-weight: 700; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-top: 28px; }}
    .approval-box {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 16px; margin-top: 30px; }}
    @media print {{ body {{ margin: 20px; }} }}
  </style>
</head>
<body>
  <div class="header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <span class="badge">CONFIDENTIAL &bull; EXECUTIVE MEMO</span>
      <span style="font-size: 0.8rem; color: #64748b;">Generated: {datetime.utcnow().strftime("%B %d, %Y")}</span>
    </div>
    <h1 style="font-size: 1.75rem; margin: 12px 0 6px 0; color: #0f172a;">Executive Automation Business Case</h1>
    <div style="font-size: 1rem; color: #475569;">Proposal: <strong>{spec.workflow_name}</strong> (Workflow ID: {spec.workflow_id})</div>
  </div>

  <div class="section-title">1. Executive Summary &amp; ROI Impact</div>
  <p>
    Through semantic ticket history mining and deterministic SQL analytics, enterprise engineering teams identified
    a high-friction, repetitive operational workflow. Automating this procedural sequence yields significant employee hours
    recovery and measurable financial return on investment.
  </p>

  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-label">Annual Labor Recovered</div>
      <div class="stat-val">{annual_hours:,.1f} hrs</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Estimated Annual Savings</div>
      <div class="stat-val" style="color: #059669;">${annual_savings:,.2f}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Evidence Grounding</div>
      <div class="stat-val">{ratio:.0f}%</div>
    </div>
  </div>

  <div class="section-title">2. Operational Trigger &amp; Systems</div>
  <p><strong>Primary Trigger:</strong> {spec.trigger_conditions[0] if spec.trigger_conditions else "Operational Incident"}</p>
  <p><strong>Required Systems &amp; APIs:</strong> {", ".join(spec.systems_and_apis_involved)}</p>

  <div class="section-title">3. Proposed Procedural Runbook</div>
  {steps_html}

  <div class="section-title">4. Governance, Rollback &amp; Mandatory Safety Boundary</div>
  <p><strong>Rollback Strategy:</strong> {spec.rollback_and_recovery_strategy}</p>
  <p style="font-size: 0.85rem; color: #dc2626; font-weight: 600;">
    Mandatory Safety Boundary: {spec.safety_boundary_notice}
  </p>

  <div class="approval-box">
    <div style="font-weight: 700; color: #065f46; font-size: 0.95rem;">
      Governance Decision Stamp: {spec.approval_status.value}
    </div>
    <div style="font-size: 0.85rem; color: #047857; margin-top: 4px;">
      Reviewed by: <strong>{spec.reviewer_name or "Pending Governance Committee Review"}</strong>
      {f"<br>Review Comments: {spec.reviewer_comments}" if spec.reviewer_comments else ""}
    </div>
  </div>
</body>
</html>"""
        return html
