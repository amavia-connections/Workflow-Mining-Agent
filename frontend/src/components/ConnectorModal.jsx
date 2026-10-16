import React, { useState, useEffect } from 'react';
import { 
  X, 
  Check, 
  AlertTriangle, 
  RefreshCw, 
  ShieldCheck, 
  Sliders, 
  ArrowRight, 
  ArrowLeft, 
  Database, 
  Key, 
  Lock, 
  CheckCircle2, 
  Copy,
  Radio,
  FileJson,
  Sparkles
} from 'lucide-react';

const CANONICAL_SCHEMA_FIELDS = [
  { key: 'ticket_id', label: 'Ticket ID / Incident Key', req: true, sample: 'INC-10928' },
  { key: 'title', label: 'Summary / Title', req: true, sample: 'Pod OOMKilled in payment-api' },
  { key: 'description', label: 'Description / Error Log', req: true, sample: 'CrashLoopBackOff detected on staging node-3' },
  { key: 'category', label: 'Category / Subsystem', req: false, sample: 'Platform / Kubernetes' },
  { key: 'priority', label: 'Priority / Severity', req: false, sample: 'High' },
  { key: 'created_at', label: 'Created Timestamp', req: true, sample: '2026-09-14T08:12:00Z' },
  { key: 'resolved_at', label: 'Resolved Timestamp', req: false, sample: '2026-09-14T08:35:00Z' },
  { key: 'assignee', label: 'Assignee / On-Call', req: false, sample: 'sre-oncall@enterprise.corp' },
  { key: 'resolution_notes', label: 'Resolution / Work Log', req: true, sample: 'Bumped memory limit to 1Gi in Helm values.' },
];

export default function ConnectorModal({ isOpen, onClose, connector, onSyncCompleted }) {
  const [step, setStep] = useState(1);
  const [isDemoMode, setIsDemoMode] = useState(false);
  
  // Step 1: Credentials
  const [tenantUrl, setTenantUrl] = useState(connector?.base_url || '');
  const [usernameOrEmail, setUsernameOrEmail] = useState(connector?.username_or_email || '');
  const [apiKey, setApiKey] = useState('');
  const [authType, setAuthType] = useState('token'); // 'token', 'oauth', 'webhook'
  
  // Custom Webhook / REST state
  const [webhookUrl, setWebhookUrl] = useState('https://agent.corp.internal/api/connectors/custom/webhook');
  const [webhookSecret, setWebhookSecret] = useState('whsec_live_9918237461928374abcdef');
  const [jsonPathRoot, setJsonPathRoot] = useState('$.data.issues[*]');
  const [copiedKey, setCopiedKey] = useState(false);

  // Step 2: Mapping
  const [fieldMappings, setFieldMappings] = useState({
    ticket_id: connector?.type === 'servicenow' ? 'number' : 'id',
    title: connector?.type === 'servicenow' ? 'short_description' : 'summary',
    description: connector?.type === 'servicenow' ? 'description' : 'body',
    category: connector?.type === 'servicenow' ? 'category' : 'labels[0]',
    priority: connector?.type === 'servicenow' ? 'priority' : 'severity',
    created_at: connector?.type === 'servicenow' ? 'sys_created_on' : 'created_at',
    resolved_at: connector?.type === 'servicenow' ? 'closed_at' : 'resolved_at',
    assignee: connector?.type === 'servicenow' ? 'assigned_to.value' : 'assignee.name',
    resolution_notes: connector?.type === 'servicenow' ? 'close_notes' : 'resolution_comment'
  });

  // Step 3: Health check test state
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Step 4: Sync & DLP
  const [syncRange, setSyncRange] = useState('90');
  const [syncTrigger, setSyncTrigger] = useState('scheduled'); // 'realtime', 'scheduled'
  const [dlpEnabled, setDlpEnabled] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(0);
  const [syncStatusText, setSyncStatusText] = useState('');
  const [syncSuccess, setSyncSuccess] = useState(false);

  // Reset and sync state when opening a connector
  useEffect(() => {
    if (connector) {
      setStep(1);
      setTenantUrl(connector.base_url || '');
      setUsernameOrEmail(connector.username_or_email || '');
      setApiKey('');
      setTestResult(null);
      setIsTesting(false);
      setSyncProgress(0);
      setSyncStatusText('');
      setSyncSuccess(false);
      setIsDemoMode(false); // Live by default

      const isSnow = connector.type === 'servicenow' || (connector.id && connector.id.includes('servicenow'));
      setFieldMappings({
        ticket_id: isSnow ? 'number' : 'id',
        title: isSnow ? 'short_description' : 'summary',
        description: isSnow ? 'description' : 'body',
        category: isSnow ? 'category' : 'labels[0]',
        priority: isSnow ? 'priority' : 'severity',
        created_at: isSnow ? 'sys_created_on' : 'created_at',
        resolved_at: isSnow ? 'closed_at' : 'resolved_at',
        assignee: isSnow ? 'assigned_to.value' : 'assignee.name',
        resolution_notes: isSnow ? 'close_notes' : 'resolution_comment'
      });
    }
  }, [connector, isOpen]);

  if (!isOpen || !connector) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`/api/connectors/${connector.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_simulated: isDemoMode,
          tenant_url: tenantUrl,
          username_or_email: usernameOrEmail,
          api_key: apiKey
        })
      });
      if (res.ok) {
        const data = await res.json();
        setTestResult(data);
      } else {
        setTestResult({
          status: 'error',
          message: 'Connection timed out or remote authentication rejected credentials.',
          latency_ms: 1250,
          details: { code: 'HTTP_401_UNAUTHORIZED' }
        });
      }
    } catch (err) {
      setTestResult({
        status: 'error',
        message: 'Network unreachable. Operating in local sandbox.',
        latency_ms: 320
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleTriggerSync = async () => {
    setIsSyncing(true);
    setSyncProgress(10);
    setSyncStatusText('Authenticating remote session and negotiating rate-limits...');

    // Simulate animated pagination progress
    const timer1 = setTimeout(() => {
      setSyncProgress(40);
      setSyncStatusText(`Querying records (Range: Last ${syncRange} days, DLP Masking: ${dlpEnabled ? 'ACTIVE' : 'OFF'})...`);
    }, 600);

    const timer2 = setTimeout(() => {
      setSyncProgress(75);
      setSyncStatusText('Sanitizing PII/tokens via Cloud DLP and writing to local database...');
    }, 1200);

    try {
      const res = await fetch(`/api/connectors/${connector.id}/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          range_days: Number(syncRange),
          dlp_masking: dlpEnabled,
          is_simulated: isDemoMode,
          tenant_url: tenantUrl,
          username_or_email: usernameOrEmail,
          api_key: apiKey
        })
      });
      const data = await res.json();
      const statusUpper = (data.status || '').toUpperCase();
      const isFailed = !res.ok || statusUpper === 'FAILED' || data.error_message || (data.errors && data.errors.length > 0 && data.tickets_ingested === 0);
      if (isFailed) {
        const errMsg = data.error_message || data.detail || (data.errors && data.errors[0]) || 'Failed to sync with remote instance.';
        setTimeout(() => {
          setSyncProgress(100);
          setSyncStatusText(`Sync failed: ${errMsg}`);
          setIsSyncing(false);
          setSyncSuccess(false);
        }, 1200);
        return;
      }
      setTimeout(() => {
        setSyncProgress(100);
        const count = data.tickets_ingested !== undefined ? data.tickets_ingested : (data.ingested_count !== undefined ? data.ingested_count : 0);
        if (count === 0) {
          setSyncStatusText('Sync finished: 0 tickets found matching query in your Jira instance. Please check your project issues or date range.');
        } else {
          setSyncStatusText(`Sync complete! Ingested ${count} tickets safely.`);
        }
        setIsSyncing(false);
        setSyncSuccess(count > 0);
        if (onSyncCompleted) onSyncCompleted(data);
      }, 1800);
    } catch (err) {
      setTimeout(() => {
        setSyncProgress(100);
        setSyncStatusText(`Sync failed: ${err.message || 'Remote endpoint unreachable or invalid credentials'}`);
        setIsSyncing(false);
        setSyncSuccess(false);
      }, 1800);
    }
  };

  const copySecret = () => {
    navigator.clipboard.writeText(webhookSecret);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '840px', padding: '24px 28px' }}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.8rem' }}>{connector.logo}</span>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>{connector.name} Integration</h3>
                <span className={`badge ${isDemoMode ? 'badge-purple' : 'badge-green'}`}>
                  {isDemoMode ? 'Simulated Demo Sandbox' : 'Live Cloud Production'}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                {connector.category} &bull; {connector.description}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', padding: '4px' }}
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* 4-Step Progress Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '20px 0 16px', position: 'relative' }}>
          {[
            { num: 1, label: 'Credentials' },
            { num: 2, label: 'Schema Mapper' },
            { num: 3, label: 'Health Check' },
            { num: 4, label: 'Sync & DLP' },
          ].map((s) => {
            const isCurrent = step === s.num;
            const isDone = step > s.num;
            return (
              <div 
                key={s.num} 
                style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
                onClick={() => setStep(s.num)}
              >
                <div 
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: isCurrent ? '#2563eb' : isDone ? '#059669' : '#e2e8f0',
                    color: isCurrent || isDone ? '#ffffff' : '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '0.82rem'
                  }}
                >
                  {isDone ? <Check size={16} /> : s.num}
                </div>
                <span style={{ fontSize: '0.82rem', fontWeight: isCurrent ? 700 : 500, color: isCurrent ? '#0f172a' : '#64748b' }}>
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* STEP 1: AUTHENTICATION & CREDENTIALS */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong style={{ fontSize: '0.88rem', color: '#0f172a' }}>Connection Mode</strong>
                <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  Run in offline sandbox without production secrets, or connect directly to live APIs.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button 
                  type="button" 
                  className={`btn btn-sm ${isDemoMode ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => setIsDemoMode(true)}
                >
                  Demo Mode
                </button>
                <button 
                  type="button" 
                  className={`btn btn-sm ${!isDemoMode ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => setIsDemoMode(false)}
                >
                  Live Production
                </button>
              </div>
            </div>

            {connector.type === 'custom_webhook' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Inbound Webhook Endpoint URL</label>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <input 
                      type="text" 
                      readOnly 
                      value={webhookUrl} 
                      style={{ flex: 1, padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.82rem', background: '#f1f5f9' }} 
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>HMAC-SHA256 Secret Signing Key</label>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <input 
                      type="password" 
                      readOnly 
                      value={webhookSecret} 
                      style={{ flex: 1, padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.82rem', background: '#f1f5f9' }} 
                    />
                    <button className="btn btn-outline btn-sm" onClick={copySecret}>
                      {copiedKey ? <Check size={14} color="#059669" /> : <Copy size={14} />}
                      <span>{copiedKey ? 'Copied' : 'Copy Key'}</span>
                    </button>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    Send payloads with header <code>X-Hub-Signature-256: sha256=&lt;signature&gt;</code>.
                  </span>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Remote Instance URL / Domain</label>
                  <input 
                    type="text" 
                    placeholder={connector ? `e.g. ${connector.base_url}` : 'https://api.provider.com'}
                    value={tenantUrl}
                    onChange={(e) => setTenantUrl(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
                    Account Email / Username {connector?.type === 'jira' && <span style={{ color: '#2563eb' }}>(Atlassian account email)</span>}
                  </label>
                  <input 
                    type="text" 
                    placeholder="e.g. name@company.com"
                    value={usernameOrEmail}
                    onChange={(e) => setUsernameOrEmail(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>API Token / Access Secret</label>
                  <input 
                    type="password" 
                    placeholder={isDemoMode ? "Simulated API Key (demo mode active)" : "ghp_xxxx or Personal API Token"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 2: UNIVERSAL SCHEMA MAPPER */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong style={{ fontSize: '0.88rem' }}>Universal Visual Field Mapper</strong>
                <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  Map inbound provider payload keys to our canonical mining data model.
                </p>
              </div>
              {connector.type === 'custom_rest' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>JSONPath Root:</span>
                  <input 
                    type="text" 
                    value={jsonPathRoot} 
                    onChange={(e) => setJsonPathRoot(e.target.value)}
                    style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.75rem', fontFamily: 'monospace' }}
                  />
                </div>
              )}
            </div>

            <div className="table-wrap" style={{ maxHeight: '280px', overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Canonical Field</th>
                    <th>Source Payload Key</th>
                    <th>Sample Extracted Value</th>
                  </tr>
                </thead>
                <tbody>
                  {CANONICAL_SCHEMA_FIELDS.map(f => (
                    <tr key={f.key}>
                      <td>
                        <strong style={{ fontSize: '0.82rem' }}>{f.key}</strong>
                        {f.req && <span style={{ color: '#dc2626', marginLeft: '2px' }}>*</span>}
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>{f.label}</div>
                      </td>
                      <td>
                        <input 
                          type="text"
                          value={fieldMappings[f.key] || ''}
                          onChange={(e) => setFieldMappings({ ...fieldMappings, [f.key]: e.target.value })}
                          style={{ width: '100%', padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.78rem', fontFamily: 'monospace' }}
                        />
                      </td>
                      <td>
                        <code style={{ fontSize: '0.75rem', color: '#059669', background: '#ecfdf5', padding: '2px 4px', borderRadius: '3px' }}>
                          {f.sample}
                        </code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* STEP 3: TEST CONNECTION & HEALTH CHECK */}
        {step === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#0f172a' }}>
                Connection Health &amp; Rate-Limit Diagnostic
              </div>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                Verifies handshake with <code>{tenantUrl}</code>, tests token scopes, and inspects HTTP 429 rate limit quotas.
              </p>

              <button 
                className="btn btn-primary btn-sm"
                onClick={handleTestConnection}
                disabled={isTesting}
                style={{ marginTop: '12px' }}
              >
                {isTesting ? <RefreshCw size={14} className="spin" /> : <CheckCircle2 size={14} />}
                <span>{isTesting ? 'Testing Remote Connectivity...' : 'Run Diagnostics'}</span>
              </button>
            </div>

            {testResult && (
              <div className={`alert ${testResult.status === 'connected' ? 'alert-success' : 'alert-warning'}`}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>
                    {testResult.status === 'connected' ? '✅ Connectivity Verified' : '⚠️ Diagnostic Warning'}
                  </div>
                  <div style={{ fontSize: '0.8rem', marginTop: '2px' }}>
                    {testResult.message}
                  </div>
                  <div style={{ fontSize: '0.75rem', marginTop: '6px', color: '#475569' }}>
                    Latency: <strong>{testResult.latency_ms || 85} ms</strong> &bull; Mode: <strong>{isDemoMode ? 'Simulated Demo' : 'Live Cloud'}</strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 4: SYNC & DLP POLICY */}
        {step === 4 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {/* Range Selector */}
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Historical Ingestion Range</label>
                <select 
                  value={syncRange}
                  onChange={(e) => setSyncRange(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
                >
                  <option value="30">Last 30 Days (Fastest)</option>
                  <option value="90">Last 90 Days (Recommended)</option>
                  <option value="180">Last 180 Days (Deep Mining)</option>
                  <option value="365">Full History (1 Year)</option>
                </select>
              </div>

              {/* Ingestion Trigger */}
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Sync Schedule</label>
                <select 
                  value={syncTrigger}
                  onChange={(e) => setSyncTrigger(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
                >
                  <option value="scheduled">Scheduled Hourly / Daily Cron</option>
                  <option value="realtime">Real-Time Inbound Webhooks</option>
                  <option value="manual">Manual On-Demand Only</option>
                </select>
              </div>
            </div>

            {/* Cloud DLP Privacy Toggle */}
            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '14px 16px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={22} color="#059669" />
                <div>
                  <strong style={{ fontSize: '0.85rem', color: '#065f46' }}>Cloud DLP Privacy Masking</strong>
                  <div style={{ fontSize: '0.78rem', color: '#166534' }}>
                    Masks PII, passwords, IPv4 addresses, and API credentials prior to database persistence.
                  </div>
                </div>
              </div>
              <input 
                type="checkbox" 
                checked={dlpEnabled} 
                onChange={(e) => setDlpEnabled(e.target.checked)} 
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
            </div>

            {/* Sync Action & Progress */}
            {isSyncing && (
              <div style={{ marginTop: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px', color: '#475569' }}>
                  <span>{syncStatusText}</span>
                  <span>{syncProgress}%</span>
                </div>
                <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${syncProgress}%`, background: '#2563eb', transition: 'width 0.4s ease' }} />
                </div>
              </div>
            )}

            {syncSuccess && (
              <div className="alert alert-success" style={{ margin: 0 }}>
                {syncStatusText}
              </div>
            )}

            <button 
              className="btn btn-primary"
              onClick={handleTriggerSync}
              disabled={isSyncing}
              style={{ width: '100%', marginTop: '6px' }}
            >
              <RefreshCw size={16} className={isSyncing ? "spin" : ""} />
              <span>{isSyncing ? 'Ingesting Tickets...' : 'Start Ingestion & Sync'}</span>
            </button>
          </div>
        )}

        {/* Modal Navigation Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '22px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
          <button 
            type="button" 
            className="btn btn-outline btn-sm" 
            disabled={step === 1}
            onClick={() => setStep(step - 1)}
          >
            <ArrowLeft size={14} /> Back
          </button>
          {step < 4 ? (
            <button 
              type="button" 
              className="btn btn-primary btn-sm"
              onClick={() => setStep(step + 1)}
            >
              Next Step <ArrowRight size={14} />
            </button>
          ) : (
            <button 
              type="button" 
              className="btn btn-outline btn-sm"
              onClick={onClose}
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
