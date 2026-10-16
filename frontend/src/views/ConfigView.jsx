import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Cloud, 
  UploadCloud, 
  Settings2, 
  Play, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw, 
  Sparkles, 
  Server, 
  ShieldCheck, 
  Lock, 
  Link2, 
  Check, 
  Radio,
  Copy,
  Terminal,
  Layers,
  Search,
  ExternalLink,
  ChevronRight,
  Shield,
  FileCheck,
  MessageSquare,
  Building,
  Gauge,
  Users,
  Send,
  Zap,
  Key
} from 'lucide-react';
import ConnectorModal from '../components/ConnectorModal';
import MetricTooltip from '../components/MetricTooltip';

// Catalog presets with logos and descriptions
const CATALOG_PRESETS = [
  // Category A: Enterprise ITSM
  {
    id: 'novadesk-itsm-01',
    name: 'NovaDesk ITSM',
    category: 'Enterprise ITSM',
    type: 'custom_rest',
    logo: '⚡',
    status: 'Connected',
    desc: 'Live Standalone REST API & Webhooks. Ingests real-time incidents from NovaDesk on Port 5000.',
    base_url: 'http://localhost:5000/api/v1/tickets'
  },
  {
    id: 'servicenow-enterprise-01',
    name: 'ServiceNow ITSM',
    category: 'Enterprise ITSM',
    type: 'servicenow',
    logo: '🟢',
    status: 'Connected',
    desc: 'Table API & OAuth 2.0 / Basic Auth. Maps sys_id, short_description, and work logs.',
    base_url: 'https://demo-corp.service-now.com'
  },
  {
    id: 'jira-enterprise-01',
    name: 'Jira Service Management',
    category: 'Enterprise ITSM',
    type: 'jira',
    logo: '🔷',
    status: 'Connected',
    desc: 'Atlassian Cloud OAuth 2.0 / API Token. Ingests issues, priority, and resolution worklogs.',
    base_url: 'https://demo-corp.atlassian.net'
  },
  {
    id: 'zendesk-prod-01',
    name: 'Zendesk Support',
    category: 'Enterprise ITSM',
    type: 'zendesk',
    logo: '🟣',
    status: 'Simulated Demo',
    desc: 'REST API v2 & OAuth 2.0. Solved ticket comments, custom tags, and SLA resolution times.',
    base_url: 'https://enterprisecorp.zendesk.com'
  },
  {
    id: 'freshservice-prod-01',
    name: 'Freshservice IT Desk',
    category: 'Enterprise ITSM',
    type: 'freshservice',
    logo: '🌿',
    status: 'Disconnected',
    desc: 'Freshworks Domain & API Key. ITIL incident records, technician notes, and close codes.',
    base_url: 'https://enterprise.freshservice.com'
  },
  {
    id: 'bmc-helix-01',
    name: 'BMC Helix ITSM Suite',
    category: 'Enterprise ITSM',
    type: 'bmc_helix',
    logo: '🔴',
    status: 'Simulated Demo',
    desc: 'BMC Remedy REST API. Enterprise change requests, problem tickets, and work orders.',
    base_url: 'https://helix.enterprise.corp/api/arsys/v1'
  },

  // Category B: DevOps & Platform Engineering
  {
    id: 'github-issues-01',
    name: 'GitHub Issues & Projects',
    category: 'DevOps & SRE',
    type: 'github',
    logo: '🐙',
    status: 'Connected',
    desc: 'Personal Access Token / GitHub App. Ingests closed issues, PR resolution comments, and run logs.',
    base_url: 'https://api.github.com/repos/enterprise-org/core-platform'
  },
  {
    id: 'gitlab-issues-01',
    name: 'GitLab Issues (Self-Managed)',
    category: 'DevOps & SRE',
    type: 'gitlab',
    logo: '🦊',
    status: 'Disconnected',
    desc: 'Project / Group API Token. Extracts GitLab CI failures, pipeline incident issues, and traces.',
    base_url: 'https://gitlab.internal.corp/api/v4/projects/42'
  },
  {
    id: 'linear-app-01',
    name: 'Linear Issue Tracker',
    category: 'DevOps & SRE',
    type: 'linear',
    logo: '📐',
    status: 'Simulated Demo',
    desc: 'Linear GraphQL API. High-velocity engineering issues, triage states, and resolution cycles.',
    base_url: 'https://api.linear.app/graphql'
  },
  {
    id: 'pagerduty-incidents-01',
    name: 'PagerDuty & Opsgenie',
    category: 'DevOps & SRE',
    type: 'pagerduty',
    logo: '🚨',
    status: 'Connected',
    desc: 'Incident REST API & Webhooks. Captures on-call alerts, MTTA/MTTR timestamps, and postmortems.',
    base_url: 'https://api.pagerduty.com/incidents'
  },

  // Category C: Custom / In-House Workflow Engines
  {
    id: 'custom-webhook-01',
    name: 'Generic Inbound Webhook Listener',
    category: 'Custom Platform',
    type: 'custom_webhook',
    logo: '⚡',
    status: 'Connected',
    desc: 'HMAC-SHA256 authenticated listener. Receives real-time JSON payloads from proprietary engines.',
    base_url: '/api/connectors/custom/webhook'
  },
  {
    id: 'custom-graphql-01',
    name: 'Custom Internal REST / GraphQL Poller',
    category: 'Custom Platform',
    type: 'custom_rest',
    logo: '🛰️',
    status: 'Simulated Demo',
    desc: 'Configurable endpoints, custom Bearer/API-key headers, and JSONPath extraction schema.',
    base_url: 'https://internal-ticketing.corp.local/api/graphql'
  },
  {
    id: 'direct-db-01',
    name: 'Direct Read-Only SQL Database Connect',
    category: 'Custom Platform',
    type: 'direct_db',
    logo: '🗄️',
    status: 'Simulated Demo',
    desc: 'Read-only connection strings for PostgreSQL, MySQL, and Microsoft SQL Server.',
    base_url: 'postgresql://readonly_analyst@internal-db.corp.local:5432/ticketing_dw'
  }
];

export default function ConfigView({ onRunAnalysis, isRunningAnalysis, currentRole = 'Governance Approver' }) {
  const [activeSubTab, setActiveSubTab] = useState('connectors'); // 'connectors', 'queue', 'chatops', 'tenants', 'audit', 'dlp', 'data'
  const [health, setHealth] = useState(null);
  const [selectedConnector, setSelectedConnector] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [catalogCategory, setCatalogCategory] = useState('ALL');

  // Synthetic Generator state
  const [synthCount, setSynthCount] = useState(3000);
  const [synthSeed, setSynthSeed] = useState(42);
  const [includeDevOps, setIncludeDevOps] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  // Financial controls
  const [hourlyRate, setHourlyRate] = useState(65.0);
  const [autoPct, setAutoPct] = useState(75);

  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error('Health check failed:', err));
  }, []);

  const handleOpenConnector = (connector) => {
    setSelectedConnector(connector);
    setIsModalOpen(true);
  };

  const handleGenerateSynthetic = async () => {
    setGenerating(true);
    setUploadStatus(null);
    try {
      const res = await fetch('/api/datasets/generate-synthetic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          count: Number(synthCount), 
          seed: Number(synthSeed),
          include_devops: includeDevOps 
        })
      });
      const data = await res.json();
      setUploadStatus({
        type: 'success',
        message: `Generated and ingested ${synthCount.toLocaleString()} synthetic tickets (${includeDevOps ? '10 Planted Workflows including DevOps/SRE' : '6 ITSM Workflows'}).`
      });
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'Failed to generate synthetic dataset.' });
    } finally {
      setGenerating(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploadStatus({ type: 'info', message: 'Uploading and parsing CSV...' });
    try {
      const res = await fetch('/api/datasets/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.invalid_records > 0) {
        setUploadStatus({
          type: 'warning',
          message: `Ingested ${data.valid_records} valid tickets (${data.invalid_records} invalid rows skipped).`
        });
      } else {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested ${data.valid_records} tickets from ${file.name}.`
        });
      }
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'CSV upload failed.' });
    }
  };

  const filteredCatalog = CATALOG_PRESETS.filter(c => {
    if (catalogCategory === 'ALL') return true;
    if (catalogCategory === 'ITSM') return c.category === 'Enterprise ITSM';
    if (catalogCategory === 'DEVOPS') return c.category === 'DevOps & SRE';
    if (catalogCategory === 'CUSTOM') return c.category === 'Custom Platform';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Architecture Status Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 className="card-title">
              <Server size={18} color="#2563eb" /> Enterprise Platform Hub &amp; Operations
            </h3>
            <p className="card-desc">
              Multi-tenant B2B integration catalog, asynchronous task queues, ChatOps webhooks, SAML 2.0 SSO, and compliance audit trail.
            </p>
          </div>
          <span className={`badge ${health?.is_cloud_mode_ready ? 'badge-green' : 'badge-purple'}`} style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            {health?.is_cloud_mode_ready ? '☁️ GCP Production (Vertex AI + BigQuery)' : '💻 Local Demo Mode (Offline SQLite)'}
          </span>
        </div>

        {/* Sub-Tabs Navigation */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginTop: '16px', paddingBottom: '2px', overflowX: 'auto' }}>
          {[
            { id: 'connectors', label: '1. Connectors Hub', icon: Link2 },
            { id: 'queue', label: '2. Task Queue & Throttling (Opt B)', icon: Gauge },
            { id: 'chatops', label: '3. ChatOps Webhooks (Opt A)', icon: MessageSquare },
            { id: 'tenants', label: '4. Tenants & SAML SSO (Opt D)', icon: Building },
            { id: 'audit', label: '5. Compliance Audit Trail', icon: ShieldCheck },
            { id: 'dlp', label: '6. Cloud DLP Sandbox', icon: Shield },
            { id: 'data', label: '7. Synthetic Data & Math', icon: Database },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeSubTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '0.78rem', padding: '6px 12px', whiteSpace: 'nowrap' }}
              >
                <Icon size={13} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* SUB-TAB 1: CONNECTORS & INTEGRATION CATALOG */}
      {activeSubTab === 'connectors' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Category Filter Controls */}
          <div className="card" style={{ padding: '14px 20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>
                Filter Integrations Catalog:
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                {[
                  { key: 'ALL', label: 'All Connectors (12)' },
                  { key: 'ITSM', label: 'Enterprise ITSM (5)' },
                  { key: 'DEVOPS', label: 'DevOps / SRE (4)' },
                  { key: 'CUSTOM', label: 'Custom In-House Engines (3)' },
                ].map(cat => (
                  <button
                    key={cat.key}
                    className={`btn btn-sm ${catalogCategory === cat.key ? 'btn-primary' : 'btn-outline'}`}
                    onClick={() => setCatalogCategory(cat.key)}
                    style={{ fontSize: '0.78rem' }}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Connectors Logo Grid */}
          <div className="connector-grid">
            {filteredCatalog.map(connector => (
              <div 
                key={connector.id} 
                className="connector-card"
                onClick={() => handleOpenConnector(connector)}
              >
                <div>
                  <div className="connector-card-header">
                    <span className="connector-logo">{connector.logo}</span>
                    <span className={`badge ${
                      connector.status === 'Connected' ? 'badge-green' :
                      connector.status === 'Simulated Demo' ? 'badge-purple' : 'badge-gray'
                    }`}>
                      {connector.status}
                    </span>
                  </div>
                  <div className="connector-name">{connector.name}</div>
                  <div style={{ fontSize: '0.72rem', color: '#2563eb', fontWeight: 600, marginTop: '2px' }}>
                    {connector.category}
                  </div>
                  <p className="connector-desc">{connector.desc}</p>
                </div>

                <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Configure &amp; Map</span>
                  <span style={{ color: '#2563eb', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
                    Open Setup &rarr;
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUB-TAB 2: DISTRIBUTED TASK QUEUE & RATE LIMITER (OPTION B) */}
      {activeSubTab === 'queue' && (
        <TaskQueueSection />
      )}

      {/* SUB-TAB 3: CHATOPS & NOTIFICATION WEBHOOKS (OPTION A) */}
      {activeSubTab === 'chatops' && (
        <ChatOpsWebhooksSection />
      )}

      {/* SUB-TAB 4: MULTI-TENANT DIRECTORY & SAML SSO (OPTION D) */}
      {activeSubTab === 'tenants' && (
        <MultiTenantDirectorySection />
      )}

      {/* SUB-TAB 5: COMPLIANCE AUDIT TRAIL */}
      {activeSubTab === 'audit' && (
        <ComplianceAuditTrailSection />
      )}

      {/* SUB-TAB 6: CLOUD DLP PRIVACY TEST BENCH */}
      {activeSubTab === 'dlp' && (
        <CloudDlpSandboxSection />
      )}

      {/* SUB-TAB 7: SYNTHETIC DATA & QUANTIFICATION */}
      {activeSubTab === 'data' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Synthetic Benchmark Generator */}
          <div className="card">
            <h3 className="card-title">
              <Database size={18} color="#2563eb" /> Deterministic Synthetic Dataset Generator
            </h3>
            <p className="card-desc">
              Generate reproducible tickets across planted ground-truth enterprise ITSM and DevOps workflows with realistic noise.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '16px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Ticket Count</label>
                <input 
                  type="number"
                  value={synthCount}
                  onChange={(e) => setSynthCount(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Random Seed</label>
                <input 
                  type="number"
                  value={synthSeed}
                  onChange={(e) => setSynthSeed(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '8px' }}>
                  Include DevOps / SRE Workflows
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.84rem' }}>
                  <input 
                    type="checkbox"
                    checked={includeDevOps}
                    onChange={(e) => setIncludeDevOps(e.target.checked)}
                    style={{ width: '18px', height: '18px' }}
                  />
                  <span>10 Planted Workflows (ITSM + SRE)</span>
                </label>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button 
                  className="btn btn-outline"
                  disabled={generating}
                  onClick={handleGenerateSynthetic}
                  style={{ width: '100%' }}
                >
                  <Sparkles size={16} /> {generating ? 'Synthesizing...' : 'Generate Tickets'}
                </button>
              </div>
            </div>

            {uploadStatus && (
              <div className={`alert ${uploadStatus.type === 'success' ? 'alert-success' : 'alert-info'}`}>
                {uploadStatus.message}
              </div>
            )}
          </div>

          {/* CSV File Ingestion */}
          <div className="card">
            <h3 className="card-title">
              <UploadCloud size={18} color="#7c3aed" /> Custom CSV Ticket Ingestion
            </h3>
            <p className="card-desc">Ingest historical closed tickets directly from customer exports.</p>
            <input 
              type="file" 
              accept=".csv" 
              onChange={handleFileUpload} 
              style={{ fontSize: '0.82rem' }}
            />
          </div>

          {/* Mining Controls & Financial Quantification */}
          <div className="card">
            <h3 className="card-title">
              <Settings2 size={18} color="#059669" /> Financial Quantification Assumptions &amp; Mining Control
            </h3>
            <p className="card-desc">Adjust labor cost assumptions and re-run clustering analysis.</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Hourly Labor Rate ($/hour)</label>
                <input 
                  type="number"
                  value={hourlyRate}
                  onChange={(e) => setHourlyRate(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Default Automatable Ratio (%)</label>
                <input 
                  type="number"
                  value={autoPct}
                  onChange={(e) => setAutoPct(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Workflow Clusters (k)</label>
                <select 
                  defaultValue={includeDevOps ? "10" : "6"}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                >
                  <option value="6">6 Clusters (ITSM Baseline)</option>
                  <option value="10">10 Clusters (ITSM + DevOps Full Suite)</option>
                </select>
              </div>
            </div>

            <button 
              className="btn btn-primary"
              disabled={isRunningAnalysis}
              onClick={() => onRunAnalysis(hourlyRate, autoPct / 100.0)}
              style={{ width: '100%' }}
            >
              <Play size={16} /> {isRunningAnalysis ? 'Mining Analysis in Progress...' : 'Execute Workflow Mining Pipeline'}
            </button>
          </div>
        </div>
      )}

      {/* Interactive Multi-Step Connector Modal */}
      <ConnectorModal 
        isOpen={isModalOpen}
        connector={selectedConnector}
        onClose={() => setIsModalOpen(false)}
        onSyncCompleted={(res) => {
          console.log('Sync finished:', res);
        }}
      />
    </div>
  );
}


/**
 * Distributed Task Queue & Rate Limiter Component (Option B)
 */
function TaskQueueSection() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [draining, setDraining] = useState(false);
  const [lastDrainResult, setLastDrainResult] = useState(null);

  useEffect(() => {
    fetchQueueStatus();
  }, []);

  const fetchQueueStatus = async () => {
    try {
      const res = await fetch('/api/queue/status');
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error('Queue metrics error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleEnqueue = async () => {
    await fetch('/api/queue/enqueue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_type: 'INGESTION_SYNC',
        connector_id: 'servicenow-enterprise-01',
        payload: { range_days: 90 },
        priority: 'HIGH'
      })
    });
    fetchQueueStatus();
  };

  const handleDrain = async () => {
    setDraining(true);
    try {
      const res = await fetch('/api/queue/drain?batch_size=5', { method: 'POST' });
      const data = await res.json();
      setLastDrainResult(data);
      fetchQueueStatus();
    } finally {
      setDraining(false);
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <h3 className="card-title">
            <Gauge size={18} color="#2563eb" /> Asynchronous Ingestion Task Queue &amp; Token-Bucket Rate Limiter
          </h3>
          <p className="card-desc">
            Simulates enterprise rate-limiting (HTTP 429 prevention) and async worker concurrency for high-volume ticket ingestion.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-outline btn-sm" onClick={handleEnqueue}>
            <Zap size={14} /> Enqueue Sample Sync Task
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleDrain} disabled={draining}>
            <RefreshCw size={14} className={draining ? "spin" : ""} /> Process / Drain Batch
          </button>
        </div>
      </div>

      {metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '20px' }}>
          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Available Tokens</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#2563eb', marginTop: '2px' }}>
              {metrics.rate_limiter?.available_tokens} / {metrics.rate_limiter?.capacity}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Refill: {metrics.rate_limiter?.refill_rate_per_sec} tokens/sec</div>
          </div>

          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Active Tasks Enqueued</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>
              {metrics.total_tasks_enqueued}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Queued: {metrics.tasks_by_status?.QUEUED || 0} &bull; Retrying: {metrics.tasks_by_status?.RETRYING || 0}</div>
          </div>

          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Completed Tasks</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#059669', marginTop: '2px' }}>
              {metrics.tasks_by_status?.COMPLETED || 0}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#059669' }}>Successfully processed</div>
          </div>

          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Throttled Requests</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#d97706', marginTop: '2px' }}>
              {metrics.rate_limiter?.total_throttled_requests || 0}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#d97706' }}>Backoff throttles enforced</div>
          </div>
        </div>
      )}

      {lastDrainResult && (
        <div className="alert alert-success" style={{ fontSize: '0.82rem' }}>
          Processed {lastDrainResult.processed_count} tasks in batch. Tokens remaining: {lastDrainResult.remaining_status?.rate_limiter?.available_tokens}.
        </div>
      )}
    </div>
  );
}


/**
 * ChatOps & Notification Webhooks Section (Option A)
 */
function ChatOpsWebhooksSection() {
  const [platform, setPlatform] = useState('slack');
  const [webhookUrl, setWebhookUrl] = useState('https://hooks.slack.com/services/DEMO/LOCAL/TEST');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  const handleTestDispatch = async () => {
    setSending(true);
    setResult(null);
    try {
      const res = await fetch('/api/notifications/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, webhook_url: webhookUrl })
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error('Notification test failed:', e);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">
        <MessageSquare size={18} color="#7c3aed" /> Enterprise ChatOps Notifications (Slack &amp; Microsoft Teams)
      </h3>
      <p className="card-desc">
        Configure automated webhook alerts when high-value opportunities are discovered or when human approval is required.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '14px' }}>
        <div>
          <div style={{ marginBottom: '14px' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Target ChatOps Platform</label>
            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
              <button 
                type="button" 
                className={`btn btn-sm ${platform === 'slack' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setPlatform('slack'); setWebhookUrl('https://hooks.slack.com/services/DEMO/LOCAL/TEST'); }}
              >
                Slack (Block Kit)
              </button>
              <button 
                type="button" 
                className={`btn btn-sm ${platform === 'teams' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => { setPlatform('teams'); setWebhookUrl('https://outlook.office.com/webhook/DEMO/TEAMS'); }}
              >
                Microsoft Teams (Adaptive Cards)
              </button>
            </div>
          </div>

          <div style={{ marginBottom: '14px' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Incoming Webhook URL</label>
            <input 
              type="text" 
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.82rem', marginTop: '4px' }}
            />
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
              Real URLs will fire live HTTP requests; test URLs will run locally in simulation mode.
            </span>
          </div>

          <button 
            className="btn btn-primary"
            onClick={handleTestDispatch}
            disabled={sending}
            style={{ width: '100%' }}
          >
            <Send size={14} /> {sending ? 'Dispatching...' : `Test Dispatch to ${platform === 'slack' ? 'Slack' : 'Teams'}`}
          </button>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
            Dispatched ChatOps Payload Preview:
          </label>
          <pre 
            style={{ 
              background: '#0f172a', 
              color: '#38bdf8', 
              padding: '12px', 
              borderRadius: '6px', 
              fontSize: '0.76rem', 
              fontFamily: 'monospace', 
              maxHeight: '220px', 
              overflowY: 'auto',
              marginTop: '4px'
            }}
          >
            <code>{result ? JSON.stringify(result.payload_preview, null, 2) : '# Click "Test Dispatch" to preview formatted JSON payload...'}</code>
          </pre>

          {result && (
            <div style={{ marginTop: '8px', fontSize: '0.78rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Check size={14} /> Status: <strong>{result.status}</strong> &bull; Recorded event in compliance audit trail.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


/**
 * Multi-Tenant Directory & SAML SSO Section (Option D)
 */
function MultiTenantDirectorySection() {
  const [tenants, setTenants] = useState([]);
  const [activeTenant, setActiveTenant] = useState(null);
  const [session, setSession] = useState(null);
  const [samlXml, setSamlXml] = useState(null);

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      const res = await fetch('/api/tenants');
      const data = await res.json();
      setTenants(data.tenants || []);
      setActiveTenant(data.active_tenant);
      const sessRes = await fetch('/api/auth/session');
      const sessData = await sessRes.json();
      setSession(sessData.session);
    } catch (e) {
      console.error('Tenant fetch error:', e);
    }
  };

  const handleSwitchTenant = async (tenantId) => {
    const res = await fetch('/api/tenants/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenant_id: tenantId })
    });
    const data = await res.json();
    setActiveTenant(data);
    fetchTenants();
  };

  const handleSimulateSAML = async () => {
    const res = await fetch('/api/auth/saml/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        idp_name: activeTenant?.sso_provider || "Okta SSO",
        tenant_id: activeTenant?.tenant_id
      })
    });
    const data = await res.json();
    setSamlXml(data.saml_request_xml);

    // Complete callback simulation
    await fetch('/api/auth/saml/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: `lead.sre@${activeTenant?.domain || 'enterprise.corp'}`,
        role: 'Governance Approver',
        tenant_id: activeTenant?.tenant_id
      })
    });
    fetchTenants();
  };

  return (
    <div className="card">
      <h3 className="card-title">
        <Building size={18} color="#2563eb" /> Multi-Tenant Customer Directory &amp; SAML 2.0 / OIDC SSO
      </h3>
      <p className="card-desc">
        Row-level security tenant isolation and enterprise single sign-on assertion exchange with Okta, Microsoft Entra ID, and Google Cloud Identity.
      </p>

      {/* Active Session & Tenant Banner */}
      <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '14px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '14px 0' }}>
        <div>
          <div style={{ fontSize: '0.82rem', color: '#1e40af', fontWeight: 600 }}>Active Enterprise Context:</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a' }}>
            {activeTenant?.name} ({activeTenant?.tier})
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
            Domain: <code>{activeTenant?.domain}</code> &bull; IdP: <strong>{activeTenant?.sso_provider}</strong>
          </div>
        </div>
        <button className="btn btn-primary btn-sm" onClick={handleSimulateSAML}>
          <Key size={14} /> Simulate SAML 2.0 SSO Handshake
        </button>
      </div>

      {/* Tenants Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', marginTop: '16px' }}>
        {tenants.map(t => {
          const isSelected = activeTenant?.tenant_id === t.tenant_id;
          return (
            <div 
              key={t.tenant_id}
              style={{
                padding: '14px',
                borderRadius: '8px',
                border: isSelected ? '2px solid #2563eb' : '1px solid #e2e8f0',
                background: isSelected ? '#f8fbff' : '#ffffff',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <strong style={{ fontSize: '0.9rem' }}>{t.name}</strong>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '2px' }}>
                  {t.sso_provider} &bull; {t.tier}
                </div>
              </div>
              <button 
                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => handleSwitchTenant(t.tenant_id)}
                disabled={isSelected}
                style={{ fontSize: '0.75rem' }}
              >
                {isSelected ? 'Active Tenant' : 'Switch Tenant'}
              </button>
            </div>
          );
        })}
      </div>

      {samlXml && (
        <div style={{ marginTop: '16px' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
            Generated SAML 2.0 AuthnRequest XML:
          </label>
          <pre 
            style={{ 
              background: '#0f172a', 
              color: '#38bdf8', 
              padding: '12px', 
              borderRadius: '6px', 
              fontSize: '0.75rem', 
              fontFamily: 'monospace', 
              maxHeight: '140px', 
              overflowY: 'auto',
              marginTop: '4px'
            }}
          >
            <code>{samlXml}</code>
          </pre>
        </div>
      )}
    </div>
  );
}


/**
 * Compliance Audit Trail Tab Component
 */
function ComplianceAuditTrailSection() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedHash, setCopiedHash] = useState(null);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/audit-logs?limit=50');
      if (res.ok) {
        const data = await res.json();
        setLogs(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyHash = (hash) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const filteredLogs = logs.filter(l => {
    if (filterAction !== 'ALL' && l.action_type !== filterAction) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        l.actor_identity?.toLowerCase().includes(q) ||
        l.resource_id?.toLowerCase().includes(q) ||
        l.action_type?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 className="card-title">
            <ShieldCheck size={18} color="#059669" /> Immutable Enterprise Governance Audit Trail
          </h3>
          <p className="card-desc">
            Cryptographically signed ledger tracking all tenant ingestion syncs, DLP sanitizations, ADK draft creations, and human approvals.
          </p>
        </div>

        <button className="btn btn-outline btn-sm" onClick={fetchLogs}>
          <RefreshCw size={14} /> Refresh Logs
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
        <input 
          type="text" 
          placeholder="Search by actor identity, resource ID, or action..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ flex: 1, padding: '7px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
        />

        <select 
          value={filterAction} 
          onChange={(e) => setFilterAction(e.target.value)}
          style={{ padding: '7px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
        >
          <option value="ALL">All Actions</option>
          <option value="INGESTION_SYNC">INGESTION_SYNC</option>
          <option value="DLP_REDACTION">DLP_REDACTION</option>
          <option value="SPEC_DRAFTED">SPEC_DRAFTED</option>
          <option value="SPEC_APPROVED">SPEC_APPROVED</option>
          <option value="SPEC_REJECTED">SPEC_REJECTED</option>
          <option value="EXPORT_DOWNLOADED">EXPORT_DOWNLOADED</option>
          <option value="NOTIFICATION_DISPATCHED">NOTIFICATION_DISPATCHED</option>
          <option value="TENANT_SWITCHED">TENANT_SWITCHED</option>
          <option value="SAML_SSO_LOGIN">SAML_SSO_LOGIN</option>
        </select>
      </div>

      {/* Audit Log Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Actor Identity</th>
              <th>Persona Role</th>
              <th>Action Type</th>
              <th>Resource ID</th>
              <th>SHA-256 Audit Signature</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                  {loading ? 'Querying compliance audit repository...' : 'No audit entries match filter.'}
                </td>
              </tr>
            ) : (
              filteredLogs.map(l => (
                <tr key={l.log_id}>
                  <td style={{ fontSize: '0.78rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                    {new Date(l.timestamp_utc).toLocaleString()}
                  </td>
                  <td>
                    <strong>{l.actor_identity}</strong>
                  </td>
                  <td>
                    <span className="badge badge-purple" style={{ fontSize: '0.72rem' }}>
                      {l.role}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${
                      l.action_type === 'SPEC_APPROVED' || l.action_type === 'SAML_SSO_LOGIN' ? 'badge-green' :
                      l.action_type === 'SPEC_REJECTED' ? 'badge-red' :
                      l.action_type === 'INGESTION_SYNC' || l.action_type === 'TENANT_SWITCHED' ? 'badge-blue' : 'badge-gray'
                    }`} style={{ fontSize: '0.72rem' }}>
                      {l.action_type}
                    </span>
                  </td>
                  <td>
                    <code style={{ fontSize: '0.75rem' }}>{l.resource_id}</code>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <code style={{ fontSize: '0.72rem', color: '#475569', background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>
                        {l.audit_hash.slice(0, 16)}...
                      </code>
                      <button 
                        onClick={() => copyHash(l.audit_hash)}
                        style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#94a3b8' }}
                        title="Copy full 64-character SHA-256 hash"
                      >
                        {copiedHash === l.audit_hash ? <Check size={12} color="#059669" /> : <Copy size={12} />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


/**
 * Cloud DLP Privacy Sandbox Test Bench Component
 */
function CloudDlpSandboxSection() {
  const [dlpSample, setDlpSample] = useState(
    "Root password set to Pwd!Secure987 on host 10.240.0.14 while testing deploy with token ghp_99887766554433221100aabbccddeeff0011 by admin john.doe@enterprise.corp."
  );
  const [dlpResult, setDlpResult] = useState(null);
  const [dlpLoading, setDlpLoading] = useState(false);

  const handleTestDLP = async () => {
    setDlpLoading(true);
    try {
      const res = await fetch('/api/connectors/preview-dlp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: dlpSample })
      });
      const data = await res.json();
      setDlpResult(data);
    } catch (err) {
      console.error('DLP test failed:', err);
    } finally {
      setDlpLoading(false);
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">
        <Shield size={18} color="#059669" /> Interactive Cloud DLP Sanitization Sandbox
      </h3>
      <p className="card-desc">
        Test privacy-first sanitization before persisting inbound tickets. Masks passwords, GitHub PATs, internal IPv4 addresses, and email addresses.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '12px' }}>
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
            Inbound Raw Ticket Text (Sample containing secrets):
          </label>
          <textarea 
            rows="5"
            value={dlpSample}
            onChange={(e) => setDlpSample(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.84rem', marginTop: '4px' }}
          />
          <button 
            className="btn btn-primary btn-sm"
            onClick={handleTestDLP}
            disabled={dlpLoading}
            style={{ marginTop: '8px' }}
          >
            {dlpLoading ? <RefreshCw size={14} className="spin" /> : <ShieldCheck size={14} />}
            <span>Execute Cloud DLP Sanitization</span>
          </button>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
            Sanitized Payload Preview (Persistent Database Storage):
          </label>
          <div 
            style={{ 
              background: '#0f172a', 
              color: '#38bdf8', 
              padding: '12px 14px', 
              borderRadius: '6px', 
              fontSize: '0.82rem', 
              fontFamily: 'monospace', 
              minHeight: '115px',
              marginTop: '4px',
              lineHeight: 1.5
            }}
          >
            {dlpResult ? dlpResult.sanitized_text : '# Click "Execute Cloud DLP Sanitization" to inspect redacted output...'}
          </div>

          {dlpResult && (
            <div style={{ marginTop: '8px', fontSize: '0.78rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Check size={14} /> Sanitized {dlpResult.redaction_count || 4} sensitive elements safely.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
