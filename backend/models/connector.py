"""
Data models for Enterprise Ingestion Connectors, RBAC, Audit Logs & Multi-Target Exporters.
AI Builder Cup 2026.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ConnectorCategory(str, Enum):
    ITSM = "Enterprise ITSM"
    DEVOPS = "DevOps & SRE Platforms"
    CUSTOM = "Custom / In-House Engines"


class ConnectorType(str, Enum):
    # Category A: Enterprise ITSM
    SERVICENOW = "SERVICENOW"
    JIRA = "JIRA"
    ZENDESK = "ZENDESK"
    FRESHSERVICE = "FRESHSERVICE"
    BMC_HELIX = "BMC_HELIX"

    # Category B: DevOps & Incident Response
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    LINEAR = "LINEAR"
    PAGERDUTY = "PAGERDUTY"
    OPSGENIE = "OPSGENIE"

    # Category C: Custom / In-House Engines
    CUSTOM_WEBHOOK = "CUSTOM_WEBHOOK"
    CUSTOM_REST = "CUSTOM_REST"
    DIRECT_DB = "DIRECT_DB"

    # Fallbacks
    CSV = "CSV"
    GENERIC_REST = "GENERIC_REST"


class AuthType(str, Enum):
    API_TOKEN = "API_TOKEN"
    BASIC = "BASIC"
    OAUTH2 = "OAUTH2"
    HMAC_SECRET = "HMAC_SECRET"
    DATABASE_CONNECTION_STRING = "DATABASE_CONNECTION_STRING"


class SyncStatus(str, Enum):
    IDLE = "IDLE"
    CONNECTED = "CONNECTED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SIMULATED_DEMO = "SIMULATED_DEMO"


class UserPersona(str, Enum):
    ADMIN = "Admin"
    ANALYST = "ITSM / DevOps Analyst"
    APPROVER = "Governance Approver"
    VIEWER = "Executive / Viewer"


class ExportTarget(str, Enum):
    SERVICENOW = "servicenow"
    JIRA = "jira"
    GITHUB_ACTIONS = "github_actions"
    ANSIBLE = "ansible"
    PYTHON_SCRIPT = "python_script"
    EXECUTIVE_SUMMARY = "executive_summary"


class FieldMappingConfig(BaseModel):
    """
    Dynamic field mapping configuration to adapt any ITSM / DevOps custom fields
    to the canonical ticket schema.
    """
    ticket_id_field: str = Field(default="id", description="Source field for remote ID / key")
    title_field: str = Field(default="summary", description="Source field for ticket title / summary")
    description_field: str = Field(default="description", description="Source field for ticket description")
    resolution_notes_field: str = Field(default="resolution_notes", description="Source field for resolution / close notes")
    category_field: str = Field(default="category", description="Source field for ticket category / subsystem")
    priority_field: str = Field(default="priority", description="Source field for ticket priority / severity")
    assignee_field: str = Field(default="assignee", description="Source field for assignee")
    created_at_field: str = Field(default="created", description="Source field for created timestamp")
    resolved_at_field: str = Field(default="resolutiondate", description="Source field for resolution timestamp")
    handling_time_field: Optional[str] = Field(default=None, description="Field for spent minutes/seconds")
    status_field: str = Field(default="status", description="Source field for ticket status")
    jsonpath_selector: Optional[str] = Field(default=None, description="Optional JSONPath selector for REST/GraphQL (e.g. $.data.issues[*])")
    custom_field_rules: Dict[str, str] = Field(default_factory=dict, description="Arbitrary custom field lookups")


class DLPConfig(BaseModel):
    """
    Google Cloud DLP & Privacy Sanitization rules.
    Applied before raw ticket text touches embeddings or LLMs.
    """
    enabled: bool = Field(default=True, description="Enable automatic DLP sanitization")
    mask_pii: bool = Field(default=True, description="Mask employee names, emails, phone numbers")
    mask_secrets: bool = Field(default=True, description="Mask passwords, API keys, bearer tokens")
    mask_network: bool = Field(default=True, description="Mask internal IP addresses, private hostnames, subnets")
    mask_financial: bool = Field(default=True, description="Mask credit card numbers, account identifiers")
    redaction_placeholder: str = Field(default="[REDACTED_{TYPE}]", description="Placeholder template for masked items")


class ConnectorConfig(BaseModel):
    """
    Configuration for an enterprise ITSM, DevOps, or Custom source connector.
    """
    connector_id: str = Field(..., description="Unique connector identifier (e.g. jira-prod-01)")
    name: str = Field(..., description="Human readable name (e.g. Atlassian Jira Service Management)")
    category: ConnectorCategory = Field(default=ConnectorCategory.ITSM, description="Connector category")
    connector_type: ConnectorType = Field(..., description="ITSM / DevOps Platform type")
    base_url: str = Field(..., description="Instance URL, DB Host, or Webhook Target")
    auth_type: AuthType = Field(default=AuthType.API_TOKEN)
    username_or_email: Optional[str] = Field(None, description="Service account or admin email")
    api_token_or_secret: Optional[str] = Field(None, description="API token, PAT, or OAuth secret (masked in API responses)")
    query_filter: Optional[str] = Field(None, description="JQL, sysparm_query, label query, or SQL SELECT statement")
    field_mapping: FieldMappingConfig = Field(default_factory=FieldMappingConfig)
    dlp_config: DLPConfig = Field(default_factory=DLPConfig)
    auto_sync_interval_hours: int = Field(default=24, description="Periodic synchronization interval")
    is_simulated_demo: bool = Field(default=True, description="Operates in offline simulated mode if no live credentials")
    icon_key: Optional[str] = Field(None, description="Frontend icon / brand identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = None
    last_sync_status: SyncStatus = Field(default=SyncStatus.IDLE)
    last_sync_message: Optional[str] = None
    total_tickets_synced: int = Field(default=0)


class SyncSummary(BaseModel):
    connector_id: str
    connector_type: ConnectorType
    status: SyncStatus
    tickets_fetched: int
    tickets_sanitized: int
    tickets_ingested: int
    errors: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


class AuditLogEntry(BaseModel):
    log_id: str = Field(..., description="Unique audit event ID (UUID or monotonic)")
    timestamp_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    actor_identity: str = Field(..., description="User email or service principal")
    role: UserPersona = Field(default=UserPersona.ANALYST)
    action_type: str = Field(..., description="INGESTION_SYNC, DLP_REDACTION, SPEC_DRAFTED, SPEC_APPROVED, EXPORT_DOWNLOADED")
    resource_id: str = Field(..., description="Target workflow, connector, or draft ID")
    details: str = Field(default="", description="Audit log human-readable details")
    audit_hash: str = Field(..., description="SHA-256 integrity hash")


class CustomWebhookPayload(BaseModel):
    ticket_id: str
    title: str
    description: Optional[str] = ""
    resolution_notes: Optional[str] = ""
    category: Optional[str] = "Custom Webhook"
    priority: Optional[str] = "Medium"
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    assignee: Optional[str] = "Webhook Service"
    estimated_active_handling_minutes: Optional[float] = 20.0
