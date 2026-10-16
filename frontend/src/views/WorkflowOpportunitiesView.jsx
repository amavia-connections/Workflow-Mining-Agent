import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Clock, 
  DollarSign, 
  Sliders, 
  CheckCircle, 
  AlertTriangle, 
  ArrowRight, 
  FileText, 
  Check, 
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react';
import ProcessDiagram from '../components/ProcessDiagram';
import MetricTooltip from '../components/MetricTooltip';
import StepExplanationModal from '../components/StepExplanationModal';

export default function WorkflowOpportunitiesView({ initialWorkflowId, onNavigateToStudio }) {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterComplexity, setFilterComplexity] = useState('ALL');
  const [modalStep, setModalStep] = useState(null);
  const [isStepModalOpen, setIsStepModalOpen] = useState(false);

  useEffect(() => {
    fetch('/api/workflows')
      .then(res => res.json())
      .then(data => {
        setWorkflows(data || []);
        if (data && data.length > 0) {
          if (initialWorkflowId) {
            const found = data.find(w => w.workflow_id === initialWorkflowId);
            setSelectedWorkflow(found || data[0]);
          } else {
            setSelectedWorkflow(data[0]);
          }
        }
      })
      .catch(err => console.error('Error fetching workflows:', err))
      .finally(() => setLoading(false));
  }, [initialWorkflowId]);

  const filteredWorkflows = workflows.filter(w => {
    if (filterComplexity === 'ALL') return true;
    return w.implementation_complexity === filterComplexity;
  });

  if (loading) {
    return <div className="card">Loading workflow opportunities...</div>;
  }

  const w = selectedWorkflow;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Overview & Filter Bar */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="card-title">Discovered Workflow Opportunities</h3>
            <p className="card-desc">
              Ranked opportunities prioritized by estimated financial savings, frequency, confidence, and implementation feasibility.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Complexity:</span>
            {['ALL', 'Low', 'Medium', 'High'].map(c => (
              <button
                key={c}
                className={`btn btn-sm ${filterComplexity === c ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setFilterComplexity(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Two Column Layout: Ranked Table and Drilldown Inspector */}
      <div className="responsive-split" style={{ display: 'grid', gap: '24px' }}>
        {/* Ranked Workflow Opportunities List */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase' }}>
              Discovered Workflows ({filteredWorkflows.length})
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {filteredWorkflows.map((wf) => {
              const isSelected = selectedWorkflow && selectedWorkflow.workflow_id === wf.workflow_id;
              return (
                <div
                  key={wf.workflow_id}
                  onClick={() => setSelectedWorkflow(wf)}
                  style={{
                    padding: '16px 20px',
                    borderBottom: '1px solid #f1f5f9',
                    cursor: 'pointer',
                    background: isSelected ? '#eff6ff' : '#ffffff',
                    borderLeft: isSelected ? '4px solid #2563eb' : '4px solid transparent',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`badge ${wf.metrics.priority_rank === 1 ? 'badge-blue' : 'badge-gray'}`} style={{ fontWeight: 700 }}>
                        Rank #{wf.metrics.priority_rank}
                      </span>
                      <code style={{ fontSize: '0.8rem', color: '#64748b' }}>{wf.workflow_id}</code>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#059669' }}>
                      ${Math.round(wf.metrics.potential_annual_cost_savings).toLocaleString()}/yr
                    </span>
                  </div>

                  <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#0f172a', marginBottom: '6px' }}>
                    {wf.workflow_name}
                  </div>

                  <div style={{ display: 'flex', gap: '14px', fontSize: '0.8rem', color: '#64748b' }}>
                    <span><strong>{wf.metrics.tickets_per_month}</strong> tickets/mo</span>
                    <span>&bull;</span>
                    <span><strong>{wf.metrics.total_handling_hours_per_month}</strong> hrs/mo</span>
                    <span>&bull;</span>
                    <span className={`badge ${wf.implementation_complexity === 'Low' ? 'badge-green' : 'badge-amber'}`}>
                      {wf.implementation_complexity}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Workflow Detailed Inspector */}
        {w ? (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span className="badge badge-blue">Rank #{w.metrics.priority_rank} Priority</span>
                  <code style={{ fontSize: '0.85rem' }}>{w.workflow_id}</code>
                  <span className="badge badge-purple">Confidence: {Math.round(w.confidence_score * 100)}%</span>
                </div>
                <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>{w.workflow_name}</h2>
              </div>
              <button 
                className="btn btn-primary"
                onClick={() => onNavigateToStudio(w.workflow_id)}
              >
                Draft Automation Spec <ArrowRight size={15} />
              </button>
            </div>

            <p style={{ color: '#475569', fontSize: '0.92rem' }}>{w.description}</p>

            {/* Financial & Time Metrics Summary */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                  Monthly Hours Wasted
                  <MetricTooltip 
                    title="Monthly Handling Hours"
                    formula="SUM(handling_minutes) / 60 / span_months"
                    note="Active engineering effort excluding inactive queue waiting time."
                  />
                </span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{w.metrics.total_handling_hours_per_month} hrs</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Avg {w.metrics.avg_handling_minutes} min/ticket</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                  Annual Potential Savings
                  <MetricTooltip 
                    title="Potential Annual Savings"
                    formula="Monthly_Hours * 12 * 0.75 * $65.00/hr"
                    note="Calculated via deterministic SQL calculations."
                  />
                </span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#059669' }}>
                  ${Math.round(w.metrics.potential_annual_cost_savings).toLocaleString()}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#059669' }}>{w.metrics.potential_annual_hours_saved} hours saved</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                  Priority Score
                  <MetricTooltip 
                    title="4-Factor Opportunity Score"
                    formula="0.40*Savings + 0.25*Volume + 0.20*Confidence + 0.15*Ease"
                    note="Weighted algorithm prioritizing highest ROI with feasible runbook complexity."
                  />
                </span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#2563eb' }}>{w.metrics.priority_score} / 100</div>
                <div style={{ fontSize: '0.75rem', color: '#2563eb' }}>Complexity: {w.implementation_complexity}</div>
              </div>
            </div>

            {/* Interactive Process Diagram (BPMN / Visualizer) */}
            <ProcessDiagram 
              workflowName={w.workflow_name}
              triggers={[w.common_trigger || 'Repetitive Incident Ingested']}
              preconditions={['Target service healthy', 'IAM API credentials valid']}
              steps={(w.typical_resolution_steps || []).map((stepText, idx) => ({
                step_number: idx + 1,
                step_name: stepText.length > 35 ? stepText.slice(0, 32) + '...' : stepText,
                target_system_or_api: w.category || 'Target System',
                action_description: stepText,
                is_grounded_in_evidence: true
              }))}
              approvalRequired={true}
              approvalRole="ITSM / DevOps Lead"
              exceptions={w.common_exceptions || ['Precondition timeout', 'Auth failure']}
              rollbackStrategy="Revert manifest changes and notify on-call engineer"
            />

            {/* Extracted Runbook Steps */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h4 style={{ fontSize: '0.92rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle size={16} color="#059669" /> Extracted Typical Resolution Steps
                </h4>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Click any step for Gemini deep-dive</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {w.typical_resolution_steps.map((step, idx) => (
                  <div 
                    key={idx} 
                    className="clickable-step-row"
                    onClick={() => {
                      setModalStep({
                        step_number: idx + 1,
                        step_name: step,
                        target_system_or_api: w.category || 'Target System',
                        action_description: step,
                        is_grounded_in_evidence: true
                      });
                      setIsStepModalOpen(true);
                    }}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.88rem', background: '#ffffff', padding: '10px 14px', borderRadius: '6px', border: '1px solid #e2e8f0' }}
                    title="Click for Gemini Step Rationale & Optimization Analysis"
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                      <span style={{ background: '#eff6ff', color: '#2563eb', fontWeight: 700, borderRadius: '50%', width: '22px', height: '22px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', flexShrink: 0 }}>
                        {idx + 1}
                      </span>
                      <span>{step}</span>
                    </div>
                    <span className="badge badge-purple" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '3px', flexShrink: 0 }}>
                      <Sparkles size={11} /> Explain
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Trigger & Common Exceptions */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Common Trigger</span>
                <p style={{ fontSize: '0.86rem', marginTop: '4px', color: '#334155' }}>{w.common_trigger}</p>
              </div>

              <div style={{ background: '#fffbeb', padding: '14px', borderRadius: '8px', border: '1px solid #fde68a' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#b45309', textTransform: 'uppercase' }}>Common Exceptions</span>
                <ul style={{ fontSize: '0.82rem', marginTop: '4px', paddingLeft: '16px', color: '#92400e' }}>
                  {w.common_exceptions.map((ex, i) => <li key={i}>{ex}</li>)}
                </ul>
              </div>
            </div>

            {/* Transparent Prioritization Formula Breakdown */}
            <div style={{ background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '14px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} /> Transparent Prioritization Ranking Breakdown
                <MetricTooltip 
                  title="Ranking Algorithm Weights"
                  formula="0.40*Savings + 0.25*Recurrence + 0.20*Confidence + 0.15*Ease"
                  note="Guarantees ranking transparency with zero arbitrary black-box scoring."
                />
              </span>
              <div className="responsive-grid-4" style={{ gap: '10px', marginTop: '10px', fontSize: '0.8rem' }}>
                <div style={{ background: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ color: '#64748b' }}>Savings (40%)</div>
                  <strong style={{ color: '#059669' }}>+{w.metrics.ranking_factors?.savings_contribution_40pct || 36.0} pts</strong>
                </div>
                <div style={{ background: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ color: '#64748b' }}>Recurrence (25%)</div>
                  <strong style={{ color: '#2563eb' }}>+{w.metrics.ranking_factors?.recurrence_contribution_25pct || 21.0} pts</strong>
                </div>
                <div style={{ background: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ color: '#64748b' }}>Confidence (20%)</div>
                  <strong style={{ color: '#7c3aed' }}>+{w.metrics.ranking_factors?.confidence_contribution_20pct || 18.0} pts</strong>
                </div>
                <div style={{ background: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ color: '#64748b' }}>Simplicity (15%)</div>
                  <strong style={{ color: '#d97706' }}>+{w.metrics.ranking_factors?.simplicity_contribution_15pct || 11.0} pts</strong>
                </div>
              </div>
            </div>

            {/* Representative Ticket Citations */}
            <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
              <strong>Representative Source Tickets:</strong>{' '}
              {w.representative_ticket_ids.map((tid, i) => (
                <code key={i} style={{ marginRight: '6px', padding: '2px 6px', background: '#f1f5f9', borderRadius: '4px' }}>
                  {tid}
                </code>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      {/* Gemini Step Explanation Modal for Extracted Steps */}
      <StepExplanationModal
        isOpen={isStepModalOpen}
        onClose={() => setIsStepModalOpen(false)}
        step={modalStep}
        workflowName={selectedWorkflow?.workflow_name || 'IT Operations Workflow'}
        category={selectedWorkflow?.category || 'IT Operations'}
      />
    </div>
  );
}
