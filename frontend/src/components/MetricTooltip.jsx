import React, { useState } from 'react';
import { Info } from 'lucide-react';

/**
 * MetricTooltip provides transparent, formula-backed explanations for 
 * calculated financial, operational, and algorithmic metrics.
 */
export default function MetricTooltip({ title, formula, sqlOrigin, note, children }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span 
      style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', verticalAlign: 'middle', marginLeft: '4px' }}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setIsOpen(!isOpen); }}
        style={{
          border: 'none',
          background: 'transparent',
          cursor: 'pointer',
          padding: '2px',
          display: 'inline-flex',
          alignItems: 'center',
          color: '#94a3b8',
          transition: 'color 0.15s'
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
        aria-label="Metric information"
      >
        <Info size={14} className="tooltip-icon" />
      </button>

      {isOpen && (
        <div 
          style={{
            position: 'absolute',
            bottom: '125%',
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#0f172a',
            color: '#f8fafc',
            padding: '12px 14px',
            borderRadius: '8px',
            fontSize: '0.78rem',
            width: '280px',
            boxShadow: '0 10px 25px -5px rgba(0,0,0,0.3)',
            zIndex: 100,
            lineHeight: 1.45,
            pointerEvents: 'none'
          }}
        >
          {title && (
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: '#93c5fd', marginBottom: '4px' }}>
              {title}
            </div>
          )}
          {formula && (
            <div style={{ marginBottom: '6px' }}>
              <span style={{ color: '#94a3b8' }}>Formula: </span>
              <code style={{ background: '#1e293b', padding: '2px 4px', borderRadius: '4px', color: '#38bdf8', fontSize: '0.75rem' }}>
                {formula}
              </code>
            </div>
          )}
          {sqlOrigin && (
            <div style={{ marginBottom: '6px', fontSize: '0.72rem', color: '#cbd5e1' }}>
              <span style={{ color: '#94a3b8' }}>Deterministic Origin: </span>
              {sqlOrigin}
            </div>
          )}
          {note && (
            <div style={{ color: '#e2e8f0', borderTop: '1px solid #334155', paddingTop: '6px', marginTop: '4px' }}>
              {note}
            </div>
          )}
          {children}
          {/* Arrow */}
          <div 
            style={{
              position: 'absolute',
              top: '100%',
              left: '50%',
              transform: 'translateX(-50%)',
              borderWidth: '5px',
              borderStyle: 'solid',
              borderColor: '#0f172a transparent transparent transparent'
            }}
          />
        </div>
      )}
    </span>
  );
}
