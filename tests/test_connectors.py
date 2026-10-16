"""
Unit and Integration Tests for Enterprise ITSM Connectors & Cloud DLP.
AI Builder Cup 2026.
"""
import os
import sys
import pytest
from starlette.testclient import TestClient

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.app import app
from backend.models.connector import ConnectorConfig, ConnectorType, AuthType, DLPConfig, FieldMappingConfig
from backend.connectors.dlp_service import DLPService
from backend.connectors.field_mapper import FieldMapper
from backend.connectors.manager import ConnectorManager

client = TestClient(app)


def test_dlp_secret_and_credential_sanitization():
    """Validates that DLP sanitizes passwords, API tokens, and private keys."""
    dlp = DLPService()
    sample = (
        "Engineer reset user account. Temporary password: 'SecretPassword123!' and "
        "deployed service with token ghp_111122223333444455556666777788889999. "
        "Contacted via admin@enterprise.corp."
    )
    sanitized, redactions = dlp.sanitize_text(sample)

    assert "[REDACTED_PASSWORD]" in sanitized
    assert "SecretPassword123!" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "ghp_111122223333444455556666777788889999" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "admin@enterprise.corp" not in sanitized
    assert len(redactions) >= 3


def test_dlp_network_ip_sanitization():
    """Validates that internal IPv4 addresses and internal hostnames are masked."""
    dlp = DLPService()
    sample = "Database connection timed out on 192.168.1.100 while communicating with db-master.internal.corp."
    sanitized, redactions = dlp.sanitize_text(sample)

    assert "[REDACTED_IP]" in sanitized
    assert "192.168.1.100" not in sanitized
    assert "[REDACTED_HOST]" in sanitized
    assert "internal.corp" not in sanitized


def test_field_mapper_jira_payload():
    """Validates field normalization from standard Jira Cloud issue format."""
    mapper = FieldMapper()
    jira_issue = {
        "key": "ITSM-402",
        "fields": {
            "summary": "Renew SSL certificate for api-gateway",
            "description": "Wildcard certificate expires in 3 days.",
            "issuetype": {"name": "Maintenance"},
            "priority": {"name": "High"},
            "created": "2025-10-15T14:00:00.000+0000",
            "resolutiondate": "2025-10-15T14:45:00.000+0000",
            "resolution": {"name": "Completed", "description": "Generated cert via Let's Encrypt and applied to Nginx."},
            "assignee": {"displayName": "DevOps Engineer"},
            "status": {"name": "Closed"},
            "timespent": 2700  # 45 minutes
        }
    }
    canonical = mapper.map_jira_issue(jira_issue)

    assert canonical["ticket_id"] == "ITSM-402"
    assert canonical["title"] == "Renew SSL certificate for api-gateway"
    assert canonical["priority"] == "High"
    assert canonical["category"] == "Maintenance"
    assert canonical["estimated_active_handling_minutes"] == 45.0
    assert "Generated cert via Let's Encrypt" in canonical["resolution_notes"]


def test_field_mapper_servicenow_payload():
    """Validates field normalization from standard ServiceNow Incident format."""
    mapper = FieldMapper()
    snow_record = {
        "number": "INC009182",
        "short_description": "Clean up full disk on /var/log",
        "description": "Log directory is at 98% utilization.",
        "category": "Storage",
        "priority": "2",
        "sys_created_on": "2025-10-18 10:00:00",
        "resolved_at": "2025-10-18 10:30:00",
        "close_notes": "Purged rotated gz files older than 30 days.",
        "assigned_to": {"display_value": "Site Reliability Engineering"},
        "time_worked": 1800  # 30 mins
    }
    canonical = mapper.map_servicenow_record(snow_record)

    assert canonical["ticket_id"] == "INC009182"
    assert canonical["title"] == "Clean up full disk on /var/log"
    assert canonical["priority"] == "High"
    assert canonical["category"] == "Storage"
    assert canonical["estimated_active_handling_minutes"] == 30.0
    assert "Purged rotated gz files" in canonical["resolution_notes"]


def test_api_connectors_list_and_test():
    """Tests the /api/connectors endpoint and connector connectivity test."""
    res = client.get("/api/connectors")
    assert res.status_code == 200
    connectors = res.json()
    assert len(connectors) >= 2

    jira_conn = next((c for c in connectors if c.get("connector_type") == "JIRA"), connectors[0])
    jira_id = jira_conn["connector_id"]
    test_res = client.post(f"/api/connectors/{jira_id}/test")
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert test_data["status"] == "connected"


def test_api_connectors_sync():
    """Tests the /api/connectors/{id}/sync endpoint and verifies ingestion."""
    res = client.get("/api/connectors")
    assert res.status_code == 200
    snow_conn = next(c for c in res.json() if c["connector_type"] == "SERVICENOW")

    sync_res = client.post(f"/api/connectors/{snow_conn['connector_id']}/sync", json={"max_records": 10})
    assert sync_res.status_code == 200
    summary = sync_res.json()
    assert summary["status"] == "SUCCESS"
    assert summary["tickets_ingested"] == 10


def test_api_dlp_preview_endpoint():
    """Tests interactive DLP redaction preview API."""
    payload = {
        "sample_text": "Root password set to Pwd!123456 on host 10.0.0.15 by user john.doe@enterprise.corp",
        "mask_pii": True,
        "mask_secrets": True,
        "mask_network": True,
        "mask_financial": True
    }
    res = client.post("/api/connectors/dlp/preview", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "[REDACTED_PASSWORD]" in data["sanitized_text"]
    assert "[REDACTED_IP]" in data["sanitized_text"]
    assert "[REDACTED_EMAIL]" in data["sanitized_text"]
    assert data["total_redactions"] >= 3
