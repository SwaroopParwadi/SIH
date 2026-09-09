import { useState } from 'react'
import { Search, Filter, ChevronLeft, ChevronRight, Eye, Download, FileText, User, Shield, Clock, AlertTriangle } from 'lucide-react'

const AUDIT_LOG = [
  { id: 'AUD-001', timestamp: '2026-09-10 14:32:15', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0847', details: 'New screening case created for Arjun Sharma (Passport, IND)', risk: 'info' },
  { id: 'AUD-002', timestamp: '2026-09-10 14:32:16', user: 'OCR Engine', action: 'OCR_STARTED', resource: 'Case SD-2026-0847', details: 'OCR processing initiated for document image', risk: 'info' },
  { id: 'AUD-003', timestamp: '2026-09-10 14:32:17', user: 'OCR Engine', action: 'OCR_COMPLETED', resource: 'Case SD-2026-0847', details: 'OCR extraction complete. 12 fields extracted with 98% confidence', risk: 'info' },
  { id: 'AUD-004', timestamp: '2026-09-10 14:28:32', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0846', details: 'New screening case created for Kiara Mehta (National ID, GBR)', risk: 'info' },
  { id: 'AUD-005', timestamp: '2026-09-10 14:28:33', user: 'AI Model', action: 'ANALYSIS_COMPLETED', resource: 'Case SD-2026-0846', details: 'Risk score calculated: 67/100. Flagged as suspicious.', risk: 'warning' },
  { id: 'AUD-006', timestamp: '2026-09-10 14:28:34', user: 'System', action: 'STATUS_CHANGED', resource: 'Case SD-2026-0846', details: 'Case status changed from Pending to Under Review', risk: 'info' },
  { id: 'AUD-007', timestamp: '2026-09-10 14:15:02', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0845', details: 'New screening case created for Vivaan Bose (Visa, CAN)', risk: 'info' },
  { id: 'AUD-008', timestamp: '2026-09-10 14:15:03', user: 'AI Model', action: 'ANALYSIS_COMPLETED', resource: 'Case SD-2026-0845', details: 'High risk detected. Score: 89/100. Multiple manipulation indicators found.', risk: 'critical' },
  { id: 'AUD-009', timestamp: '2026-09-10 14:15:04', user: 'System', action: 'CASE_FLAGGED', resource: 'Case SD-2026-0845', details: 'Case automatically flagged for investigation due to high risk score', risk: 'critical' },
  { id: 'AUD-010', timestamp: '2026-09-10 13:58:10', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0844', details: 'New screening case created for Sara Kulkarni (Passport, CAN)', risk: 'info' },
  { id: 'AUD-011', timestamp: '2026-09-10 13:58:11', user: 'System', action: 'CASE_VERIFIED', resource: 'Case SD-2026-0844', details: 'Document verified as authentic. Risk score: 8/100.', risk: 'info' },
  { id: 'AUD-012', timestamp: '2026-09-10 13:42:00', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0843', details: 'New screening case created for Rohan Rao (National ID, IND)', risk: 'info' },
  { id: 'AUD-013', timestamp: '2026-09-10 13:25:45', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0842', details: 'New screening case created for Neel Patel (Passport, CAN)', risk: 'info' },
  { id: 'AUD-014', timestamp: '2026-09-10 12:50:30', user: 'System', action: 'BATCH_UPLOAD', resource: '3 Cases', details: 'Batch of 3 cases processed in sequence', risk: 'info' },
  { id: 'AUD-015', timestamp: '2026-09-10 12:15:00', user: 'Admin User', action: 'CONFIG_CHANGED', resource: 'Risk Thresholds', details: 'Risk threshold for suspicious level adjusted from 60 to 55', risk: 'warning' },
  { id: 'AUD-016', timestamp: '2026-09-09 17:30:00', user: 'System Admin', action: 'SYSTEM_LOGIN', resource: 'Admin Panel', details: 'User logged into SecureDoc AI admin panel from IP 192.168.1.100', risk: 'info' },
  { id: 'AUD-017', timestamp: '2026-09-09 16:05:22', user: 'Admin User', action: 'CASE_CREATED', resource: 'Case SD-2026-0834', details: 'New screening case created for Diya Malhotra (National ID, USA)', risk: 'info' },
  { id: 'AUD-018', timestamp: '2026-09-09 14:45:10', user: 'System', action: 'AUDIT_ARCHIVED', resource: 'Previous Month', details: 'Old audit logs from August 2026 archived to cold storage', risk: 'info' },
]

const PAGE_SIZE = 8

function RiskBadge({ risk }) {
  const colors = {
    info: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    critical: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  }
  return (
    <span className={`badge ${colors[risk] || colors.info}`}>
      {risk.charAt(0).toUpperCase() + risk.slice(1)}
    </span>
  )
}

function ActionBadge({ action }) {
  const labels = {
    CASE_CREATED: 'Case Created',
    OCR_STARTED: 'OCR Started',
    OCR_COMPLETED: 'OCR Completed',
    ANALYSIS_COMPLETED: 'Analysis Done',
    STATUS_CHANGED: 'Status Changed',
    CASE_FLAGGED: 'Case Flagged',
    CASE_VERIFIED: 'Verified',
    BATCH_UPLOAD: 'Batch Upload',
    CONFIG_CHANGED: 'Config Changed',
    SYSTEM_LOGIN: 'Login',
    AUDIT_ARCHIVED: 'Archived',
  }
  return (
    <span className="text-sm text-slate-300">{labels[action] || action}</span>
  )
}

export default function Audit() {
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)

  const filteredLogs = AUDIT_LOG.filter(log => {
    const matchesSearch = search === '' ||
      log.id.toLowerCase().includes(search.toLowerCase()) ||
      log.user.toLowerCase().includes(search.toLowerCase()) ||
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      log.resource.toLowerCase().includes(search.toLowerCase())
    const matchesRisk = riskFilter === 'all' || log.risk === riskFilter
    return matchesSearch && matchesRisk
  })

  const totalPages = Math.ceil(filteredLogs.length / PAGE_SIZE)
  const paginatedLogs = filteredLogs.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Log</h1>
          <p className="text-slate-400 text-sm mt-1">Complete system activity history and accountability trail</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <FileText className="w-4 h-4" />
          <span>{AUDIT_LOG.length} total events</span>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-400 mb-2">Search Events</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setCurrentPage(1) }}
                placeholder="Search by ID, user, action, or resource..."
                className="input-field pl-9"
              />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                  <span className="text-xs text-slate-400">Clear</span>
                </button>
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Risk Level</label>
            <select
              value={riskFilter}
              onChange={(e) => { setRiskFilter(e.target.value); setCurrentPage(1) }}
              className="input-field appearance-none cursor-pointer"
            >
              <option value="all">All Events</option>
              <option value="critical" className="bg-surface-50">Critical</option>
              <option value="warning" className="bg-surface-50">Warning</option>
              <option value="info" className="bg-surface-50">Info</option>
              <option value="success" className="bg-surface-50">Success</option>
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn-secondary text-sm">
              <Download className="w-4 h-4" />
              Export Audit Log
            </button>
          </div>
        </div>
      </div>

      {/* Audit Table */}
      <div className="card">
        {paginatedLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Search className="w-12 h-12 text-slate-600 mb-4" />
            <p className="text-slate-400 font-medium">No events match your filters</p>
            <button onClick={() => { setSearch(''); setRiskFilter('all') }} className="btn-secondary mt-4 text-sm">Clear filters</button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-surface-200">
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">Event ID</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">Timestamp</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">User / System</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">Action</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">Resource</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">Details</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-3">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLogs.map((log) => (
                    <tr key={log.id} className="border-b border-surface-200/50 hover:bg-surface-100 transition-colors">
                      <td className="py-3 px-3 text-sm text-primary-400 font-mono">{log.id}</td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5 text-sm text-slate-300">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          {log.timestamp}
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5">
                          {log.user === 'System' || log.user.includes('Engine') ? (
                            <Shield className="w-3.5 h-3.5 text-slate-500" />
                          ) : (
                            <User className="w-3.5 h-3.5 text-slate-500" />
                          )}
                          <span className="text-sm text-white">{log.user}</span>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <ActionBadge action={log.action} />
                      </td>
                      <td className="py-3 px-3 text-sm text-slate-300">{log.resource}</td>
                      <td className="py-3 px-3 text-sm text-slate-400 max-w-xs truncate">{log.details}</td>
                      <td className="py-3 px-3">
                        <RiskBadge risk={log.risk} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-surface-200">
                <p className="text-sm text-slate-400">
                  Showing {((currentPage - 1) * PAGE_SIZE) + 1}-{Math.min(currentPage * PAGE_SIZE, filteredLogs.length)} of {filteredLogs.length} events
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="btn-secondary text-sm px-3 py-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-sm text-slate-300 font-medium px-2">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="btn-secondary text-sm px-3 py-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
        <div className="stat-card">
          <p className="stat-label">Total Events</p>
          <p className="stat-value mt-1">{AUDIT_LOG.length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Critical Events</p>
          <p className="stat-value mt-1 text-rose-400">{AUDIT_LOG.filter(l => l.risk === 'critical').length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Warning Events</p>
          <p className="stat-value mt-1 text-amber-400">{AUDIT_LOG.filter(l => l.risk === 'warning').length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Last 24 Hours</p>
          <p className="stat-value mt-1">{AUDIT_LOG.length}</p>
        </div>
      </div>
    </div>
  )
}
