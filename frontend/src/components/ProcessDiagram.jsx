import React, { useState } from 'react';
import { 
  Zap, 
  ShieldCheck, 
  ArrowRight, 
  UserCheck, 
  AlertTriangle, 
  RotateCcw, 
  CheckCircle2, 
  Layers, 
  ChevronRight,
  GitBranch,
  Info,
  Sparkles
} from 'lucide-react';
import StepExplanationModal from './StepExplanationModal';

/**
 * Interactive BPMN / Process Flow Diagram
 * Visualizes Trigger Event -> Preconditions -> Sequential Steps -> Human Approval -> Happy vs Exception Paths -> Rollback.
 */
export default function ProcessDiagram({ 
  workflowName = 'Remediation Workflow',
  category = 'Target System',
  triggers = ['System alert or incident webhook received'],
  preconditions = ['Target service reachable & credentials valid'],
  steps = [],
  approvalRequired = true,
  approvalRole = 'DevOps / SRE Lead',
  exceptions = ['API rate limit exceeded', 'Precondition assertion failed'],
  rollbackStrategy = 'Purge temporary cache and revert to previous configuration manifest',
  onStepClick = null
}) {
  const [activePathView, setActivePathView] = useState('ALL'); // 'ALL', 'HAPPY', 'EXCEPTION'
  const [selectedStepForModal, setSelectedStepForModal] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Default fallback steps if none passed
  const displaySteps = steps && steps.length > 0 ? steps : [
    { step_number: 1, step_name: 'Inspect System Crash Logs', target_system_or_api: 'Observability API', action_description: 'Extract recent error traces and exit codes.', is_grounded_in_evidence: true },
    { step_number: 2, step_name: 'Execute Target Remediation', target_system_or_api: 'Platform Engine', action_description: 'Adjust resource limits or restart deadlocked worker pool.', is_grounded_in_evidence: true },
    { step_number: 3, step_name: 'Verify Post-Remediation Health', target_system_or_api: 'Health Check API', action_description: 'Poll /healthz for 60 seconds with zero 5xx errors.', is_grounded_in_evidence: true }
  ];

  const isHappy = activePathView === 'HAPPY' || activePathView === 'ALL';
  const isException = activePathView === 'EXCEPTION' || activePathView === 'ALL';

  return (
    <div className="process-diagram-wrap">
      {/* Diagram Header & Toggle Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-purple" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <GitBranch size={12} /> BPMN / Process Visualizer
            </span>
            <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{workflowName}</strong>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
            Visual process orchestration graph showing Happy Path (80% frequency) vs Exception &amp; Rollback paths
          </div>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          <button 
            type="button"
            className={`btn btn-sm ${activePathView === 'ALL' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActivePathView('ALL')}
            style={{ fontSize: '0.75rem', padding: '4px 10px' }}
          >
            All Paths
          </button>
          <button 
            type="button"
            className={`btn btn-sm ${activePathView === 'HAPPY' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActivePathView('HAPPY')}
            style={{ fontSize: '0.75rem', padding: '4px 10px', color: activePathView === 'HAPPY' ? '#ffffff' : '#047857' }}
          >
            Happy Path (~80%)
          </button>
          <button 
            type="button"
            className={`btn btn-sm ${activePathView === 'EXCEPTION' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActivePathView('EXCEPTION')}
            style={{ fontSize: '0.75rem', padding: '4px 10px', color: activePathView === 'EXCEPTION' ? '#ffffff' : '#b91c1c' }}
          >
            Exceptions &amp; Rollback
          </button>
        </div>
      </div>

      {/* Main Process Diagram Flow Canvas */}
      <div className="flow-canvas">
        {/* Row 1: The Main Flow Sequence (Happy Path) */}
        <div className={`flow-sequence ${isHappy ? 'highlight-happy' : 'dimmed'}`}>
          {/* Node 1: Trigger Event */}
          <div className="flow-node trigger-node">
            <div className="node-icon-bubble" style={{ background: '#fef3c7', color: '#d97706' }}>
              <Zap size={16} />
            </div>
            <div className="node-header">Trigger Event</div>
            <div className="node-title">{triggers[0] || 'Incident Ingested'}</div>
            <div className="node-sub">Inbound Webhook / Alert</div>
          </div>

          <div className="flow-connector">
            <ArrowRight size={18} color="#94a3b8" />
          </div>

          {/* Node 2: Preconditions Check */}
          <div className="flow-node precondition-node">
            <div className="node-icon-bubble" style={{ background: '#eff6ff', color: '#2563eb' }}>
              <ShieldCheck size={16} />
            </div>
            <div className="node-header">Safety Gate</div>
            <div className="node-title">Verify Preconditions</div>
            <div className="node-sub">{preconditions[0] || 'Assert Environment Ready'}</div>
          </div>

          <div className="flow-connector">
            <ArrowRight size={18} color="#94a3b8" />
          </div>

          {/* Nodes 3..N: Sequential Action Steps */}
          {displaySteps.map((s, idx) => (
            <React.Fragment key={s.step_number || idx}>
              <div 
                className="flow-node step-node"
                onClick={() => {
                  setSelectedStepForModal(s);
                  setIsModalOpen(true);
                  if (onStepClick) onStepClick(s);
                }}
                title="Click for Gemini Step Rationale & Optimization Analysis"
              >
                <div className="node-icon-bubble" style={{ background: s.is_grounded_in_evidence ? '#ecfdf5' : '#f5f3ff', color: s.is_grounded_in_evidence ? '#059669' : '#7c3aed' }}>
                  <Layers size={15} />
                </div>
                <div className="node-header">
                  <span>Step {s.step_number || idx + 1}</span>
                  {s.is_grounded_in_evidence ? (
                    <span className="badge badge-green" style={{ fontSize: '0.62rem', padding: '1px 4px' }}>Grounded</span>
                  ) : (
                    <span className="badge badge-purple" style={{ fontSize: '0.62rem', padding: '1px 4px' }}>Best Practice</span>
                  )}
                </div>
                <div className="node-title">{s.step_name}</div>
                <div className="node-sub"><code>{s.target_system_or_api}</code></div>
                
                <div className="step-ai-pill">
                  <Sparkles size={10} /> Gemini Deep-Dive
                </div>
              </div>

              <div className="flow-connector">
                <ArrowRight size={18} color="#94a3b8" />
              </div>
            </React.Fragment>
          ))}

          {/* Node: Human Approval Gate (if required) */}
          {approvalRequired && (
            <>
              <div className="flow-node approval-node">
                <div className="node-icon-bubble" style={{ background: '#fef2f2', color: '#dc2626' }}>
                  <UserCheck size={16} />
                </div>
                <div className="node-header">Governance Boundary</div>
                <div className="node-title">Human Approval Gate</div>
                <div className="node-sub">Role: {approvalRole}</div>
              </div>

              <div className="flow-connector">
                <ArrowRight size={18} color="#059669" />
              </div>
            </>
          )}

          {/* Final Node: Success Resolution */}
          <div className="flow-node success-node">
            <div className="node-icon-bubble" style={{ background: '#ecfdf5', color: '#059669' }}>
              <CheckCircle2 size={16} />
            </div>
            <div className="node-header" style={{ color: '#047857' }}>Primary Outcome</div>
            <div className="node-title" style={{ color: '#065f46' }}>Incident Resolved</div>
            <div className="node-sub">Happy Path Complete</div>
          </div>
        </div>

        {/* Row 2: Exception Branch & Rollback Recovery (Dashed Loop) */}
        {isException && (
          <div className="flow-branch-row">
            <div className="branch-label">
              <span className="badge badge-amber" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <AlertTriangle size={12} /> Exception Branch
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>If precondition fails, API times out, or auth rejected</span>
            </div>

            <div className="branch-sequence">
              <div className="flow-node exception-node">
                <div className="node-icon-bubble" style={{ background: '#fffbeb', color: '#d97706' }}>
                  <AlertTriangle size={15} />
                </div>
                <div className="node-header" style={{ color: '#b45309' }}>Exception Detected</div>
                <div className="node-title">{exceptions[0] || 'Execution Error / Timeout'}</div>
                <div className="node-sub">Trigger Circuit Breaker</div>
              </div>

              <div className="flow-connector dashed">
                <ArrowRight size={16} color="#d97706" />
              </div>

              <div className="flow-node rollback-node">
                <div className="node-icon-bubble" style={{ background: '#fef2f2', color: '#dc2626' }}>
                  <RotateCcw size={15} />
                </div>
                <div className="node-header" style={{ color: '#b91c1c' }}>Fault Recovery</div>
                <div className="node-title">Rollback Node</div>
                <div className="node-sub">{rollbackStrategy.slice(0, 48)}...</div>
              </div>

              <div className="flow-connector dashed">
                <ArrowRight size={16} color="#dc2626" />
              </div>

              <div className="flow-node escalate-node">
                <div className="node-header" style={{ color: '#7c3aed' }}>Escalation Gate</div>
                <div className="node-title">Page On-Call SRE</div>
                <div className="node-sub">High-Priority Alert</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Gemini Step Explanation Modal */}
      <StepExplanationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        step={selectedStepForModal}
        workflowName={workflowName}
        category={category}
      />
    </div>
  );
}
