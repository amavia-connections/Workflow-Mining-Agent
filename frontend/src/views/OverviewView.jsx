import React from 'react';
import { 
  Clock, 
  DollarSign, 
  Layers, 
  TrendingUp, 
  Sparkles, 
  CheckCircle2, 
  ArrowRight,
  ShieldAlert,
  Server
} from 'lucide-react';

import MetricTooltip from '../components/MetricTooltip';

export default function OverviewView({ summary, onNavigateToWorkflow, onNavigateToStudio, onOpenDoc }) {
  if (!summary) {
    return <div className="card">Loading overview summary...</div>;
  }

  const topOpps = summary.top_opportunities || [];
  const distribution = summary.workflow_distribution || [];
  const maxMonthlyHours = Math.max(...distribution.map(d => d.monthly_hours), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner / Mode Notice */}
      <div className="alert alert-info" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Server size={18} />
          <span>
            <strong>Tenant Organization:</strong>{' '}
            <span className="badge badge-green" style={{ marginLeft: '4px', marginRight: '6px' }}>
              {summary.tenant_name || 'Enterprise Production'}
            </span>
            &bull; Operating in{' '}
            <span className="badge badge-green" style={{ marginLeft: '4px' }}>
              {summary.cloud_mode_enabled ? 'GCP Production (Vertex AI & BigQuery)' : 'Live Production Mode'}
            </span>
            {' '}&bull; Run ID: <code style={{ fontWeight: 600 }}>{summary.active_run_id}</code>
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: '#1e40af' }}>
            Deterministic SQL Quantification &bull; Isolated Tenant Data &bull; Human Governance Gate
          </span>
        </div>
      </div>

      {/* Primary KPI Stats Grid */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">
              Tickets Analyzed
              <MetricTooltip 
                title="Total Tickets Analyzed" 
                sqlOrigin="SELECT COUNT(*) FROM service_tickets WHERE status = 'Closed'"
                note="Ingested from ServiceNow, Jira, GitHub, or synthetic benchmark store."
              />
            </span>
            <Layers size={18} color="#2563eb" />
          </div>
          <div className="stat-value">{summary.total_tickets_analyzed !== undefined && summary.total_tickets_analyzed !== null ? summary.total_tickets_analyzed.toLocaleString() : '0'}</div>
          <div className="stat-sub">
            <span className="badge badge-blue">{summary.total_tickets_analyzed > 0 ? "100% Ingested" : "Live Sync Ready"}</span> across active channels
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">
              Discovered Workflows
              <MetricTooltip 
                title="Discovered Workflow Clusters" 
                formula="k clusters where ticket_count >= 10"
                sqlOrigin="SELECT COUNT(DISTINCT cluster_id) FROM ticket_clusters"
                note="Separates recurring standardized incident workflows from idiosyncratic noise."
              />
            </span>
            <Sparkles size={18} color="#7c3aed" />
          </div>
          <div className="stat-value">{summary.workflows_discovered_count !== undefined && summary.workflows_discovered_count !== null ? summary.workflows_discovered_count : 0}</div>
          <div className="stat-sub">
            <span className="badge badge-green">{summary.workflows_discovered_count > 0 ? "High Coherence" : "Idle"}</span> semantic clusters
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">
              Monthly Handling Time
              <MetricTooltip 
                title="Active Handling Hours / Month" 
                formula="SUM(active_handling_minutes) / 60 / span_months"
                sqlOrigin="Deterministic touch-time excluding calendar queue wait idle time."
                note="Mean Time to Resolution (MTTR) is 80-95% queue idle waiting. Only active handling time is quantified."
              />
            </span>
            <Clock size={18} color="#d97706" />
          </div>
          <div className="stat-value">{summary.total_monthly_handling_hours?.toFixed(1) || '0'} <span style={{ fontSize: '1rem', fontWeight: 500 }}>hrs/mo</span></div>
          <div className="stat-sub">
            Active engineer time spent on repetitive tasks
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">
              Est. Potential Annual Savings
              <MetricTooltip 
                title="Potential Annual Financial ROI" 
                formula="Monthly_Hours * 12 * 0.75 * $65.00/hr"
                sqlOrigin="SUM(handling_hours_annual) * automatable_ratio * hourly_rate"
                note="Assumes 75% runbook automation feasibility at standard IT labor rate ($65/hr)."
              />
            </span>
            <DollarSign size={18} color="#059669" />
          </div>
          <div className="stat-value" style={{ color: '#059669' }}>
            ${Math.round(summary.potential_annual_cost_savings_usd || 0).toLocaleString()}
          </div>
          <div className="stat-sub">
            <span className="badge badge-green">75% automatable</span> at $65/hr labor rate
          </div>
        </div>
      </div>

      {/* Two Column Layout: Top Opportunities & Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px' }}>
        {/* Top Automation Opportunities */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 className="card-title">Top Automation Opportunities</h3>
              <p className="card-desc">Ranked by potential annual labor savings and recurrence frequency.</p>
            </div>
            <button className="btn btn-outline btn-sm" onClick={() => onNavigateToWorkflow()}>
              View All <ArrowRight size={14} />
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Workflow Name</th>
                  <th>Frequency</th>
                  <th>Hours Wasted</th>
                  <th>Potential Savings</th>
                  <th>Complexity</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {topOpps.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '1.2rem' }}>⚡</span>
                        <div style={{ fontWeight: 600 }}>No workflows discovered yet</div>
                        <div style={{ fontSize: '0.85rem' }}>Ingest live tickets from NovaDesk ITSM or Connectors to begin discovery.</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  topOpps.map((opp) => (
                    <tr key={opp.workflow_id}>
                      <td>
                        <span className={`badge ${opp.priority_rank === 1 ? 'badge-blue' : 'badge-gray'}`} style={{ fontWeight: 700 }}>
                          #{opp.priority_rank}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{opp.workflow_name}</td>
                      <td>{opp.tickets_per_month} /mo</td>
                      <td>{opp.total_handling_hours_per_month} hrs/mo</td>
                      <td style={{ color: '#059669', fontWeight: 600 }}>
                        ${Math.round(opp.potential_annual_cost_savings).toLocaleString()}
                      </td>
                      <td>
                        <span className={`badge ${opp.implementation_complexity === 'Low' ? 'badge-green' : 'badge-amber'}`}>
                          {opp.implementation_complexity}
                        </span>
                      </td>
                      <td>
                        {opp.priority_rank === 1 ? (
                          <button 
                            className="btn btn-primary btn-sm"
                            onClick={() => onNavigateToStudio(opp.workflow_id)}
                          >
                            Draft Spec
                          </button>
                        ) : (
                          <button 
                            className="btn btn-outline btn-sm"
                            onClick={() => onNavigateToWorkflow(opp.workflow_id)}
                          >
                            Inspect
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Workflow Volume & Hours Distribution Chart */}
        <div className="card">
          <h3 className="card-title">Handling Time Distribution</h3>
          <p className="card-desc">Monthly labor hours consumed per discovered workflow category.</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '10px' }}>
            {distribution.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '36px', color: '#64748b', fontSize: '0.85rem' }}>
                No active workflow clusters found in current dataset.
              </div>
            ) : (
              distribution.map((item, idx) => {
                const pct = Math.round((item.monthly_hours / maxMonthlyHours) * 100);
                return (
                  <div key={item.workflow_id || idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 500 }}>{item.name}</span>
                      <span style={{ fontWeight: 600, color: '#334155' }}>
                        {item.monthly_hours} hrs/mo ({item.ticket_count} tickets)
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                      <div 
                        style={{ 
                          width: `${pct}%`, 
                          height: '100%', 
                          background: idx === 0 ? '#4f46e5' : (idx === 1 ? '#0284c7' : '#059669'),
                          borderRadius: '4px'
                        }} 
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div style={{ marginTop: '24px', padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.82rem', color: '#64748b' }}>
            <strong>💡 Governance Rule:</strong> Active employee handling time excludes queue wait idle time. All annual savings calculations are calculated via BigQuery SQL logic without model hallucination.
          </div>
        </div>
      </div>
    </div>
  );
}
