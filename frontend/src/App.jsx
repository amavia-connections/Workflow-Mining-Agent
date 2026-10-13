import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  Workflow, 
  Cpu, 
  CheckCircle, 
  Settings, 
  Layers, 
  ShieldAlert, 
  RefreshCw,
  Server
} from 'lucide-react';

import OverviewView from './views/OverviewView';
import TicketExplorerView from './views/TicketExplorerView';
import WorkflowOpportunitiesView from './views/WorkflowOpportunitiesView';
import AutomationStudioView from './views/AutomationStudioView';
import EvaluationCenterView from './views/EvaluationCenterView';
import ConfigView from './views/ConfigView';
import DocDrawer from './components/DocDrawer';
import { BookOpen, UserCheck, Building2, X as CloseIcon } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [summary, setSummary] = useState(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(null);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [analysisStatusText, setAnalysisStatusText] = useState('');
  
  // Enterprise RBAC Persona state
  const [currentRole, setCurrentRole] = useState('Governance Approver');

  // Enterprise Multi-Tenant state
  const [tenants, setTenants] = useState([]);
  const [activeTenant, setActiveTenant] = useState(null);
  
  // In-App Guided UX & Documentation Drawer state
  const [isDocOpen, setIsDocOpen] = useState(false);
  const [showQuickstart, setShowQuickstart] = useState(true);

  const fetchSummary = async () => {
    try {
      const res = await fetch('/api/dashboard/summary');
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard summary:', err);
    }
  };

  const fetchTenants = async () => {
    try {
      const res = await fetch('/api/tenants');
      if (res.ok) {
        const data = await res.json();
        setTenants(data.tenants || []);
        setActiveTenant(data.active_tenant || null);
      }
    } catch (err) {
      console.error('Failed to fetch tenants:', err);
    }
  };

  const handleTenantChange = async (tenantId) => {
    try {
      setIsRunningAnalysis(true);
      setAnalysisStatusText('Switching tenant organization context...');
      const res = await fetch('/api/tenants/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId })
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveTenant(updated);
        setSelectedWorkflowId(null);
        await fetchSummary();
      }
    } catch (err) {
      console.error('Failed to switch tenant context:', err);
    } finally {
      setIsRunningAnalysis(false);
      setAnalysisStatusText('');
    }
  };

  useEffect(() => {
    fetchSummary();
    fetchTenants();
  }, []);

  const handleRunAnalysis = async (hourlyRate = 65.0, automatablePct = 0.75) => {
    setIsRunningAnalysis(true);
    setAnalysisStatusText('Triggering workflow analysis pipeline...');
    try {
      const res = await fetch('/api/analysis/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_name: 'IT Service Tickets',
          hourly_labor_rate: Number(hourlyRate),
          automatable_percentage: Number(automatablePct),
          n_clusters: 6
        })
      });
      const data = await res.json();
      const runId = data.run_id;

      // Poll until completed
      const pollInterval = setInterval(async () => {
        try {
          const pollRes = await fetch(`/api/analysis/${runId}`);
          const pollData = await pollRes.json();
          setAnalysisStatusText(pollData.message || 'Processing...');
          if (pollData.status === 'COMPLETED' || pollData.status === 'FAILED') {
            clearInterval(pollInterval);
            setIsRunningAnalysis(false);
            setAnalysisStatusText('');
            await fetchSummary();
            setActiveTab('overview');
          }
        } catch (e) {
          clearInterval(pollInterval);
          setIsRunningAnalysis(false);
        }
      }, 1500);
    } catch (err) {
      console.error('Failed to start analysis run:', err);
      setIsRunningAnalysis(false);
      setAnalysisStatusText('');
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-title">
            <Workflow size={22} color="#2563eb" />
            <span>Workflow Mining</span>
          </div>
          <div style={{ marginTop: '6px', display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span className="brand-badge">AI Builder Cup 2026</span>
            <span className="badge badge-gray" style={{ fontSize: '0.65rem' }}>v1.0</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard size={18} />
            <span>Overview</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'tickets' ? 'active' : ''}`}
            onClick={() => setActiveTab('tickets')}
          >
            <Search size={18} />
            <span>Ticket Explorer</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'workflows' ? 'active' : ''}`}
            onClick={() => { setSelectedWorkflowId(null); setActiveTab('workflows'); }}
          >
            <Workflow size={18} />
            <span>Workflow Opportunities</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'studio' ? 'active' : ''}`}
            onClick={() => { setSelectedWorkflowId(null); setActiveTab('studio'); }}
          >
            <Cpu size={18} />
            <span>Automation Studio</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'evaluation' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluation')}
          >
            <CheckCircle size={18} />
            <span>Evaluation Center</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            <Settings size={18} />
            <span>Data &amp; Config</span>
          </button>
        </nav>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#059669' }} />
            <span>Agent Active &bull; Human in the Loop</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
            Never executes automations automatically
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Top Header Bar */}
        <header className="top-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', textTransform: 'capitalize' }}>
              {activeTab === 'overview' && 'Executive Overview'}
              {activeTab === 'tickets' && 'Service Ticket Explorer'}
              {activeTab === 'workflows' && 'Workflow Opportunities & Ranking'}
              {activeTab === 'studio' && 'Automation Studio (Google ADK)'}
              {activeTab === 'evaluation' && 'Evaluation & Ground-Truth Center'}
              {activeTab === 'config' && 'Enterprise Connectors & Governance'}
            </h1>
            {isRunningAnalysis && (
              <span className="badge badge-amber" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RefreshCw size={12} className="spin" /> {analysisStatusText}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Enterprise Tenant Context Switcher */}
            <div className="persona-switcher" title="Active Enterprise Tenant context isolates ticket logs, cluster metrics, and workflow models">
              <Building2 size={14} color="#059669" />
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Tenant:</span>
              <select 
                className="persona-select"
                value={activeTenant?.tenant_id || ''}
                onChange={(e) => handleTenantChange(e.target.value)}
              >
                {tenants.map(t => (
                  <option key={t.tenant_id} value={t.tenant_id}>
                    {t.name} ({t.tier || 'Enterprise'})
                  </option>
                ))}
              </select>
            </div>

            {/* Enterprise Role Persona Switcher */}
            <div className="persona-switcher" title="Active Role persona enforces permissions across the SaaS platform">
              <UserCheck size={14} color="#2563eb" />
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Role:</span>
              <select 
                className="persona-select"
                value={currentRole}
                onChange={(e) => setCurrentRole(e.target.value)}
              >
                <option value="Admin">Admin (Full Control)</option>
                <option value="ITSM / DevOps Analyst">ITSM / DevOps Analyst</option>
                <option value="Governance Approver">Governance Approver</option>
                <option value="Executive / Viewer">Executive / Viewer (Read-Only)</option>
              </select>
            </div>

            {/* Contextual Documentation Drawer Toggle */}
            <button 
              className="btn btn-outline btn-sm"
              onClick={() => setIsDocOpen(true)}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Open documentation and architectural guide"
            >
              <BookOpen size={14} color="#2563eb" />
              <span>Guide &amp; Docs</span>
            </button>

            <button 
              className="btn btn-outline btn-sm"
              onClick={fetchSummary}
              title="Refresh Metrics"
            >
              <RefreshCw size={14} /> Refresh
            </button>
            <button 
              className="btn btn-primary btn-sm"
              disabled={isRunningAnalysis}
              onClick={() => handleRunAnalysis(65.0, 0.75)}
            >
              Run Mining Agent
            </button>
          </div>
        </header>

        {/* Dismissible Quickstart Product Tour Bar */}
        {showQuickstart && (
          <div className="quickstart-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase', fontSize: '0.75rem', color: '#60a5fa' }}>
                Quickstart Tour:
              </span>
              <div className="quickstart-steps">
                <div 
                  className={`quickstart-step ${activeTab === 'config' ? 'active' : ''}`}
                  onClick={() => setActiveTab('config')}
                >
                  <span>1. Ingest Tickets</span>
                </div>
                <span style={{ color: '#64748b' }}>&rarr;</span>
                <div 
                  className={`quickstart-step ${activeTab === 'workflows' ? 'active' : ''}`}
                  onClick={() => setActiveTab('workflows')}
                >
                  <span>2. Review Discovered Workflows</span>
                </div>
                <span style={{ color: '#64748b' }}>&rarr;</span>
                <div 
                  className={`quickstart-step ${activeTab === 'studio' ? 'active' : ''}`}
                  onClick={() => setActiveTab('studio')}
                >
                  <span>3. Inspect Grounded Spec</span>
                </div>
                <span style={{ color: '#64748b' }}>&rarr;</span>
                <div 
                  className={`quickstart-step ${activeTab === 'studio' ? 'active' : ''}`}
                  onClick={() => setActiveTab('studio')}
                >
                  <span>4. Record Human Approval</span>
                </div>
                <span style={{ color: '#64748b' }}>&rarr;</span>
                <div 
                  className={`quickstart-step ${activeTab === 'studio' ? 'active' : ''}`}
                  onClick={() => setActiveTab('studio')}
                >
                  <span>5. Export Runbook</span>
                </div>
              </div>
            </div>
            <button 
              onClick={() => setShowQuickstart(false)}
              style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#94a3b8', padding: '2px' }}
              title="Dismiss Quickstart Tour"
              aria-label="Dismiss Quickstart Tour"
            >
              <CloseIcon size={14} />
            </button>
          </div>
        )}

        {/* Active Page View */}
        <div className="page-container">
          {activeTab === 'overview' && (
            <OverviewView 
              key={activeTenant?.tenant_id}
              summary={summary}
              onNavigateToWorkflow={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('workflows');
              }}
              onNavigateToStudio={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('studio');
              }}
              onOpenDoc={() => setIsDocOpen(true)}
            />
          )}

          {activeTab === 'tickets' && (
            <TicketExplorerView 
              key={activeTenant?.tenant_id}
              onNavigateToWorkflow={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('workflows');
              }}
            />
          )}

          {activeTab === 'workflows' && (
            <WorkflowOpportunitiesView 
              key={activeTenant?.tenant_id}
              initialWorkflowId={selectedWorkflowId}
              onNavigateToStudio={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('studio');
              }}
            />
          )}

          {activeTab === 'studio' && (
            <AutomationStudioView 
              key={activeTenant?.tenant_id}
              workflowId={selectedWorkflowId}
              currentRole={currentRole}
            />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationCenterView 
              key={activeTenant?.tenant_id}
              runId={summary?.active_run_id}
            />
          )}

          {activeTab === 'config' && (
            <ConfigView 
              key={activeTenant?.tenant_id}
              onRunAnalysis={handleRunAnalysis}
              isRunningAnalysis={isRunningAnalysis}
              currentRole={currentRole}
            />
          )}
        </div>
      </main>

      {/* Contextual In-App Documentation Drawer */}
      <DocDrawer 
        isOpen={isDocOpen} 
        onClose={() => setIsDocOpen(false)} 
        activeView={activeTab} 
      />
    </div>
  );
}
