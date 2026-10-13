"""
Enterprise Notification & ChatOps Service (Slack & Microsoft Teams).
Dispatches rich Block Kit and Adaptive Card webhooks for discovered workflows and approval gates.
AI Builder Cup 2026.
"""
from typing import Dict, Any, Optional
import json
import urllib.request
import urllib.error
from datetime import datetime

from backend.models.automation import AutomationSpecification
from backend.services.audit_service import audit_service


class NotificationService:
    @staticmethod
    def build_slack_opportunity_payload(workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Builds a rich Slack Block Kit payload for newly discovered automation opportunities."""
        wf_name = workflow.get("workflow_name", "Discovered Workflow")
        annual_savings = workflow.get("potential_annual_cost_savings", 0)
        annual_hours = workflow.get("potential_annual_hours_saved", 0)
        complexity = workflow.get("implementation_complexity", "Medium")
        wf_id = workflow.get("workflow_id", "WF-XX")

        return {
            "text": f"🚀 New Automation Opportunity Discovered: {wf_name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚀 High-Impact Workflow Discovered: {wf_name}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Workflow ID:*\n`{wf_id}`"},
                        {"type": "mrkdwn", "text": f"*Est. Annual Savings:*\n*${annual_savings:,.0f}* / yr"},
                        {"type": "mrkdwn", "text": f"*Annual Hours Wasted:*\n*{annual_hours:,.1f}* hrs"},
                        {"type": "mrkdwn", "text": f"*Complexity:*\n`{complexity}`"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{workflow.get('description', 'Repetitive workflow identified via unsupervised ticket clustering.')}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🤖 *Workflow Mining Agent* • Deterministic SQL Calculation • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def build_slack_approval_request_payload(spec: AutomationSpecification) -> Dict[str, Any]:
        """Builds a Slack Block Kit payload requesting human governance sign-off."""
        return {
            "text": f"🛡️ Human Approval Required for Runbook: {spec.workflow_name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🛡️ Governance Review Required: {spec.workflow_name}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Specification ID:*\n`{spec.draft_id}`"},
                        {"type": "mrkdwn", "text": f"*Required Reviewer:*\n*{spec.human_approval_gate.approval_role}*"},
                        {"type": "mrkdwn", "text": f"*Annual Labor Savings:*\n*{spec.estimated_annual_hours_saved:,.1f} hrs*"},
                        {"type": "mrkdwn", "text": f"*Status:*\n`{spec.approval_status}`"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Business Objective:*\n{spec.business_objective}\n\n*Safety Boundary:* Approval is a recorded review decision. The system never executes automations automatically."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Inspect in Automation Studio", "emoji": True},
                            "style": "primary",
                            "url": "http://localhost:8000"
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def build_teams_opportunity_payload(workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Builds a Microsoft Teams MessageCard payload."""
        wf_name = workflow.get("workflow_name", "Discovered Workflow")
        annual_savings = workflow.get("potential_annual_cost_savings", 0)
        annual_hours = workflow.get("potential_annual_hours_saved", 0)

        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"New Automation Opportunity: {wf_name}",
            "themeColor": "2563EB",
            "title": f"🚀 Workflow Discovered: {wf_name}",
            "sections": [
                {
                    "activityTitle": "Workflow Mining Agent (Google ADK & Vertex AI)",
                    "activitySubtitle": f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                    "facts": [
                        {"name": "Workflow ID", "value": workflow.get("workflow_id", "WF-XX")},
                        {"name": "Est. Annual Savings", "value": f"${annual_savings:,.0f} / yr"},
                        {"name": "Annual Hours Saved", "value": f"{annual_hours:,.1f} hrs"},
                        {"name": "Complexity", "value": workflow.get("implementation_complexity", "Medium")}
                    ],
                    "text": workflow.get("description", "Identified repetitive operational pattern.")
                }
            ]
        }

    @classmethod
    def dispatch_webhook(
        cls,
        webhook_url: str,
        platform: str,
        payload: Dict[str, Any],
        event_name: str = "NOTIFICATION"
    ) -> Dict[str, Any]:
        """
        Dispatches payload to Slack or Teams webhook.
        Handles real network calls or simulated local dispatch gracefully.
        """
        is_dummy = any(k in (webhook_url or "") for k in ["DEMO", "TEST", "LOCAL", "example.com", "localhost"])
        is_live = bool(webhook_url and webhook_url.startswith("https://") and not is_dummy)
        status = "simulated"
        http_code = 200

        if is_live:
            try:
                data_bytes = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    webhook_url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    http_code = response.getcode()
                    status = "dispatched"
            except Exception as e:
                status = f"failed: {str(e)}"
                http_code = 502

        audit_service.record_event(
            actor_identity="NotificationService",
            role="System",
            action_type="NOTIFICATION_DISPATCHED",
            resource_id=platform,
            details=f"Event: {event_name} | Platform: {platform} | Status: {status} | HTTP: {http_code}"
        )

        return {
            "status": status,
            "platform": platform,
            "http_code": http_code,
            "is_live_network_call": is_live,
            "payload_preview": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
