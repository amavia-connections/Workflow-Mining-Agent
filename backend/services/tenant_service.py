"""
Enterprise Multi-Tenant Data Isolation & SAML 2.0 / OIDC SSO Provider.
AI Builder Cup 2026.
"""
from typing import Dict, Any, List, Optional
import uuid
import base64
from datetime import datetime

from backend.models.connector import UserPersona


# Enterprise Tenants Directory
ENTERPRISE_TENANTS = {
    "tenant_acme_global": {
        "tenant_id": "tenant_acme_global",
        "name": "Acme Global Manufacturing",
        "domain": "acmeglobal.com",
        "tier": "Enterprise Platinum",
        "sso_provider": "Okta Enterprise SSO",
        "idp_entity_id": "https://acme-global.okta.com/app/exk991823746",
        "active_connectors": ["jira-enterprise-01", "pagerduty-incidents-01"],
        "created_at": "2026-01-15T00:00:00Z"
    },
    "tenant_apex_bank": {
        "tenant_id": "tenant_apex_bank",
        "name": "Apex Financial Group",
        "domain": "apexbank.corp",
        "tier": "Regulated Financial (SOC2 + FedRAMP)",
        "sso_provider": "Microsoft Entra ID (Azure AD)",
        "idp_entity_id": "https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47",
        "active_connectors": ["servicenow-enterprise-01", "gitlab-issues-01"],
        "created_at": "2026-02-01T00:00:00Z"
    },
    "tenant_cloudscale": {
        "tenant_id": "tenant_cloudscale",
        "name": "CloudScale DevOps Platform",
        "domain": "cloudscale.io",
        "tier": "Enterprise Gold",
        "sso_provider": "Google Cloud Identity (OIDC)",
        "idp_entity_id": "https://accounts.google.com/o/saml2?idpid=C039281a",
        "active_connectors": ["github-issues-01", "linear-app-01"],
        "created_at": "2026-03-10T00:00:00Z"
    },
    "tenant_demo_sandbox": {
        "tenant_id": "tenant_demo_sandbox",
        "name": "Default Demo Enterprise",
        "domain": "enterprise-demo.internal",
        "tier": "Developer Sandbox",
        "sso_provider": "Local Enterprise Simulator",
        "idp_entity_id": "http://localhost:8000/saml/idp",
        "active_connectors": ["custom-webhook-01", "servicenow-enterprise-01"],
        "created_at": "2026-04-01T00:00:00Z"
    }
}


class TenantContextManager:
    """Manages active enterprise tenant state, SAML tokens, and RBAC claims."""
    def __init__(self):
        self.active_tenant_id = "tenant_demo_sandbox"
        self.active_session: Dict[str, Any] = {
            "session_id": "SESS-ENTERPRISE-DEMO-01",
            "user_id": "usr_991823746",
            "email": "sarah.connor@enterprise.corp",
            "full_name": "Sarah Connor",
            "role": "Governance Approver",
            "tenant_id": "tenant_demo_sandbox",
            "idp_issuer": "Okta Enterprise SSO",
            "saml_groups": ["SRE-Tech-Leads", "Change-Advisory-Board"],
            "authenticated_at": datetime.utcnow().isoformat()
        }

    def get_active_tenant(self) -> Dict[str, Any]:
        return ENTERPRISE_TENANTS.get(self.active_tenant_id, ENTERPRISE_TENANTS["tenant_demo_sandbox"])

    def list_tenants(self) -> List[Dict[str, Any]]:
        return list(ENTERPRISE_TENANTS.values())

    def switch_tenant(self, tenant_id: str) -> Dict[str, Any]:
        if tenant_id in ENTERPRISE_TENANTS:
            self.active_tenant_id = tenant_id
            self.active_session["tenant_id"] = tenant_id
            self.active_session["email"] = f"admin@{ENTERPRISE_TENANTS[tenant_id]['domain']}"
        return self.get_active_tenant()

    def generate_saml_auth_request(self, idp_name: str) -> Dict[str, Any]:
        """Generates a SAML 2.0 AuthnRequest XML structure."""
        req_id = f"AUTHN-{uuid.uuid4().hex[:12].upper()}"
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    ID="{req_id}"
                    Version="2.0"
                    IssueInstant="{datetime.utcnow().isoformat()}Z"
                    Destination="https://login.idp.enterprise/{idp_name}"
                    AssertionConsumerServiceURL="http://localhost:8000/api/auth/saml/callback">
    <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">https://workflow-mining.enterprise.corp</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress" AllowCreate="true"/>
</samlp:AuthnRequest>"""
        encoded = base64.b64encode(xml_template.encode("utf-8")).decode("utf-8")
        return {
            "request_id": req_id,
            "idp_name": idp_name,
            "relay_state": f"tenant={self.active_tenant_id}",
            "saml_request_encoded": encoded,
            "saml_request_xml": xml_template
        }

    def simulate_saml_login(self, email: str, role: str, tenant_id: str) -> Dict[str, Any]:
        """Simulates successful SAML 2.0 assertion verification."""
        if tenant_id in ENTERPRISE_TENANTS:
            self.active_tenant_id = tenant_id

        self.active_session = {
            "session_id": f"SESS-{uuid.uuid4().hex[:10].upper()}",
            "user_id": f"usr_{uuid.uuid4().hex[:8]}",
            "email": email,
            "full_name": email.split("@")[0].replace(".", " ").title(),
            "role": role,
            "tenant_id": self.active_tenant_id,
            "idp_issuer": ENTERPRISE_TENANTS.get(self.active_tenant_id, {}).get("sso_provider", "Corporate SAML"),
            "saml_groups": ["Enterprise-Users", f"Role-{role.replace(' ', '')}"],
            "authenticated_at": datetime.utcnow().isoformat()
        }
        return self.active_session


# Singleton Tenant Manager instance
tenant_manager = TenantContextManager()
