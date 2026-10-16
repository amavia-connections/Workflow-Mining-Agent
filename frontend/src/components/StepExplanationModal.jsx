import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  X, 
  Target, 
  Zap, 
  ShieldCheck, 
  Clock, 
  RefreshCw, 
  Cpu, 
  Layers, 
  CheckCircle2, 
  AlertCircle,
  ExternalLink
} from 'lucide-react';

export default function StepExplanationModal({ 
  isOpen, 
  onClose, 
  step, 
  workflowName = 'IT Operations Workflow',
  category = 'IT Operations' 
}) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const fetchExplanation = async () => {
    if (!step) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/workflows/explain-step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_name: workflowName,
          step_number: step.step_number || 1,
          step_name: step.step_name || 'Operational Step',
          target_system: step.target_system_or_api || 'Target Enterprise System',
          action_description: step.action_description || '',
          evidence_source_note: step.evidence_source_note || null,
          workflow_category: category
        })
      });

      if (!res.ok) {
        throw new Error(`Failed to load step intelligence (HTTP ${res.status})`);
      }

      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error('Error fetching step explanation:', err);
      setError(err.message || 'Could not retrieve Gemini explanation.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && step) {
      fetchExplanation();
    } else {
      setData(null);
      setError(null);
    }
  }, [isOpen, step?.step_name, step?.step_number]);

  if (!isOpen || !step) return null;

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()} 
        style={{ 
          maxWidth: '780px', 
          width: '92%', 
          borderRadius: '12px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          border: '1px solid #e2e8f0',
          padding: '24px 28px'
        }}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
              <span className="badge badge-blue" style={{ fontWeight: 700, fontSize: '0.72rem', letterSpacing: '0.04em' }}>
                STEP {step.step_number || 1}
              </span>
              <span className="badge badge-purple" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
                <Sparkles size={12} color="#9333ea" /> Gemini Step Intelligence
              </span>
              {step.is_grounded_in_evidence && (
                <span className="badge badge-green" style={{ fontSize: '0.72rem' }}>
                  ✓ Grounded in Evidence
                </span>
              )}
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', margin: '4px 0 2px' }}>
              {step.step_name}
            </h2>
            <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Workflow: <strong>{workflowName}</strong></span>
              <span>&bull;</span>
              <span>Target: <code style={{ color: '#2563eb', fontWeight: 600 }}>{step.target_system_or_api || 'Target System'}</code></span>
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px', borderRadius: '4px' }}
            title="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Action Description context */}
        {step.action_description && (
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '10px 14px', margin: '16px 0 20px', fontSize: '0.85rem', color: '#334155' }}>
            <span style={{ fontWeight: 600, color: '#475569' }}>Action Description: </span>
            {step.action_description}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div style={{ padding: '40px 20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
            <div style={{ position: 'relative', width: '48px', height: '48px' }}>
              <RefreshCw size={36} color="#7c3aed" className="spin" style={{ margin: 'auto' }} />
              <Sparkles size={18} color="#2563eb" style={{ position: 'absolute', top: '-4px', right: '-4px' }} />
            </div>
            <div>
              <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                Gemini 1.5 Flash is analyzing operational rationale...
              </strong>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                Synthesizing failure modes, automation playbooks, and toil reduction estimates.
              </p>
            </div>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="alert alert-warning" style={{ margin: '16px 0' }}>
            <AlertCircle size={18} />
            <div>
              <strong>Analysis Notice:</strong> {error}
              <button 
                className="btn btn-outline btn-sm" 
                onClick={fetchExplanation} 
                style={{ marginTop: '8px', display: 'block', fontSize: '0.75rem' }}
              >
                Retry Gemini Analysis
              </button>
            </div>
          </div>
        )}

        {/* Populated Gemini Analysis Body */}
        {!loading && data && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '58vh', overflowY: 'auto', paddingRight: '4px', marginTop: '16px' }}>
            {/* Card 1: Why This Step Is Needed */}
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <div style={{ background: '#eff6ff', color: '#2563eb', padding: '6px', borderRadius: '6px', display: 'flex' }}>
                  <Target size={16} />
                </div>
                <strong style={{ fontSize: '0.9rem', color: '#1e3a8a' }}>
                  Why This Step Is Needed (Operational Rationale)
                </strong>
              </div>
              <p style={{ fontSize: '0.86rem', color: '#334155', lineHeight: '1.55', margin: 0 }}>
                {data.why_needed}
              </p>
            </div>

            {/* Card 2: What & How It Can Improve */}
            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <div style={{ background: '#dcfce7', color: '#16a34a', padding: '6px', borderRadius: '6px', display: 'flex' }}>
                  <Zap size={16} />
                </div>
                <strong style={{ fontSize: '0.9rem', color: '#14532d' }}>
                  What It Can Improve &amp; Recommended Automation
                </strong>
              </div>
              <p style={{ fontSize: '0.86rem', color: '#166534', lineHeight: '1.55', margin: '0 0 10px 0' }}>
                {data.how_to_improve}
              </p>
              
              {/* Tooling recommendations tags */}
              {data.automation_tooling && data.automation_tooling.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#15803d', textTransform: 'uppercase', marginRight: '6px' }}>
                    Recommended Tooling:
                  </span>
                  <div style={{ display: 'inline-flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                    {data.automation_tooling.map((tool, i) => (
                      <span key={i} className="badge badge-green" style={{ fontSize: '0.72rem', fontWeight: 600 }}>
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Card 3: Safeguards & Rollback Gates */}
            <div style={{ background: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: '8px', padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <div style={{ background: '#f3e8ff', color: '#7e22ce', padding: '6px', borderRadius: '6px', display: 'flex' }}>
                  <ShieldCheck size={16} />
                </div>
                <strong style={{ fontSize: '0.9rem', color: '#581c87' }}>
                  Verification Criteria &amp; Rollback Safeguards
                </strong>
              </div>
              <p style={{ fontSize: '0.86rem', color: '#4c1d95', lineHeight: '1.55', margin: 0 }}>
                {data.safeguards}
              </p>
            </div>

            {/* Card 4: Toil Reduction & Impact */}
            <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ background: '#fef3c7', color: '#b45309', padding: '6px', borderRadius: '6px', display: 'flex', flexShrink: 0 }}>
                <Clock size={16} />
              </div>
              <div>
                <strong style={{ fontSize: '0.82rem', color: '#78350f', textTransform: 'uppercase' }}>
                  Estimated Toil Reduction
                </strong>
                <div style={{ fontSize: '0.86rem', color: '#92400e', fontWeight: 600, marginTop: '1px' }}>
                  {data.time_savings}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="#7c3aed" />
            <span>AI Model: <strong>{data?.model_name || 'Gemini 1.5 Flash'}</strong></span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              type="button" 
              className="btn btn-outline btn-sm"
              onClick={fetchExplanation}
              disabled={loading}
              style={{ fontSize: '0.78rem' }}
            >
              <RefreshCw size={12} className={loading ? 'spin' : ''} /> Regenerate
            </button>
            <button 
              type="button" 
              className="btn btn-primary btn-sm"
              onClick={onClose}
              style={{ fontSize: '0.78rem' }}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
