"""
Enterprise Jira Cloud & Data Center Connector.
AI Builder Cup 2026.

Supports:
- Basic Auth with API Tokens / Personal Access Tokens (PAT)
- OAuth 2.0 3LO Bearer Tokens
- JQL query filtering
- Paginated ticket retrieval
- Atlassian Document Format (ADF) & custom field parsing
- Mock/Demo mode for offline presentations
"""
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from backend.connectors.base import BaseConnector, ConnectorAuthError, ConnectorConnectionError
from backend.models.connector import ConnectorConfig, AuthType


class JiraConnector(BaseConnector):
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.base_url = config.base_url.rstrip("/")
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._setup_auth()

    def _setup_auth(self):
        """Sets up HTTP Authorization header based on configuration."""
        if self.config.auth_type == AuthType.OAUTH2 and self.config.api_token_or_secret:
            self.headers["Authorization"] = f"Bearer {self.config.api_token_or_secret}"
        elif self.config.api_token_or_secret and ":" in self.config.api_token_or_secret:
            b64_creds = base64.b64encode(self.config.api_token_or_secret.encode()).decode()
            self.headers["Authorization"] = f"Basic {b64_creds}"
        elif self.config.username_or_email and self.config.api_token_or_secret:
            creds = f"{self.config.username_or_email}:{self.config.api_token_or_secret}"
            b64_creds = base64.b64encode(creds.encode()).decode()
            self.headers["Authorization"] = f"Basic {b64_creds}"

    def test_connection(self) -> Dict[str, Any]:
        """
        Validates connectivity to the Jira instance using the 'myself' endpoint.
        """
        # Demo / Mock check
        if "mock" in self.base_url.lower() or "demo" in self.base_url.lower():
            return {
                "status": "connected",
                "server_info": {"deploymentType": "Cloud", "buildNumber": 100200, "version": "9.12.0-mock"},
                "authenticated_user": self.config.username_or_email or "admin@enterprise.demo",
                "message": "Successfully authenticated with simulated Enterprise Jira instance."
            }

        url = f"{self.base_url}/rest/api/3/myself"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=self.headers)
                if resp.status_code == 401 or resp.status_code == 403:
                    raise ConnectorAuthError(f"Authentication failed (HTTP {resp.status_code}): Invalid Jira API token or email.")
                elif resp.status_code == 404:
                    # Fallback to Jira v2 API (Data Center / Server)
                    url_v2 = f"{self.base_url}/rest/api/2/myself"
                    resp_v2 = client.get(url_v2, headers=self.headers)
                    if resp_v2.status_code == 200:
                        data = resp_v2.json()
                        return {
                            "status": "connected",
                            "server_info": {"deploymentType": "Server/DataCenter"},
                            "authenticated_user": data.get("displayName") or data.get("name"),
                            "message": f"Connected to Jira Data Center as {data.get('displayName')}."
                        }
                    raise ConnectorConnectionError(f"Jira endpoint returned HTTP {resp.status_code}")
                elif resp.status_code != 200:
                    raise ConnectorConnectionError(f"Jira returned HTTP {resp.status_code}: {resp.text[:200]}")

                data = resp.json()
                return {
                    "status": "connected",
                    "server_info": {"deploymentType": "Cloud"},
                    "authenticated_user": data.get("displayName") or data.get("emailAddress"),
                    "message": f"Connected to Jira Cloud as {data.get('displayName')} ({data.get('emailAddress')})."
                }
        except httpx.RequestError as e:
            raise ConnectorConnectionError(f"Could not reach Jira at {self.base_url}: {str(e)}")

    def fetch_raw_tickets(self, max_records: int = 100, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Executes JQL search query to fetch closed issues.
        """
        # If simulated demo mode, return synthetic Jira structures
        if "mock" in self.base_url.lower() or "demo" in self.base_url.lower():
            return self._generate_simulated_jira_issues(max_records)

        jql = self.config.query_filter or "status in (Closed, Resolved, Done) ORDER BY updated DESC"
        if since:
            since_str = since.strftime("%Y-%m-%d %H:%M")
            jql = f"({jql}) AND updated >= '{since_str}'"

        all_issues = []
        start_at = 0
        batch_size = min(max_records, 50)

        # Jira v3 endpoint
        search_url = f"{self.base_url}/rest/api/3/search"

        try:
            with httpx.Client(timeout=25.0) as client:
                while len(all_issues) < max_records:
                    payload = {
                        "jql": jql,
                        "startAt": start_at,
                        "maxResults": batch_size,
                        "fields": [
                            "summary", "description", "issuetype", "priority",
                            "created", "resolutiondate", "resolution", "assignee",
                            "status", "timespent", "comment"
                        ]
                    }
                    resp = client.post(search_url, headers=self.headers, json=payload)
                    if resp.status_code == 404:
                        # Fallback to v2
                        search_url = f"{self.base_url}/rest/api/2/search"
                        resp = client.post(search_url, headers=self.headers, json=payload)

                    if resp.status_code != 200:
                        raise ConnectorConnectionError(f"Jira search failed with status {resp.status_code}: {resp.text[:200]}")

                    res_json = resp.json()
                    issues = res_json.get("issues", [])
                    if not issues:
                        break

                    all_issues.extend(issues)
                    start_at += len(issues)

                    if start_at >= res_json.get("total", 0):
                        break

            return all_issues[:max_records]
        except httpx.RequestError as e:
            raise ConnectorConnectionError(f"Network error querying Jira: {str(e)}")

    def normalize_raw_ticket(self, raw_ticket: Dict[str, Any]) -> Dict[str, Any]:
        return self.mapper.map_jira_issue(raw_ticket)

    def _generate_simulated_jira_issues(self, count: int) -> List[Dict[str, Any]]:
        """Generates realistic Jira-format JSON issues for demonstration/testing."""
        issues = []
        for i in range(1, count + 1):
            key = f"ITPROD-{1000 + i}"
            issues.append({
                "id": str(20000 + i),
                "key": key,
                "fields": {
                    "summary": f"Grant temporary IAM BigQuery viewer role for service account batch-data-{i}",
                    "description": f"Engineer requested access to dataset marketing_eu. Contacted lead via slack. IP 10.240.1.{i%250}",
                    "issuetype": {"name": "Service Request"},
                    "priority": {"name": "Medium"},
                    "created": "2025-11-01T10:15:30.000+0000",
                    "resolutiondate": "2025-11-01T10:35:45.000+0000",
                    "resolution": {"name": "Done", "description": "IAM role viewer assigned in project cloud-prod-10."},
                    "assignee": {"displayName": "DevOps Support Team", "emailAddress": "devops-support@enterprise.corp"},
                    "status": {"name": "Closed"},
                    "timespent": 1200,
                    "comment": {
                        "comments": [
                            {"body": f"Assigned role bigquery.dataViewer via gcloud command. Token ghp_mockedToken1234567890abcdef12345678 verified."}
                        ]
                    }
                }
            })
        return issues
