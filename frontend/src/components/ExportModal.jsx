import React, { useState, useEffect } from 'react';
import { 
  X, 
  Download, 
  Copy, 
  Check, 
  FileCode, 
  FileText, 
  Layers, 
  Terminal, 
  Printer, 
  Share2,
  ExternalLink
} from 'lucide-react';

const EXPORT_TARGETS = [
  { id: 'servicenow', name: 'ServiceNow Flow Designer', ext: 'json', mime: 'application/json', icon: Layers, desc: 'Enterprise ITSM flow definition with trigger conditions and scripted actions' },
  { id: 'jira', name: 'Jira Automation Rule', ext: 'json', mime: 'application/json', icon: FileCode, desc: 'Native Atlassian Jira automation rule template ready for import' },
  { id: 'github_actions', name: 'GitHub Actions Workflow', ext: 'yml', mime: 'text/yaml', icon: Terminal, desc: 'CI/CD pipeline YAML with checkout, safety gates, and action steps' },
  { id: 'ansible', name: 'Ansible Playbook', ext: 'yml', mime: 'text/yaml', icon: Terminal, desc: 'Host and VM configuration playbook with idempotency assertions' },
  { id: 'python', name: 'Python Runbook Script', ext: 'py', mime: 'text/x-python', icon: Terminal, desc: 'Executable Python 3 script template with logging and mocked API clients' },
  { id: 'executive_summary', name: 'CFO / CIO Executive Memo', ext: 'html', mime: 'text/html', icon: FileText, desc: 'Print-ready executive business case with financial ROI and governance stamps' },
];

export default function ExportModal({ isOpen, onClose, draftId, spec }) {
  const [activeTarget, setActiveTarget] = useState('servicenow');
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && draftId) {
      loadExport(activeTarget);
    }
  }, [isOpen, draftId, activeTarget]);

  const loadExport = async (targetId) => {
    setLoading(true);
    setCopied(false);
    try {
      const res = await fetch(`/api/exports/automation/${draftId}/target?target=${targetId}`);
      if (res.ok) {
        const text = await res.text();
        setContent(text);
      } else {
        setContent(`# Failed to load export format for ${targetId}`);
      }
    } catch (err) {
      console.error('Export fetch error:', err);
      setContent(`# Error connecting to export service for ${targetId}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!content) return;
    const targetMeta = EXPORT_TARGETS.find(t => t.id === activeTarget);
    const filename = `${draftId.toLowerCase()}_${activeTarget}.${targetMeta.ext}`;
    const blob = new Blob([content], { type: targetMeta.mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handlePrintExecutive = () => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  if (!isOpen) return null;

  const currentMeta = EXPORT_TARGETS.find(t => t.id === activeTarget);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '920px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-purple">Multi-Target Enterprise Exporter</span>
              <code style={{ fontSize: '0.85rem' }}>{draftId}</code>
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '4px' }}>
              Export Automation Specification &amp; Runbooks
            </h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Transform verified workflow specs into production-ready ITSM rules, DevOps CI/CD pipelines, or executive memos.
            </p>
          </div>
          <button 
            onClick={onClose} 
            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', padding: '4px' }}
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Target Tabs */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', padding: '12px 0', borderBottom: '1px solid #f1f5f9' }}>
          {EXPORT_TARGETS.map(t => {
            const Icon = t.icon;
            const isSelected = activeTarget === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTarget(t.id)}
                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '0.78rem', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Icon size={14} />
                <span>{t.name}</span>
              </button>
            );
          })}
        </div>

        {/* Target Description Bar */}
        <div style={{ padding: '8px 12px', background: '#f8fafc', borderRadius: '6px', marginTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: '#475569' }}>
            <strong>Target:</strong> {currentMeta?.desc}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              className="btn btn-outline btn-sm" 
              onClick={() => window.open(`/api/exports/automation/${draftId}/pdf`, '_blank')} 
              title="Download Boardroom-Ready Executive Business Case PDF Memo directly rendered by server"
              style={{ borderColor: '#fca5a5', color: '#b91c1c' }}
            >
              <Download size={14} color="#dc2626" /> Download Executive PDF
            </button>
            {activeTarget === 'executive_summary' && (
              <button className="btn btn-outline btn-sm" onClick={handlePrintExecutive} title="Print or Save as PDF">
                <Printer size={14} /> Print HTML
              </button>
            )}
            <button className="btn btn-outline btn-sm" onClick={handleCopy} disabled={loading || !content}>
              {copied ? <Check size={14} color="#059669" /> : <Copy size={14} />}
              <span>{copied ? 'Copied!' : 'Copy Code'}</span>
            </button>
            <button className="btn btn-primary btn-sm" onClick={handleDownload} disabled={loading || !content}>
              <Download size={14} /> Download File
            </button>
          </div>
        </div>

        {/* Content Viewer */}
        <div style={{ flex: 1, marginTop: '12px', minHeight: '360px', overflowY: 'auto' }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', color: '#64748b' }}>
              Synthesizing target template via Google ADK specification engine...
            </div>
          ) : activeTarget === 'executive_summary' ? (
            <div 
              style={{ 
                background: '#ffffff', 
                border: '1px solid #e2e8f0', 
                borderRadius: '8px', 
                padding: '16px',
                maxHeight: '440px',
                overflowY: 'auto'
              }}
            >
              <iframe 
                srcDoc={content} 
                title="Executive Business Case Memo" 
                style={{ width: '100%', height: '420px', border: 'none' }}
              />
            </div>
          ) : (
            <pre 
              style={{ 
                background: '#0f172a', 
                color: '#f8fafc', 
                padding: '16px', 
                borderRadius: '8px', 
                fontSize: '0.82rem', 
                fontFamily: 'monospace', 
                overflowX: 'auto',
                maxHeight: '440px'
              }}
            >
              <code>{content}</code>
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
