import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  CheckCircle, 
  XCircle, 
  RotateCcw, 
  Download, 
  FileCode, 
  Layers, 
  Lock, 
  Terminal, 
  FileText,
  UserCheck,
  Check,
  AlertOctagon,
  Share2,
  AlertTriangle,
  GitBranch,
  Sparkles
} from 'lucide-react';
import ProcessDiagram from '../components/ProcessDiagram';
import ExportModal from '../components/ExportModal';
import StepExplanationModal from '../components/StepExplanationModal';

export default function AutomationStudioView({ workflowId, currentRole = 'Governance Approver' }) {
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewComments, setReviewComments] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewerName, setReviewerName] = useState('Demo Approver (Governance Lead)');
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [modalStep, setModalStep] = useState(null);
  const [isStepModalOpen, setIsStepModalOpen] = useState(false);

  const canApprove = currentRole === 'Governance Approver' || currentRole === 'Admin';

  const fetchDraft = async () => {
    setLoading(true);
    try {
      let wfId = workflowId;
      if (!wfId) {
        // Auto-detect top discovered workflow if not explicitly provided
        try {
          const wfRes = await fetch('/api/workflows');
          if (wfRes.ok) {
            const wfs = await wfRes.json();
            if (wfs && wfs.length > 0) {
              wfId = wfs[0].workflow_id;
            }
          }
        } catch (e) {
          console.warn('Could not auto-fetch top workflow:', e);
        }
      }

      if (wfId) {
        const draftRes = await fetch(`/api/automations/draft?workflow_id=${encodeURIComponent(wfId)}`, { method: 'POST' });
        if (draftRes.ok) {
          const data = await draftRes.json();
          setSpec(data);
          return;
        }
      }

      const res = await fetch('/api/automations/any');
      if (res.ok) {
        const data = await res.json();
        setSpec(data);
      } else {
        setSpec(null);
      }
    } catch (err) {
      console.error('Failed to load specification draft:', err);
      setSpec(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDraft();
  }, [workflowId]);

  const handleReviewAction = async (action) => {
    if (!spec) return;
    if (!canApprove) {
      alert(`RBAC Permission Denied: Role "${currentRole}" cannot record approval decisions.`);
      return;
    }
    setSubmittingReview(true);
    try {
      const res = await fetch(`/api/automations/${spec.draft_id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: action,
          reviewer_name: reviewerName,
          reviewer_role: currentRole,
          comments: reviewComments || `Recorded ${action} decision via Automation Studio review gate.`
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setSpec(updated);
        setReviewComments('');
      } else {
        const errData = await res.json();
        alert(`Review failed: ${errData.detail || 'Access Denied'}`);
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleExport = (format) => {
    if (!spec) return;
    window.open(`/api/exports/automation/${spec.draft_id}?format=${format}`, '_blank');
  };

  if (loading) {
    return <div className="card">Drafting automation specification via Google ADK Agent...</div>;
  }

  if (!spec) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <div style={{ display: 'inline-flex', padding: '16px', background: '#f1f5f9', borderRadius: '50%', marginBottom: '16px' }}>
          <Sparkles size={36} color="#6366f1" />
        </div>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
          No Automation Draft Available
        </h3>
        <p style={{ color: '#64748b', maxWidth: '520px', margin: '0 auto 20px', fontSize: '0.92rem' }}>
          Connect an enterprise ticketing source (Jira or ServiceNow) in Data &amp; Config, or select a discovered workflow from Workflow Opportunities to draft a grounded specification.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={fetchDraft}>
            <RotateCcw size={16} /> Check for Drafts
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* MANDATORY SAFETY BOUNDARY BANNER */}
      <div 
        style={{ 
          background: '#fef2f2', 
          border: '2px solid #ef4444', 
          borderRadius: '10px', 
          padding: '16px 20px', 
          display: 'flex', 
          alignItems: 'center', 
          gap: '14px', 
          boxShadow: '0 2px 4px rgba(239, 68, 68, 0.1)' 
        }}
      >
        <AlertOctagon size={28} color="#dc2626" style={{ flexShrink: 0 }} />
        <div>
          <div style={{ fontWeight: 700, color: '#991b1b', fontSize: '0.95rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Mandatory Safety Boundary
          </div>
          <div style={{ color: '#b91c1c', fontSize: '0.88rem', marginTop: '2px' }}>
            Approval is a recorded review decision, <strong>NOT permission to execute</strong> the proposed automation. 
            The Workflow Mining Agent <strong>never executes generated automations automatically</strong>.
          </div>
        </div>
      </div>

      {/* Header and Export Controls */}
      <div className="card">
        <div className="responsive-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ minWidth: '260px', flex: '1 1 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '6px' }}>
              <span className="badge badge-purple">Google ADK Multi-Step Agent</span>
              <code style={{ fontSize: '0.85rem' }}>{spec.draft_id}</code>
              <span className={`badge ${
                spec.approval_status === 'APPROVED' ? 'badge-green' :
                spec.approval_status === 'REJECTED' ? 'badge-red' :
                spec.approval_status === 'REVISION_REQUESTED' ? 'badge-amber' : 'badge-blue'
              }`}>
                Status: {spec.approval_status}
              </span>
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>{spec.workflow_name}</h2>
            <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '4px' }}>
              {spec.business_objective}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm" onClick={() => setIsExportModalOpen(true)}>
              <Share2 size={14} /> Multi-Target Exporter
            </button>
            <button className="btn btn-outline btn-sm" onClick={() => handleExport('markdown')}>
              <Download size={14} /> Markdown
            </button>
            <button className="btn btn-outline btn-sm" onClick={() => handleExport('json')}>
              <FileCode size={14} /> JSON
            </button>
          </div>
        </div>
      </div>

      {/* Interactive BPMN Process Diagram */}
      <ProcessDiagram 
        workflowName={spec.workflow_name}
        triggers={spec.trigger_conditions || ['Incoming high-priority incident']}
        preconditions={spec.preconditions || ['Verify valid credentials and service reachability']}
        steps={spec.ordered_steps || []}
        approvalRequired={spec.human_approval_gate?.required}
        approvalRole={spec.human_approval_gate?.approval_role}
        exceptions={spec.exception_handling || ['API rate limit exceeded', 'Health check assertion timeout']}
        rollbackStrategy={spec.rollback_and_recovery_strategy || 'Revert changes and alert SRE lead'}
      />

      {/* Two Column Layout: Specification Details and Human Review Gate */}
      <div className="responsive-split-studio" style={{ display: 'grid', gap: '22px' }}>
        {/* Left Column: Ordered Steps, Decision Rules, Rollback */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Ordered Automation Steps */}
          <div className="card">
            <h3 className="card-title">
              <Layers size={18} color="#2563eb" /> Ordered Automation Steps
            </h3>
            <p className="card-desc">Grounded in actual ticket resolution notes and target API contracts.</p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {spec.ordered_steps?.map((step) => (
                <div 
                  key={step.step_number}
                  className="clickable-step-row"
                  onClick={() => {
                    setModalStep(step);
                    setIsStepModalOpen(true);
                  }}
                  style={{
                    padding: '14px',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    background: '#ffffff'
                  }}
                  title="Click for Gemini Step Rationale & Optimization Analysis"
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#2563eb' }}>
                        Step {step.step_number}
                      </span>
                      <strong style={{ fontSize: '0.9rem' }}>{step.step_name}</strong>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="badge badge-purple" style={{ fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <Sparkles size={11} /> Gemini Explain
                      </span>
                      <span className={`badge ${step.is_grounded_in_evidence ? 'badge-green' : 'badge-amber'}`}>
                        {step.is_grounded_in_evidence ? '✅ Grounded' : '💡 Recommendation'}
                      </span>
                    </div>
                  </div>

                  <p style={{ fontSize: '0.88rem', color: '#334155', marginBottom: '8px' }}>
                    {step.action_description}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#64748b' }}>
                    <span>Target System: <code>{step.target_system_or_api}</code></span>
                    {step.evidence_source_note && <span>{step.evidence_source_note}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Rollback Strategy & Idempotency */}
          <div className="card">
            <h3 className="card-title">
              <RotateCcw size={18} color="#dc2626" /> Rollback &amp; Fault Recovery Strategy
            </h3>
            <p style={{ fontSize: '0.88rem', color: '#334155', marginBottom: '14px' }}>
              {spec.rollback_and_recovery_strategy}
            </p>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '0.82rem' }}>
              <strong>Retry &amp; Idempotency Policy:</strong> {spec.retry_strategy_and_idempotency}
            </div>
          </div>

          {/* Proposed Workflow Implementation Pseudocode */}
          <div className="card">
            <h3 className="card-title">
              <Terminal size={18} color="#7c3aed" /> Proposed Workflow Definition (Pseudocode)
            </h3>
            <pre 
              style={{ 
                background: '#0f172a', 
                color: '#e2e8f0', 
                padding: '16px', 
                borderRadius: '8px', 
                fontSize: '0.82rem', 
                overflowX: 'auto',
                lineHeight: 1.45
              }}
            >
              {spec.pseudocode_or_workflow_definition}
            </pre>
          </div>
        </div>

        {/* Right Column: Human Review Gate & Security Parameters */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Human Review & Approval Action Card */}
          <div className="card" style={{ border: '2px solid #cbd5e1' }}>
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UserCheck size={18} color="#2563eb" /> Human Review &amp; Approval Gate
            </h3>
            <p className="card-desc">
              All automated workflows require verified human review before being scheduled into engineering backlogs.
            </p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Reviewer Identity</label>
              <input 
                type="text"
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Review Comments &amp; Justification</label>
              <textarea 
                rows="3"
                placeholder="Enter review notes, security verification comments, or change authorization ID..."
                value={reviewComments}
                onChange={(e) => setReviewComments(e.target.value)}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '0.85rem' }}
              />
            </div>

            {/* Action Buttons with RBAC boundary */}
            {!canApprove && (
              <div className="alert alert-warning" style={{ fontSize: '0.8rem', padding: '10px 12px', marginBottom: '12px' }}>
                <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                <span>
                  <strong>RBAC Restricted:</strong> Active role is <em>"{currentRole}"</em>. Only <strong>Governance Approver</strong> or <strong>Admin</strong> can record human approval decisions.
                </span>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button 
                className="btn btn-success" 
                disabled={submittingReview || !canApprove}
                onClick={() => handleReviewAction('APPROVED')}
                style={{ width: '100%', opacity: canApprove ? 1 : 0.6 }}
                title={canApprove ? "Record approval decision" : "Restricted: Approver or Admin role required"}
              >
                <CheckCircle size={16} /> Approve Proposal (Record Review Decision)
              </button>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <button 
                  className="btn btn-danger" 
                  disabled={submittingReview || !canApprove}
                  onClick={() => handleReviewAction('REJECTED')}
                  style={{ opacity: canApprove ? 1 : 0.6 }}
                >
                  <XCircle size={15} /> Reject
                </button>
                <button 
                  className="btn btn-outline" 
                  disabled={submittingReview || !canApprove}
                  onClick={() => handleReviewAction('REVISION_REQUESTED')}
                  style={{ opacity: canApprove ? 1 : 0.6 }}
                >
                  <RotateCcw size={15} /> Request Revision
                </button>
              </div>
            </div>

            {/* Audit Log Record */}
            {spec.reviewed_at && (
              <div style={{ marginTop: '16px', padding: '10px', background: '#f8fafc', borderRadius: '6px', fontSize: '0.78rem', color: '#64748b' }}>
                <div><strong>Recorded Decision:</strong> {spec.approval_status}</div>
                <div><strong>Reviewer:</strong> {spec.reviewer_name}</div>
                <div><strong>Timestamp:</strong> {new Date(spec.reviewed_at).toLocaleString()}</div>
                {spec.reviewer_comments && <div><strong>Comments:</strong> {spec.reviewer_comments}</div>}
              </div>
            )}
          </div>

          {/* Security & Access Controls */}
          <div className="card">
            <h3 className="card-title">
              <Lock size={18} color="#059669" /> Security &amp; IAM Permissions
            </h3>
            <ul style={{ fontSize: '0.84rem', color: '#334155', paddingLeft: '18px', marginTop: '8px' }}>
              {spec.security_and_permission_requirements?.map((req, i) => (
                <li key={i} style={{ marginBottom: '6px' }}>{req}</li>
              ))}
            </ul>
          </div>

          {/* Evidence Citations */}
          <div className="card">
            <h3 className="card-title">
              <FileText size={18} color="#2563eb" /> Supporting Evidence Tickets
            </h3>
            <p className="card-desc">Source tickets inspected by the ADK Agent to validate these procedural steps.</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {spec.evidence_ticket_ids?.map((tid, i) => (
                <span key={i} className="badge badge-gray" style={{ fontSize: '0.8rem' }}>
                  {tid}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Target Export Modal */}
      <ExportModal 
        isOpen={isExportModalOpen} 
        onClose={() => setIsExportModalOpen(false)} 
        draftId={spec.draft_id} 
        spec={spec} 
      />

      {/* Gemini Step Explanation Modal */}
      <StepExplanationModal 
        isOpen={isStepModalOpen} 
        onClose={() => setIsStepModalOpen(false)} 
        step={modalStep} 
        workflowName={spec.workflow_name || 'Automated Remediation'} 
        category={spec.business_objective || 'Production Infrastructure'}
      />
    </div>
  );
}
