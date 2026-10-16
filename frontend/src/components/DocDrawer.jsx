import React, { useState } from 'react';
import { 
  X, 
  BookOpen, 
  Calculator, 
  Search, 
  Workflow, 
  Cpu, 
  ShieldCheck, 
  Settings, 
  CheckCircle2, 
  AlertTriangle,
  FileCode,
  Lock,
  Layers,
  ArrowRight,
  Server,
  Bell,
  Sliders
} from 'lucide-react';

export default function DocDrawer({ isOpen, onClose, activeView = 'overview' }) {
  const [selectedSection, setSelectedSection] = useState(activeView);

  // Sync section with active view when drawer opens
  React.useEffect(() => {
    if (isOpen) {
      setSelectedSection(activeView);
    }
  }, [isOpen, activeView]);

  if (!isOpen) return null;

  const sections = [
    { id: 'overview', title: 'Executive Overview & ROI', icon: Calculator },
    { id: 'tickets', title: 'Ticket Explorer & Semantic Prep', icon: Search },
    { id: 'workflows', title: 'Workflow Opportunities & Ranking', icon: Workflow },
    { id: 'studio', title: 'Automation Studio & ADK Safety', icon: Cpu },
    { id: 'evaluation', title: 'Evaluation Center & Zero Leakage', icon: ShieldCheck },
    { id: 'config', title: 'Connectors & Cloud DLP', icon: Settings },
    { id: 'chatops_pdf', title: 'Enterprise ChatOps & PDF Memos', icon: Bell },
    { id: 'queue_limits', title: 'Distributed Queue & Rate Limiter', icon: Sliders },
    { id: 'terraform_iac', title: 'Cloud Infrastructure & Terraform IaC', icon: Server },
    { id: 'multitenant_sso', title: 'Multi-Tenant Architecture & SSO', icon: Lock },
  ];

  return (
    <div className="doc-drawer-overlay" onClick={onClose}>
      <div className="doc-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="doc-drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: '#eff6ff', color: '#2563eb', padding: '6px', borderRadius: '6px' }}>
              <BookOpen size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>Platform Guide &amp; System Docs</h2>
              <p style={{ fontSize: '0.78rem', color: '#64748b' }}>Mathematical formulations, architectural boundaries &amp; integration specs</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="btn-icon"
            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', padding: '4px' }}
            aria-label="Close documentation drawer"
          >
            <X size={20} />
          </button>
        </div>

        {/* Section Navigation Tabs */}
        <div className="doc-drawer-tabs">
          {sections.map(s => {
            const Icon = s.icon;
            const isActive = selectedSection === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setSelectedSection(s.id)}
                className={`doc-tab-btn ${isActive ? 'active' : ''}`}
              >
                <Icon size={14} />
                <span>{s.title.split(' & ')[0]}</span>
              </button>
            );
          })}
        </div>

        {/* Drawer Content Body */}
        <div className="doc-drawer-body">
          {selectedSection === 'overview' && (
            <div className="doc-section">
              <span className="badge badge-blue">Executive Overview</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Deterministic Financial Quantification &amp; ROI
              </h3>
              
              <div className="doc-alert-info">
                <strong>Core Architectural Pillar:</strong> No hallucinated metrics. All dollar amounts, hours saved, and recurring volumes are calculated via deterministic SQL logic executed directly against ingested ticket timestamps.
              </div>

              <h4>1. The Mathematical ROI Formula</h4>
              <p>For any identified workflow cluster, the annual financial value is calculated as:</p>
              <pre className="doc-code-block">
{`Annual Hours Saved = (Total Handling Minutes / 60) / (Date Span in Months) * 12 * Automatable_Pct
Annual Labor Cost Saved = Annual Hours Saved * Hourly Labor Rate ($/hour)`}
              </pre>
              <p style={{ fontSize: '0.85rem', color: '#475569' }}>
                Where default parameters are <code>Automatable_Pct = 75% (0.75)</code> and <code>Hourly Labor Rate = $65.00/hour</code> (fully loaded enterprise engineer cost).
              </p>

              <h4>2. Calendar MTTR vs. Active Handling Time (Critical Distinction)</h4>
              <p>
                A standard ITSM ticket might show an elapsed calendar duration (Mean Time To Resolution) of <strong>26 hours</strong>. However, 25 hours of that was inactive queue wait time (overnight pauses, waiting for customer email replies, weekend queue stagnation).
              </p>
              <ul className="doc-list">
                <li><strong>Inactive Calendar Time:</strong> Time ticket spent in pending/assigned states without active work.</li>
                <li><strong>Active Handling Time:</strong> The actual engineering labor minutes spent executing diagnostic steps, reading logs, and applying fixes.</li>
              </ul>
              <p>
                Multiplying calendar MTTR by hourly engineering rates creates multi-million dollar fictitious ROI claims. Our agent deterministically isolates active handling minutes from work notes, time-worked fields, and resolution complexity.
              </p>

              <h4>3. Key Metric Definitions</h4>
              <table className="doc-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>SQL / Deterministic Definition</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Monthly Volume</strong></td>
                    <td><code>COUNT(ticket_id) / span_months</code></td>
                  </tr>
                  <tr>
                    <td><strong>Monthly Handling Hours</strong></td>
                    <td><code>SUM(handling_minutes) / 60 / span_months</code></td>
                  </tr>
                  <tr>
                    <td><strong>Potential Annual Savings</strong></td>
                    <td><code>(Monthly Hours * 12 * 0.75) * $65.00</code></td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {selectedSection === 'tickets' && (
            <div className="doc-section">
              <span className="badge badge-purple">Ticket Explorer</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Semantic Normalization, Clustering &amp; Noise Isolation
              </h3>

              <div className="doc-alert-info">
                <strong>Ingestion Integrity:</strong> Unstructured natural language resolution notes and incident summaries contain noise, repetitive email headers, and one-off anomalies.
              </div>

              <h4>1. Text Normalization Pipeline</h4>
              <p>Before text is vectorized for pattern recognition, the agent executes preprocessing steps:</p>
              <ul className="doc-list">
                <li>Stripping greeting boilerplate (e.g., <em>"Hello Team, please find below..."</em>).</li>
                <li>Redacting PII and credentials via Cloud DLP (tokens, IPs, emails).</li>
                <li>Tokenizing command snippets and technical identifiers (e.g., <code>kubectl</code>, <code>terraform</code>, <code>OOMKilled</code>).</li>
              </ul>

              <h4>2. Separation of Recurrent Workflows vs. One-Off Noise</h4>
              <p>
                In any enterprise environment, approximately <strong>25% to 35% of all tickets</strong> are idiosyncratic one-off issues (e.g., <em>"Monitor flickering on 4th floor conference room TV"</em>).
              </p>
              <p>
                The mining agent separates one-off noise tickets from dense programmatic clusters. Only clusters with recurrence frequency <strong>&ge; 10 tickets/quarter</strong> are promoted to candidate automation workflows.
              </p>

              <h4>3. Search &amp; Filter Operators</h4>
              <p>
                The Ticket Explorer supports full-text search across titles, descriptions, categories, and resolution notes with immediate real-time filtering.
              </p>
            </div>
          )}

          {selectedSection === 'workflows' && (
            <div className="doc-section">
              <span className="badge badge-amber">Workflow Opportunities</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                The 4-Factor Opportunity Ranking Formula
              </h3>

              <p>
                To prevent engineers from building low-value automations or tackling high-risk monolithic tasks first, candidate workflows are ranked using a transparent, multi-dimensional scoring model:
              </p>

              <pre className="doc-code-block">
{`Rank Score = 
    0.40 * Normalized(Annual Hours Saved) + 
    0.25 * Normalized(Monthly Ticket Recurrence) + 
    0.20 * Normalized(Clustering Semantic Confidence) + 
    0.15 * Normalized(Implementation Ease Score)`}
              </pre>

              <h4>Implementation Ease Weights</h4>
              <table className="doc-table">
                <thead>
                  <tr>
                    <th>Complexity</th>
                    <th>Ease Score</th>
                    <th>Characteristics</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><span className="badge badge-green">Low</span></td>
                    <td><code>1.00</code></td>
                    <td>Deterministic single-system API call or script (e.g. cache flush, account reset).</td>
                  </tr>
                  <tr>
                    <td><span className="badge badge-amber">Medium</span></td>
                    <td><code>0.65</code></td>
                    <td>Multi-step procedural workflow with conditional health check (e.g. K8s OOM triage, cert renewal).</td>
                  </tr>
                  <tr>
                    <td><span className="badge badge-red">High</span></td>
                    <td><code>0.35</code></td>
                    <td>Distributed state coordination, cloud IAM drift, or DB migration lock cleanup.</td>
                  </tr>
                </tbody>
              </table>

              <h4>Confidence Score</h4>
              <p>
                Represents semantic cluster cohesion derived from vector cosine similarity. High confidence (&gt; 85%) indicates standardized, highly repeatable incident remediation patterns across engineers.
              </p>
            </div>
          )}

          {selectedSection === 'studio' && (
            <div className="doc-section">
              <span className="badge badge-blue">Automation Studio</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Google ADK Multi-Step Orchestration &amp; Governance
              </h3>

              <div className="doc-alert-danger">
                <strong>CRITICAL GOVERNANCE BOUNDARY:</strong> The Workflow Mining Agent operates strictly in advisory mode. 
                Human approval is a recorded compliance decision, <strong>NOT permission to execute</strong> scripts. The agent NEVER triggers execution automatically.
              </div>

              <h4>1. Grounded Steps vs. Architectural Recommendations</h4>
              <ul className="doc-list">
                <li>
                  <strong>✅ Evidence-Grounded Steps:</strong> Extracted directly from resolution notes of closed historical tickets with specific citations (e.g., <em>"Ticket INC-1029 notes: executed kubectl logs --previous"</em>).
                </li>
                <li>
                  <strong>💡 Architectural Recommendations:</strong> Best-practice safety assertions synthesized by Google ADK (e.g., automated health check assertions, idempotency guards, and rollback strategies).
                </li>
              </ul>

              <h4>2. Multi-Target Automation Exporters</h4>
              <p>Discovered workflows can be exported with one click into enterprise deployment runbooks:</p>
              <ul className="doc-list">
                <li><strong>ServiceNow Flow Designer:</strong> Native JSON action definition schema ready for Flow Designer import.</li>
                <li><strong>Jira Automation Rules:</strong> Trigger-condition-action rule JSON.</li>
                <li><strong>GitHub Actions YAML:</strong> Automated CI/CD remediation pipeline with checkout, verification, and step execution.</li>
                <li><strong>Ansible Playbooks:</strong> Host and VM level automation with idempotency checks.</li>
                <li><strong>Executable Python Scripts:</strong> Clean Python 3 script boilerplate with mocked clients, logging, and exception handling.</li>
                <li><strong>CFO/CIO Executive Business Case:</strong> Print-ready executive memo with financial ROI and governance sign-off fields.</li>
              </ul>
            </div>
          )}

          {selectedSection === 'evaluation' && (
            <div className="doc-section">
              <span className="badge badge-green">Evaluation Center</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Scientific Benchmark &amp; Zero Ground-Truth Leakage
              </h3>

              <div className="doc-alert-info">
                <strong>Rigorous Evaluation Protocol:</strong> Demonstrating algorithmic honesty by benchmarking unsupervised cluster discovery against planted ground-truth workflows.
              </div>

              <h4>1. Zero Ground-Truth Leakage Guarantee</h4>
              <p>
                In synthetic benchmarking, each ticket has hidden evaluation metadata (<code>workflow_ground_truth</code> and <code>handling_minutes_ground_truth</code>).
              </p>
              <p>
                Our architecture enforces a <strong>hard quarantine boundary</strong>:
              </p>
              <ul className="doc-list">
                <li>Clustering algorithms (K-Means / Gemini embeddings) only see title, description, category, and resolution notes.</li>
                <li>Google ADK agents generating runbooks only inspect sanitised ticket text.</li>
                <li>Ground-truth labels are queried exclusively at evaluation time inside <code>backend/services/evaluation_service.py</code> to compute Precision, Recall, and F1.</li>
              </ul>

              <h4>2. Metric Calculations</h4>
              <table className="doc-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Scientific Formula</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Precision</strong></td>
                    <td><code>True Positives / (True Positives + False Positives)</code></td>
                  </tr>
                  <tr>
                    <td><strong>Recall</strong></td>
                    <td><code>True Positives / (True Positives + False Negatives)</code></td>
                  </tr>
                  <tr>
                    <td><strong>F1 Score</strong></td>
                    <td><code>2 * (Precision * Recall) / (Precision + Recall)</code></td>
                  </tr>
                  <tr>
                    <td><strong>Time Error</strong></td>
                    <td><code>|Estimated Hours - Ground Truth Hours| / Ground Truth Hours</code></td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {selectedSection === 'config' && (
            <div className="doc-section">
              <span className="badge badge-purple">Settings &amp; Connectors</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Universal Connector Catalog &amp; Cloud DLP Privacy
              </h3>

              <h4>1. Supported Connector Pathways</h4>
              <ul className="doc-list">
                <li><strong>Enterprise ITSM:</strong> ServiceNow (Table API &amp; OAuth), Jira Service Management (REST v3), Zendesk Support, Freshservice, BMC Helix.</li>
                <li><strong>DevOps &amp; SRE:</strong> GitHub Issues &amp; Projects, GitLab Issues, Linear, PagerDuty &amp; Opsgenie incidents.</li>
                <li><strong>Custom / In-House Platforms:</strong>
                  <ul>
                    <li><em>Inbound Webhook:</em> Tenant HMAC-SHA256 authenticated listener at <code>POST /api/connectors/custom/webhook</code>.</li>
                    <li><em>Custom REST/GraphQL Poller:</em> Configurable endpoint, custom headers, and JSONPath extraction schema (e.g. <code>$.data.issues[*].id</code>).</li>
                    <li><em>Direct Database Connect:</em> Read-only connection strings for PostgreSQL, MySQL, and Microsoft SQL Server.</li>
                  </ul>
                </li>
              </ul>

              <h4>2. Privacy-First Cloud DLP Pipeline</h4>
              <p>
                Prior to storing records in SQLite or BigQuery, every ticket passes through our data loss prevention (DLP) sanitization engine:
              </p>
              <ul className="doc-list">
                <li><code>[REDACTED_PASSWORD]</code>: Passwords and connection secrets.</li>
                <li><code>[REDACTED_API_TOKEN]</code>: GitHub PATs (<code>ghp_*</code>), Bearer tokens, and AWS/GCP API keys.</li>
                <li><code>[REDACTED_IPV4]</code>: Internal and external IPv4 addresses.</li>
                <li><code>[REDACTED_EMAIL]</code>: Customer and employee email addresses.</li>
              </ul>
            </div>
          )}

          {selectedSection === 'chatops_pdf' && (
            <div className="doc-section">
              <span className="badge badge-blue">ChatOps Notification Architecture</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Headless PDF Generator &amp; ChatOps Webhook Dispatcher
              </h3>
              
              <h4>1. Boardroom-Grade PDF Generator (ReportLab)</h4>
              <p>
                Generates vector-rendered executive business case memos directly on the backend via <code>PDFService</code> without requiring headless Chromium:
              </p>
              <ul className="doc-list">
                <li><strong>Executive Summary &amp; ROI Table:</strong> Deterministic annual dollar savings, hours saved, and labor rate.</li>
                <li><strong>System Architecture:</strong> APIs involved, preconditions, triggers, and ordered execution steps.</li>
                <li><strong>Enterprise Governance:</strong> Human approval gate requirements, RBAC reviewer signatures, and rollback runbooks.</li>
                <li><strong>Audit Footprint:</strong> Cryptographic SHA-256 event hash matching compliance audit trails.</li>
              </ul>

              <h4>2. ChatOps Dispatcher (Slack &amp; Teams)</h4>
              <p>
                Pre-formatted interactive notification payloads sent via incoming webhooks:
              </p>
              <ul className="doc-list">
                <li><strong>Slack Block Kit:</strong> Formatted headers, markdown summary blocks, financial metric callouts, and interactive "Review in Studio" action buttons.</li>
                <li><strong>Microsoft Teams Adaptive Cards:</strong> AdaptiveCard v1.4 schemas featuring color-coded FactSets and direct action links.</li>
                <li><strong>Demo Simulation Mode:</strong> URLs containing <code>DEMO</code>, <code>TEST</code>, or <code>LOCAL</code> are safely simulated offline with real payload previews and zero external network calls.</li>
              </ul>
            </div>
          )}

          {selectedSection === 'queue_limits' && (
            <div className="doc-section">
              <span className="badge badge-emerald">Distributed Queue Architecture</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Asynchronous Task Queue &amp; Token-Bucket Rate Limiter
              </h3>

              <h4>1. Leaky/Token-Bucket Rate Limiter</h4>
              <p>
                Protects against upstream vendor API throttling (HTTP 429 Too Many Requests) when polling large volumes of ServiceNow tickets, Jira issues, or GitHub repositories:
              </p>
              <ul className="doc-list">
                <li><strong>Burst Capacity:</strong> 50 maximum tokens.</li>
                <li><strong>Refill Rate:</strong> 15 tokens per second.</li>
                <li><strong>Adaptive Backoff:</strong> Automatic exponential delay if rate limit budget is temporarily depleted.</li>
              </ul>

              <h4>2. TaskQueueEngine Architecture</h4>
              <p>
                In-memory queue simulating Google Cloud Tasks. In local mode, workers process tasks with simulated latency and audit logging. In production GCP mode, tasks bind directly to Cloud Tasks queues targeting Cloud Run worker endpoints.
              </p>
            </div>
          )}

          {selectedSection === 'terraform_iac' && (
            <div className="doc-section">
              <span className="badge badge-purple">Infrastructure & IaC Architecture</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Production Google Cloud Platform Infrastructure-as-Code
              </h3>
              
              <p>
                Located in <code>deploy/terraform/</code>, provides enterprise-grade infrastructure deployable with a single <code>terraform apply</code>:
              </p>
              <ul className="doc-list">
                <li><code>main.tf</code>: Enables 9 essential Google Cloud APIs (Cloud Run, BigQuery, Vertex AI, Cloud DLP, Cloud KMS, Secret Manager, Cloud Tasks, Artifact Registry, Compute Engine).</li>
                <li><code>cloud_run.tf</code>: High-availability Cloud Run v2 service with horizontal autoscaling (1 to 20 instances) and HTTP liveness/startup probes at <code>/health</code>.</li>
                <li><code>bigquery.tf</code>: Multi-tenant dataset (<code>workflow_mining_prod</code>) with daily partitioning and clustering by <code>tenant_id</code>.</li>
                <li><code>security_iam.tf</code>: Cloud KMS KeyRing with 90-day auto-rotating Customer-Managed Encryption Keys (CMEK), Cloud Armor WAF IP rate limiting, and least-privilege IAM service accounts.</li>
                <li><code>variables.tf</code> &amp; <code>outputs.tf</code>: Production-ready parameters and exportable outputs.</li>
              </ul>
            </div>
          )}

          {selectedSection === 'multitenant_sso' && (
            <div className="doc-section">
              <span className="badge badge-amber">Multi-Tenant SSO Architecture</span>
              <h3 style={{ marginTop: '10px', fontSize: '1.25rem', fontWeight: 700 }}>
                Multi-Tenant Isolation &amp; SAML 2.0 / OIDC SSO Handshake
              </h3>

              <h4>1. Multi-Tenant Directory Context</h4>
              <p>
                Enforces strict data partition boundaries. All ingested tickets, discovered clusters, and audit events carry an immutable <code>tenant_id</code>:
              </p>
              <ul className="doc-list">
                <li><code>tenant_acme_global</code>: Acme Global Enterprises (Enterprise Tier, Production)</li>
                <li><code>tenant_apex_financial</code>: Apex Financial Group (FinTech Tier, Staging)</li>
                <li><code>tenant_cloudscale_sre</code>: CloudScale DevOps (High-Growth Tier, Production)</li>
                <li><code>tenant_demo_sandbox</code>: Demo Sandbox (Evaluation Tier, Local)</li>
              </ul>

              <h4>2. SAML 2.0 / OIDC Authentication Handshake</h4>
              <p>
                Enterprise single sign-on simulator supporting Okta, Azure AD (Entra ID), and PingFederate:
              </p>
              <ul className="doc-list">
                <li><code>POST /api/auth/saml/login</code>: Generates standard XML <code>samlp:AuthnRequest</code> payload with RelayState and SP Entity ID.</li>
                <li><code>POST /api/auth/saml/callback</code>: Exchanges SAML assertions, validates claims, and maps corporate directory groups into platform RBAC roles.</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
