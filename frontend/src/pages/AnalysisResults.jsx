import { useState } from 'react'
import { Shield, AlertTriangle, CheckCircle, X, Eye, Copy, Hash, Clock, ChevronDown, ChevronUp, ArrowLeft } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const ANALYSIS_RESULT = {
  caseId: 'SD-2026-0846',
  subject: 'Kiara Mehta',
  documentType: 'National ID Card',
  country: 'GBR',
  riskScore: 67,
  riskLevel: 'suspicious',
  verdict: 'Requires Manual Review',
  screenedAt: '2026-09-10 14:28:32 UTC',
  processingTime: '1.8s',
  checks: {
    ocr: { status: 'passed', score: 85, label: 'OCR Quality' },
    mrz: { status: 'passed', score: 92, label: 'MRZ Consistency' },
    barcode: { status: 'passed', score: 78, label: 'Barcode Integrity' },
    visualIntegrity: { status: 'warning', score: 45, label: 'Visual Integrity' },
    metadata: { status: 'warning', score: 52, label: 'Metadata Analysis' },
    faceVerification: { status: 'standby', score: null, label: 'Face Verification' },
    forgeryDetection: { status: 'warning', score: 38, label: 'Forgery Detection' },
    documentStructure: { status: 'passed', score: 88, label: 'Document Structure' },
  },
  flags: [
    { type: 'suspicious_region', severity: 'high', description: 'Anomalous region detected at coordinates [205, 150, 650, 173]', detail: 'Text region shows inconsistency with surrounding typography' },
    { type: 'font_mismatch', severity: 'medium', description: 'Font characteristics differ from genuine samples', detail: 'Suspicious region uses slightly different kerning' },
    { type: 'compression_artifact', severity: 'low', description: 'Unusual compression patterns in image data', detail: 'Region shows recompression evidence' },
  ],
  extractedData: {
    surname: 'Mehta',
    givenNames: 'Kiara',
    fullName: 'Kiara Mehta',
    dateOfBirth: '1998-01-25',
    documentNumber: 'E3511615',
    nationality: 'GBR',
    sex: 'F',
    issueDate: '2020-03-23',
    expiryDate: '2030-06-09',
  },
  evidence: {
    originalImage: null,
    processedImage: null,
    suspiciousRegions: [
      { x: 205, y: 150, w: 445, h: 23, label: 'Suspicious Region 1' },
      { x: 45, y: 100, w: 120, h: 150, label: 'Photo Area Analysis' },
    ],
  },
}

function ExpandableRow({ label, children }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="border-b border-surface-200/50 last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full py-3 text-left hover:bg-surface-100/50 transition-colors"
      >
        <span className="text-sm font-medium text-slate-300">{label}</span>
        {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
      </button>
      {expanded && <div className="pb-3">{children}</div>}
    </div>
  )
}

function StatusIcon({ status }) {
  if (status === 'passed') return <CheckCircle className="w-5 h-5 text-emerald-400" />
  if (status === 'warning') return <AlertTriangle className="w-5 h-5 text-amber-400" />
  if (status === 'failed') return <X className="w-5 h-5 text-rose-400" />
  return <Shield className="w-5 h-5 text-slate-500" />
}

export default function AnalysisResults() {
  const [copied, setCopied] = useState(false)
  const { caseId, subject, documentType, country, riskScore, riskLevel, verdict, screenedAt, processingTime, checks, flags, extractedData } = ANALYSIS_RESULT

  const copyToClipboard = () => {
    navigator.clipboard.writeText(caseId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const checkScoreData = Object.entries(checks)
    .filter(([_, c]) => c.score !== null)
    .map(([key, c]) => ({ name: c.label, score: c.score, status: c.status }))

  return (
    <div className="max-w-6xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => window.history.back()}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-white">Analysis Results</h1>
            <span className={`badge ${riskLevel === 'low' ? 'badge-low' : riskLevel === 'suspicious' ? 'badge-suspicious' : 'badge-high'}`}>
              {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>Case ID: <span className="text-primary-400 font-mono">{caseId}</span></span>
            <button onClick={copyToClipboard} className="flex items-center gap-1 hover:text-primary-300 transition-colors">
              {copied ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <span>Screened: {screenedAt}</span>
            <span>Processing: {processingTime}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm text-slate-400">Risk Score</p>
            <p className={`text-3xl font-bold ${riskScore <= 30 ? 'text-emerald-400' : riskScore <= 70 ? 'text-amber-400' : 'text-rose-400'}`}>
              {riskScore}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Verdict Card */}
          <div className={`card border-l-4 ${
            riskLevel === 'low' ? 'border-l-emerald-500 bg-emerald-500/5' :
            riskLevel === 'suspicious' ? 'border-l-amber-500 bg-amber-500/5' :
            'border-l-rose-500 bg-rose-500/5'
          }`}>
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                riskLevel === 'low' ? 'bg-emerald-500/10' :
                riskLevel === 'suspicious' ? 'bg-amber-500/10' :
                'bg-rose-500/10'
              }`}>
                {riskLevel === 'low' ? <CheckCircle className="w-6 h-6 text-emerald-400" /> :
                 riskLevel === 'suspicious' ? <AlertTriangle className="w-6 h-6 text-amber-400" /> :
                 <X className="w-6 h-6 text-rose-400" />}
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{verdict}</h2>
                <p className="text-slate-400 text-sm mt-1">
                  {riskLevel === 'low' && 'Document appears authentic. No significant anomalies detected.'}
                  {riskLevel === 'suspicious' && 'Multiple indicators suggest potential manipulation. Manual review recommended.'}
                  {riskLevel === 'high' && 'Strong evidence of document tampering. Immediate investigation required.'}
                </p>
              </div>
            </div>
          </div>

          {/* Check Results */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Analysis Checks</h2>
            <div className="space-y-1">
              {Object.entries(checks).map(([key, check]) => (
                <div key={key} className="flex items-center gap-4 p-3 rounded-lg bg-surface-100 hover:bg-surface-100/80 transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-surface-200 flex items-center justify-center">
                    <StatusIcon status={check.status} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white">{check.label}</p>
                    {check.score !== null && (
                      <div className="mt-1">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-surface-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                check.score >= 80 ? 'bg-emerald-500' : check.score >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${check.score}%` }}
                            />
                          </div>
                          <span className="text-xs font-mono text-slate-400 w-8 text-right">{check.score}</span>
                        </div>
                      </div>
                    )}
                  </div>
                  {check.status === 'passed' && (
                    <span className="text-xs text-emerald-400 font-medium">Pass</span>
                  )}
                  {check.status === 'warning' && (
                    <span className="text-xs text-amber-400 font-medium">Review</span>
                  )}
                  {check.status === 'standby' && (
                    <span className="text-xs text-slate-500 font-medium">Standby</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Score Chart */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Check Score Breakdown</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={checkScoreData} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} stroke="#64748b" fontSize={12} />
                  <YAxis dataKey="name" type="category" width={140} stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                    }}
                    formatter={(value) => [`${value}/100`, 'Score']}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={24}>
                    {checkScoreData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.score >= 80 ? '#10B981' : entry.score >= 50 ? '#F59E0B' : '#F43F5E'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Flags */}
          {flags.length > 0 && (
            <div className="card border-amber-500/20">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Detection Flags ({flags.length})
              </h2>
              <div className="space-y-3">
                {flags.map((flag, i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-lg bg-surface-100 border border-amber-500/10">
                    <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                      flag.severity === 'high' ? 'bg-rose-400' : flag.severity === 'medium' ? 'bg-amber-400' : 'bg-sky-400'
                    }`} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-medium text-white">{flag.description}</p>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          flag.severity === 'high' ? 'bg-rose-500/10 text-rose-400' :
                          flag.severity === 'medium' ? 'bg-amber-500/10 text-amber-400' :
                          'bg-sky-500/10 text-sky-400'
                        }`}>
                          {flag.severity}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{flag.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Extracted Data */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Hash className="w-5 h-5 text-primary-400" />
              Extracted Data
            </h2>
            <div className="space-y-3">
              {Object.entries(extractedData).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between py-2 border-b border-surface-200/50 last:border-0">
                  <span className="text-xs text-slate-400 uppercase tracking-wider">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                  <span className="text-sm text-white font-medium text-right max-w-[60%]">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk Meter */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Risk Assessment</h2>
            <div className="relative h-4 bg-surface-100 rounded-full overflow-hidden">
              <div className="absolute inset-y-0 left-0 w-1/3 bg-emerald-500/30" />
              <div className="absolute inset-y-0 left-1/3 w-1/3 bg-amber-500/30" />
              <div className="absolute inset-y-0 left-2/3 w-1/3 bg-rose-500/30" />
              <div
                className="absolute top-0 bottom-0 w-1 rounded-full bg-amber-500 transition-all"
                style={{ left: `${(riskScore / 100) * 100}%`, transform: 'translateX(-50%)' }}
              />
            </div>
            <div className="flex justify-between mt-2 text-xs text-slate-500">
              <span>Safe (0-30)</span>
              <span>Review (31-70)</span>
              <span>High (71-100)</span>
            </div>
            <div className="mt-4 p-3 rounded-lg bg-surface-100 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Overall Risk</span>
                <span className={`text-sm font-bold ${riskScore <= 30 ? 'text-emerald-400' : riskScore <= 70 ? 'text-amber-400' : 'text-rose-400'}`}>
                  {riskScore}/100
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Confidence</span>
                <span className="text-sm text-slate-300 font-medium">87%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Checks Passed</span>
                <span className="text-sm text-slate-300 font-medium">
                  {Object.values(checks).filter(c => c.status === 'passed').length}/{Object.keys(checks).length}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Actions</h2>
            <div className="space-y-2">
              <button className="w-full btn-secondary text-sm justify-start bg-surface-100 hover:bg-surface-200">
                <Eye className="w-4 h-4" />
                View Evidence
              </button>
              <button className="w-full btn-secondary text-sm justify-start bg-surface-100 hover:bg-surface-200">
                <Clock className="w-4 h-4" />
                Add Notes
              </button>
              <button className="w-full btn-secondary text-sm justify-start bg-surface-100 hover:bg-surface-200">
                <Shield className="w-4 h-4" />
                Request Manual Review
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
