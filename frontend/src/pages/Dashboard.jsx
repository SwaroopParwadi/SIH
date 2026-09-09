import { useEffect, useState } from 'react'
import { TrendingUp, ShieldCheck, AlertTriangle, AlertCircle, Activity, Database, Type, Barcode, Brain, FaceScan, ChevronRight, Clock } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const RISK_COLORS = {
  low: '#10B981',
  suspicious: '#F59E0B',
  high: '#F43F5E',
}

const SYSTEM_STATUS = {
  mongodb: { label: 'MongoDB Atlas', icon: Database, status: 'connected', latency: '42ms' },
  ocr: { label: 'OCR Engine', icon: Type, status: 'operational', latency: '18ms' },
  mrz: { label: 'MRZ Parser', icon: Activity, status: 'operational', latency: '12ms' },
  barcode: { label: 'Barcode Scanner', icon: Barcode, status: 'operational', latency: '8ms' },
  aiModel: { label: 'AI Model', icon: Brain, status: 'operational', latency: '340ms' },
  faceVerification: { label: 'Face Verification', icon: FaceScan, status: 'standby', latency: '—' },
}

const RECENT_CASES = [
  { id: 'SD-2026-0847', name: 'Arjun Sharma', docType: 'Passport', risk: 'low', score: 12, status: 'Verified', date: '2026-09-10 14:32' },
  { id: 'SD-2026-0846', name: 'Kiara Mehta', docType: 'National ID', risk: 'suspicious', score: 67, status: 'Under Review', date: '2026-09-10 14:28' },
  { id: 'SD-2026-0845', name: 'Vivaan Bose', docType: 'Visa', risk: 'high', score: 89, status: 'Flagged', date: '2026-09-10 14:15' },
  { id: 'SD-2026-0844', name: 'Sara Kulkarni', docType: 'Passport', risk: 'low', score: 8, status: 'Verified', date: '2026-09-10 13:58' },
  { id: 'SD-2026-0843', name: 'Rohan Rao', docType: 'National ID', risk: 'low', score: 23, status: 'Verified', date: '2026-09-10 13:42' },
]

const RISK_DISTRIBUTION = [
  { name: 'Low Risk', value: 72, color: RISK_COLORS.low },
  { name: 'Suspicious', value: 18, color: RISK_COLORS.suspicious },
  { name: 'High Risk', value: 10, color: RISK_COLORS.high },
]

function StatusBadge({ status }) {
  const config = {
    connected: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', dot: 'bg-emerald-400' },
    operational: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', dot: 'bg-emerald-400' },
    standby: { bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-400' },
    degraded: { bg: 'bg-rose-500/10', text: 'text-rose-400', dot: 'bg-rose-400' },
  }
  const c = config[status] || config.standby

  return (
    <span className={`inline-flex items-center gap-1.5 ${c.bg} ${c.text} px-2 py-0.5 rounded-full text-xs font-medium`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function StatCard({ icon: Icon, label, value, subtext, color, trend }) {
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="stat-label">{label}</p>
          <p className="stat-value mt-1">{value}</p>
          {subtext && <p className="text-xs text-slate-500 mt-1">{subtext}</p>}
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-3">
          {trend.dir === 'up' ? <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> : <TrendingUp className="w-3.5 h-3.5 text-rose-400 rotate-180" />}
          <span className={`text-xs font-medium ${trend.dir === 'up' ? 'text-emerald-400' : 'text-rose-400'}`}>{trend.value}</span>
          <span className="text-xs text-slate-500">vs last week</span>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [cases, setCases] = useState(RECENT_CASES)
  const [riskData, setRiskData] = useState(RISK_DISTRIBUTION)

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Real-time document screening overview</p>
        </div>
        <div className="flex items-center gap-3 mt-3 sm:mt-0">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400 font-medium">Live</span>
          </div>
          <span className="text-xs text-slate-500">Last updated: just now</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <StatCard
          icon={ShieldCheck}
          label="Total Documents Screened"
          value="1,247"
          subtext="23 pending review"
          color="bg-primary-500"
          trend={{ dir: 'up', value: '+12.4%' }}
        />
        <StatCard
          icon={ShieldCheck}
          label="Low Risk"
          value="918"
          subtext="73.6% of total"
          color="bg-emerald-500"
        />
        <StatCard
          icon={AlertTriangle}
          label="Suspicious"
          value="225"
          subtext="18.0% of total"
          color="bg-amber-500"
          trend={{ dir: 'up', value: '+3.2%' }}
        />
        <StatCard
          icon={AlertCircle}
          label="High Risk"
          value="124"
          subtext="9.9% of total"
          color="bg-rose-500"
          trend={{ dir: 'down', value: '-2.1%' }}
        />
        <StatCard
          icon={Activity}
          label="Average Risk Score"
          value="34.2"
          subtext="on 0-100 scale"
          color="bg-violet-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Risk Distribution */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Risk Distribution</h2>
              <p className="text-sm text-slate-400">Last 30 days breakdown</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-500" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f1f5f9',
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  iconSize={10}
                  formatter={(value) => (
                    <span className="text-sm text-slate-300">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Trend Bar Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Weekly Risk Trend</h2>
              <p className="text-sm text-slate-400">New cases by risk level</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-500" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { week: 'W1', low: 180, suspicious: 45, high: 28 },
                { week: 'W2', low: 205, suspicious: 52, high: 31 },
                { week: 'W3', low: 195, suspicious: 48, high: 25 },
                { week: 'W4', low: 210, suspicious: 55, high: 29 },
                { week: 'W5', low: 128, suspicious: 25, high: 11 },
              ]}>
                <XAxis dataKey="week" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f1f5f9',
                  }}
                />
                <Bar dataKey="low" fill="#10B981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="suspicious" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                <Bar dataKey="high" fill="#F43F5E" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Cases Table */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent Cases</h2>
            <p className="text-sm text-slate-400">Latest 5 screenings</p>
          </div>
          <a href="/history" className="text-sm text-primary-400 hover:text-primary-300 font-medium flex items-center gap-1">
            View all <ChevronRight className="w-4 h-4" />
          </a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-200">
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Case ID</th>
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Subject</th>
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Document</th>
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Risk</th>
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Score</th>
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Status</th>
                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider pb-3">Screened</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className="border-b border-surface-200/50 hover:bg-surface-100 transition-colors">
                  <td className="py-3 text-sm text-primary-400 font-mono">{c.id}</td>
                  <td className="py-3 text-sm text-white font-medium">{c.name}</td>
                  <td className="py-3 text-sm text-slate-400">{c.docType}</td>
                  <td className="py-3">
                    <span className={`badge ${c.risk === 'low' ? 'badge-low' : c.risk === 'suspicious' ? 'badge-suspicious' : 'badge-high'}`}>
                      {c.risk.charAt(0).toUpperCase() + c.risk.slice(1)}
                    </span>
                  </td>
                  <td className="py-3 text-sm text-slate-300 font-mono">{c.score}</td>
                  <td className="py-3 text-sm">
                    <span className={`inline-flex items-center gap-1.5 ${
                      c.status === 'Verified' ? 'text-emerald-400' :
                      c.status === 'Flagged' ? 'text-rose-400' : 'text-amber-400'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        c.status === 'Verified' ? 'bg-emerald-400' :
                        c.status === 'Flagged' ? 'bg-rose-400' : 'bg-amber-400'
                      }`} />
                      {c.status}
                    </span>
                  </td>
                  <td className="py-3 text-sm text-slate-500">{c.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* System Health */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white">System Health</h2>
            <p className="text-sm text-slate-400">Service status monitoring</p>
          </div>
          <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            All systems nominal
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(SYSTEM_STATUS).map(([key, sys]) => {
            const Icon = sys.icon
            return (
              <div key={key} className="flex items-center gap-4 p-4 rounded-lg bg-surface-100 border border-surface-200/50 hover:border-surface-200 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-primary-500/10 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-primary-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{sys.label}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={sys.status} />
                    <span className="text-xs text-slate-500">{sys.latency}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer note */}
      <div className="mt-6 text-center text-xs text-slate-600">
        <p>SecureDoc AI v1.0 — Smart India Hackathon 2026 Prototype — Data shown is mock for demonstration</p>
      </div>
    </div>
  )
}
