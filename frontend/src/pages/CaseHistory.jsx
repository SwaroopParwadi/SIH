import { useState, useMemo } from 'react'
import { Search, Filter, ChevronLeft, ChevronRight, Eye, Download, Calendar, Shield, X } from 'lucide-react'

const ALL_CASES = [
  { id: 'SD-2026-0847', name: 'Arjun Sharma', docType: 'Passport', country: 'IND', risk: 'low', score: 12, status: 'Verified', date: '2026-09-10', time: '14:32' },
  { id: 'SD-2026-0846', name: 'Kiara Mehta', docType: 'National ID', country: 'GBR', risk: 'suspicious', score: 67, status: 'Under Review', date: '2026-09-10', time: '14:28' },
  { id: 'SD-2026-0845', name: 'Vivaan Bose', docType: 'Visa', country: 'CAN', risk: 'high', score: 89, status: 'Flagged', date: '2026-09-10', time: '14:15' },
  { id: 'SD-2026-0844', name: 'Sara Kulkarni', docType: 'Passport', country: 'CAN', risk: 'low', score: 8, status: 'Verified', date: '2026-09-10', time: '13:58' },
  { id: 'SD-2026-0843', name: 'Rohan Rao', docType: 'National ID', country: 'IND', risk: 'low', score: 23, status: 'Verified', date: '2026-09-10', time: '13:42' },
  { id: 'SD-2026-0842', name: 'Neel Patel', docType: 'Passport', country: 'CAN', risk: 'low', score: 15, status: 'Verified', date: '2026-09-10', time: '13:25' },
  { id: 'SD-2026-0841', name: 'Diya Malhotra', docType: 'National ID', country: 'USA', risk: 'low', score: 18, status: 'Verified', date: '2026-09-10', time: '12:50' },
  { id: 'SD-2026-0840', name: 'Anaya Bose', docType: 'Visa', country: 'USA', risk: 'suspicious', score: 55, status: 'Under Review', date: '2026-09-10', time: '12:15' },
  { id: 'SD-2026-0839', name: 'Aditya Joshi', docType: 'Passport', country: 'AUS', risk: 'low', score: 9, status: 'Verified', date: '2026-09-10', time: '11:42' },
  { id: 'SD-2026-0838', name: 'Tara Iyer', docType: 'National ID', country: 'SGP', risk: 'low', score: 22, status: 'Verified', date: '2026-09-10', time: '11:18' },
  { id: 'SD-2026-0837', name: 'Ishaan Mehta', docType: 'Passport', country: 'USA', risk: 'low', score: 14, status: 'Verified', date: '2026-09-09', time: '16:30' },
  { id: 'SD-2026-0836', name: 'Meera Kapoor', docType: 'Driver License', country: 'USA', risk: 'high', score: 78, status: 'Flagged', date: '2026-09-09', time: '15:55' },
  { id: 'SD-2026-0835', name: 'Kabir Rao', docType: 'Passport', country: 'AUS', risk: 'low', score: 11, status: 'Verified', date: '2026-09-09', time: '14:20' },
  { id: 'SD-2026-0834', name: 'Sara Desai', docType: 'National ID', country: 'AUS', risk: 'suspicious', score: 62, status: 'Under Review', date: '2026-09-09', time: '13:45' },
  { id: 'SD-2026-0833', name: 'Vivaan Sharma', docType: 'Passport', country: 'IND', risk: 'low', score: 7, status: 'Verified', date: '2026-09-09', time: '12:10' },
  { id: 'SD-2026-0832', name: 'Kiara Patel', docType: 'Visa', country: 'GBR', risk: 'low', score: 19, status: 'Verified', date: '2026-09-09', time: '10:35' },
  { id: 'SD-2026-0831', name: 'Rohan Kulkarni', docType: 'Passport', country: 'USA', risk: 'low', score: 21, status: 'Verified', date: '2026-09-08', time: '17:22' },
  { id: 'SD-2026-0830', name: 'Anaya Sharma', docType: 'National ID', country: 'IND', risk: 'suspicious', score: 58, status: 'Under Review', date: '2026-09-08', time: '16:05' },
]

const PAGE_SIZE = 8

function StatusBadge({ status }) {
  const colors = {
    'Verified': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    'Under Review': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    'Flagged': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    'Pending': 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  }
  return (
    <span className={`badge ${colors[status] || 'bg-surface-100 text-slate-400'}`}>
      {status}
    </span>
  )
}

export default function CaseHistory() {
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)

  const filteredCases = useMemo(() => {
    return ALL_CASES.filter(c => {
      const matchesSearch = search === '' ||
        c.id.toLowerCase().includes(search.toLowerCase()) ||
        c.name.toLowerCase().includes(search.toLowerCase())
      const matchesRisk = riskFilter === 'all' || c.risk === riskFilter
      const matchesStatus = statusFilter === 'all' || c.status === statusFilter
      return matchesSearch && matchesRisk && matchesStatus
    })
  }, [search, riskFilter, statusFilter])

  const totalPages = Math.ceil(filteredCases.length / PAGE_SIZE)
  const paginatedCases = filteredCases.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Case History</h1>
          <p className="text-slate-400 text-sm mt-1">All document screenings with filtering and search</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Shield className="w-4 h-4" />
          <span>{filteredCases.length} cases found</span>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-slate-400 mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setCurrentPage(1) }}
                placeholder="Case ID or subject name..."
                className="input-field pl-9"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Risk Filter */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Risk Level</label>
            <select
              value={riskFilter}
              onChange={(e) => { setRiskFilter(e.target.value); setCurrentPage(1) }}
              className="input-field appearance-none cursor-pointer"
            >
              <option value="all">All Risk Levels</option>
              <option value="low" className="bg-surface-50">Low Risk</option>
              <option value="suspicious" className="bg-surface-50">Suspicious</option>
              <option value="high" className="bg-surface-50">High Risk</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1) }}
              className="input-field appearance-none cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="Verified" className="bg-surface-50">Verified</option>
              <option value="Under Review" className="bg-surface-50">Under Review</option>
              <option value="Flagged" className="bg-surface-50">Flagged</option>
              <option value="Pending" className="bg-surface-50">Pending</option>
            </select>
          </div>

          {/* Export */}
          <div className="flex items-end">
            <button className="btn-secondary text-sm">
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Cases Table */}
      <div className="card">
        {paginatedCases.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Search className="w-12 h-12 text-slate-600 mb-4" />
            <p className="text-slate-400 font-medium">No cases match your filters</p>
            <p className="text-slate-500 text-sm mt-1">Try adjusting your search or filter criteria</p>
            <button onClick={() => { setSearch(''); setRiskFilter('all'); setStatusFilter('all') }} className="btn-secondary mt-4 text-sm">
              Clear all filters
            </button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-surface-200">
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Case ID</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Subject</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Document</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Country</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Risk</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Score</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Status</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2">Screened</th>
                    <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3 px-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedCases.map((c) => (
                    <tr
                      key={c.id}
                      className="border-b border-surface-200/50 hover:bg-surface-100 transition-colors cursor-pointer"
                    >
                      <td className="py-3 px-2 text-sm text-primary-400 font-mono">{c.id}</td>
                      <td className="py-3 px-2 text-sm text-white font-medium">{c.name}</td>
                      <td className="py-3 px-2 text-sm text-slate-400">{c.docType}</td>
                      <td className="py-3 px-2 text-sm text-slate-400 font-mono">{c.country}</td>
                      <td className="py-3 px-2">
                        <span className={`badge ${c.risk === 'low' ? 'badge-low' : c.risk === 'suspicious' ? 'badge-suspicious' : 'badge-high'}`}>
                          {c.risk.charAt(0).toUpperCase() + c.risk.slice(1)}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-sm text-slate-300 font-mono">{c.score}</td>
                      <td className="py-3 px-2">
                        <StatusBadge status={c.status} />
                      </td>
                      <td className="py-3 px-2 text-sm text-slate-500">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" />
                          {c.date}
                        </div>
                      </td>
                      <td className="py-3 px-2">
                        <button className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1 transition-colors">
                          <Eye className="w-4 h-4" />
                          View
                        </button>
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
                  Showing {((currentPage - 1) * PAGE_SIZE) + 1}-{Math.min(currentPage * PAGE_SIZE, filteredCases.length)} of {filteredCases.length} cases
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
    </div>
  )
}
