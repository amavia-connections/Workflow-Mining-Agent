import React, { useState, useEffect } from 'react';
import { Search, Filter, Eye, X, ArrowLeft, ArrowRight, FileText, CheckCircle, Tag } from 'lucide-react';

export default function TicketExplorerView({ onNavigateToWorkflow }) {
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [selectedWorkflow, setSelectedWorkflow] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [availableWorkflows, setAvailableWorkflows] = useState([]);
  const limit = 25;

  const fetchTickets = async () => {
    setLoading(true);
    try {
      let url = `/api/tickets?limit=${limit}&offset=${page * limit}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (selectedWorkflow) url += `&workflow_id=${encodeURIComponent(selectedWorkflow)}`;
      
      const res = await fetch(url);
      const data = await res.json();
      setTickets(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch('/api/workflows')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setAvailableWorkflows(data);
        else if (data && data.workflows) setAvailableWorkflows(data.workflows);
      })
      .catch(e => console.error('Failed to fetch workflows for filter:', e));
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [page, search, selectedWorkflow]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header and Filter Controls */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 className="card-title">Ticket Explorer</h3>
            <p className="card-desc">Inspect raw IT service tickets, categories, resolution notes, and semantic cluster assignments.</p>
          </div>
          <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
            Showing <strong>{tickets.length}</strong> of <strong>{total.toLocaleString()}</strong> tickets
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px auto', gap: '12px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '11px' }} />
            <input 
              type="text"
              placeholder="Search by keywords (e.g. password, disk, permission, restore)..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              style={{
                width: '100%',
                padding: '8px 12px 8px 36px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <select
            value={selectedWorkflow}
            onChange={(e) => { setSelectedWorkflow(e.target.value); setPage(0); }}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.9rem',
              outline: 'none',
              background: '#ffffff'
            }}
          >
            <option value="">All Workflow Clusters</option>
            {availableWorkflows.length > 0 ? (
              availableWorkflows.map(wf => (
                <option key={wf.workflow_id} value={wf.workflow_id}>
                  {wf.workflow_id}: {wf.name}
                </option>
              ))
            ) : (
              <>
                <option value="WF-01">WF-01: Access Requests</option>
                <option value="WF-02">WF-02: Env Resets</option>
                <option value="WF-03">WF-03: Log Cleanup</option>
                <option value="WF-04">WF-04: Password Resets</option>
                <option value="WF-05">WF-05: Deployment Checks</option>
                <option value="WF-06">WF-06: Cert Renewals</option>
              </>
            )}
          </select>

          <button className="btn btn-outline" onClick={() => { setSearch(''); setSelectedWorkflow(''); setPage(0); }}>
            Reset Filters
          </button>
        </div>
      </div>

      {/* Tickets Data Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Title</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Assigned Workflow</th>
              <th>Handling Time</th>
              <th>Assignee</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                  Loading tickets...
                </td>
              </tr>
            ) : tickets.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                  No matching service tickets found.
                </td>
              </tr>
            ) : (
              tickets.map((t) => (
                <tr key={t.ticket_id}>
                  <td>
                    <code style={{ fontSize: '0.82rem', fontWeight: 600 }}>{t.ticket_id}</code>
                  </td>
                  <td style={{ maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    <span style={{ fontWeight: 500 }}>{t.normalized_title || t.title}</span>
                  </td>
                  <td>
                    <span className="badge badge-gray">{t.category}</span>
                  </td>
                  <td>
                    <span className={`badge ${
                      t.priority === 'Critical' ? 'badge-red' : 
                      t.priority === 'High' ? 'badge-amber' : 'badge-blue'
                    }`}>
                      {t.priority}
                    </span>
                  </td>
                  <td>
                    {t.predicted_workflow_id ? (
                      <span className="badge badge-purple" style={{ fontWeight: 600 }}>
                        {t.predicted_workflow_id}
                      </span>
                    ) : (
                      <span className="badge badge-gray">Unclustered</span>
                    )}
                  </td>
                  <td>
                    <strong>{t.estimated_active_handling_minutes || 15}</strong> min
                  </td>
                  <td style={{ fontSize: '0.82rem', color: '#475569' }}>
                    {t.assignee}
                  </td>
                  <td>
                    <button 
                      className="btn btn-outline btn-sm"
                      onClick={() => setSelectedTicket(t)}
                    >
                      <Eye size={13} /> View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
          Page {page + 1} of {Math.max(1, totalPages)}
        </span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className="btn btn-outline btn-sm" 
            disabled={page === 0} 
            onClick={() => setPage(p => Math.max(0, p - 1))}
          >
            <ArrowLeft size={14} /> Previous
          </button>
          <button 
            className="btn btn-outline btn-sm" 
            disabled={page + 1 >= totalPages} 
            onClick={() => setPage(p => p + 1)}
          >
            Next <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Ticket Details & Semantic Assignment Modal */}
      {selectedTicket && (
        <div className="modal-overlay" onClick={() => setSelectedTicket(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <code style={{ fontSize: '1rem', fontWeight: 700 }}>{selectedTicket.ticket_id}</code>
                  <span className={`badge ${
                    selectedTicket.priority === 'Critical' ? 'badge-red' : 'badge-blue'
                  }`}>
                    {selectedTicket.priority} Priority
                  </span>
                  <span className="badge badge-gray">{selectedTicket.category}</span>
                </div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>{selectedTicket.title}</h2>
              </div>
              <button 
                onClick={() => setSelectedTicket(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Why did the agent group this ticket? */}
            <div style={{ background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: '8px', padding: '14px', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <CheckCircle size={16} color="#7c3aed" />
                <strong style={{ color: '#5b21b6', fontSize: '0.9rem' }}>
                  Workflow Assignment: {selectedTicket.predicted_workflow_id || 'Cluster Assigned'}
                </strong>
                <span className="badge badge-purple" style={{ marginLeft: 'auto' }}>
                  Similarity: {Math.round((selectedTicket.similarity_score || 0.88) * 100)}%
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#4c1d95', margin: 0 }}>
                This ticket was clustered into <strong>{selectedTicket.predicted_workflow_id}</strong> based on semantic similarity of its resolution notes and technical terminology matching the operational runbook pattern.
              </p>
            </div>

            {/* Description */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Description</label>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0', marginTop: '4px', fontSize: '0.9rem' }}>
                {selectedTicket.description || 'No description provided.'}
              </div>
            </div>

            {/* Resolution Notes */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Engineer Resolution Notes</label>
              <div style={{ background: '#ecfdf5', padding: '12px', borderRadius: '6px', border: '1px solid #a7f3d0', marginTop: '4px', fontSize: '0.9rem', color: '#065f46' }}>
                {selectedTicket.resolution_notes || 'Resolved according to standard procedures.'}
              </div>
            </div>

            {/* Metadata Footer */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '0.82rem', color: '#64748b', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
              <div><strong>Created:</strong> {selectedTicket.created_at ? new Date(selectedTicket.created_at).toLocaleString() : '-'}</div>
              <div><strong>Resolved:</strong> {selectedTicket.resolved_at ? new Date(selectedTicket.resolved_at).toLocaleString() : '-'}</div>
              <div><strong>Handling Minutes:</strong> {selectedTicket.estimated_active_handling_minutes} min</div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-outline btn-sm" onClick={() => setSelectedTicket(null)}>
                Close
              </button>
              {selectedTicket.predicted_workflow_id && (
                <button 
                  className="btn btn-primary btn-sm" 
                  onClick={() => {
                    const wf = selectedTicket.predicted_workflow_id;
                    setSelectedTicket(null);
                    onNavigateToWorkflow(wf);
                  }}
                >
                  View Workflow Cluster
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
