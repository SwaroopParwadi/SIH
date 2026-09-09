import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { ArrowLeft, Shield, Clock, User, FileText, MapPin, Calendar, Hash, Building2, AlertTriangle, CheckCircle, Download, Eye, ExternalLink, ChevronRight } from 'lucide-react'

const CASE_DETAILS = {
  id: 'SD-2026-0846',
  subject: 'Kiara Mehta',
  documentType: 'National ID Card',
  country: 'GBR',
  riskScore: 67,
  riskLevel: 'suspicious',
  status: 'Under Review',
  screenedAt: '2026-09-10 14:28:32 UTC',
  processedAt: '2026-09-10 14:28:34 UTC',
  processingTime: '1.8s',
  examiner: 'Auto Analysis v2.1',
  notes: 'Multiple indicators suggest potential document manipulation. Region of interest at [205, 150, 650, 173] shows font inconsistencies.',
  metadata: {
    surname: 'Mehta',
    givenNames: 'Kiara',
    fullName: 'Kiara Mehta',
    dateOfBirth: '1998-01-25',
    age: 28,
    documentNumber: 'E3511615',
    documentIssue: '2020-03-23',
    documentExpiry: '2030-06-09',
    nationality: 'GBR',
    sex: 'F',
    issuingAuthority: 'HM Passport Office',
    documentVersion: '3.2',
  },
  checks: [
    { name: 'OCR Quality Assessment', status: 'passed', score: 85, details: 'Text extraction successful. All fields readable.' },
    { name: 'MRZ Code Validation', status: 'passed', score: 92, details: 'MRZ checksum valid. Format conforms to ICAO 9303.' },
    { name: 'Barcode Integrity', status: 'passed', score: 78, details: 'PDF417 barcode decoded. Contains expected data fields.' },
    { name: 'Visual Integrity Check', status: 'warning', score: 45, details: 'Anomalous region detected. Pixel analysis shows inconsistencies.' },
    { name: 'Metadata Examination', status: 'warning', score: 52, details: 'EXIF data shows signs of post-processing.' },
    { name: 'Face Verification', status: 'standby', score: null, details: 'Face verification module not activated for this screening.' },
    { name: 'Forgery Detection', status: 'warning', score: 38, details: 'AI model detected potential fabrication indicators with 62% confidence.' },
    { name: 'Document Structure Analysis', status: 'passed', score: 88, details: 'Layout matches genuine document template for GBR National ID.' },
  ],
  evidence: [
    { type: 'document_image', label: 'Original Document', timestamp: '2026-09-10 14:28:32', url: null },
    { type: 'processed_image', label: 'Enhanced Analysis View', timestamp: '2026-09-10 14:28:33', url: null },
    { type: 'heatmap', label: 'Suspicion Heatmap', timestamp: '2026-09-10 14:28:33', url: null },
    { type: 'ocr_result', label: 'OCR Text Output', timestamp: '2026-09-10 14:28:33', url: null },
    { type: 'mrz_decode', label: 'MRZ Decoded Data', timestamp: '2026-09-10 14:28:33', url: null },
  ],
  timeline: [
    { time: '2026-09-10 14:28:32', event: 'Case created', actor: 'System' },
    { time: '2026-09-10 14:28:32', event: 'Document uploaded', actor: 'User' },
    { time: '2026-09-10 14:28:33', event: 'OCR processing started', actor: 'OCR Engine' },
    { time: '2026-09-10 14:28:33', event: 'MRZ parsing completed', actor: 'MRZ Parser' },
    { time: '2026-09-10 14:28:33', event: 'Barcode decoded', actor: 'Barcode Scanner' },
    { time: '2026-09-10 14:28:34', event: 'AI analysis completed', actor: 'AI Model' },
    { time: '2026-09-10 14:28:34', event: 'Risk score calculated: 67', actor: 'AI Model' },
    { time: '2026-09-10 14:28:34', event: 'Case status set to Under Review', actor: 'System' },
  ],
}

function EvidenceRow({ evidence }) {
  return (
    <div className="flex items-center gap-4 p-3 rounded-lg bg-surface-100 border border-surface-200/50 hover:border-surface-200 transition-colors">
      <div className="w-9 h-9 rounded-lg bg-surface-200 flex items-center justify-center flex-shrink-0">
        <Eye className="w-4 h-4 text-slate-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{evidence.label}</p>
        <p className="text-xs text-slate-500 mt-0.5">{evidence.type.replace(/_/g, ' ')}</p>
      </div>
      <span className="text-xs text-slate-500">{evidence.timestamp}</span>
      <button className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1 transition-colors">
        <Download className="w-3.5 h-3.5" />
        Download
      </button>
    </div>
  )
}

export default function CaseDetails() {
  const { id } = useParams()
  const caseData = CASE_DETAILS

  return (
    <div className="max-w-6xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => window.history.back()}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Case History
      </button>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs text-slate-500 font-mono">{caseData.id}</span>
            <span className={`badge ${caseData.riskLevel === 'low' ? 'badge-low' : caseData.riskLevel === 'suspicious' ? 'badge-suspicious' : 'badge-high'}`}>
              {caseData.riskLevel.charAt(0).toUpperCase() + caseData.riskLevel.slice(1)}
            </span>
            <span className={`badge ${caseData.status === 'Verified' ? 'badge-low' : caseData.status === 'Under Review' ? 'badge-suspicious' : 'badge-high'}`}>
              {caseData.status}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">{caseData.subject}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
            <span className="flex items-center gap-1"><FileText className="w-3.5 h-3.5" /> {caseData.documentType}</span>
            <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" /> {caseData.country}</span>
            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Screened {caseData.screenedAt}</span>
            <span className="flex items-center gap-1"><Hash className="w-3.5 h-3.5" /> Processing: {caseData.processingTime}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-sm">
            <Download className="w-4 h-4" />
            Export Report
          </button>
          <button className="btn-primary text-sm">
            <ExternalLink className="w-4 h-4" />
            Full Analysis
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Overview */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Risk Assessment Overview</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <p className="text-sm text-slate-400 mb-1">Overall Risk Score</p>
                <p className={`text-3xl font-bold ${caseData.riskScore <= 30 ? 'text-emerald-400' : caseData.riskScore <= 70 ? 'text-amber-400' : 'text-rose-400'}`}>
                  {caseData.riskScore}
                </p>
                <div className="mt-2">
                  <div className="flex-1 h-2 bg-surface-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        caseData.riskScore <= 30 ? 'bg-emerald-500' : caseData.riskScore <= 70 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${caseData.riskScore}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-slate-500">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                  </div>
                </div>
              </div>
              <div className="p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <p className="text-sm text-slate-400 mb-1">Analysis Confidence</p>
                <p className="text-3xl font-bold text-white">87%</p>
                <p className="text-xs text-slate-500 mt-2">Based on 8 analysis checks</p>
              </div>
              <div className="p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <p className="text-sm text-slate-400 mb-1">Checks Passed</p>
                <p className="text-3xl font-bold text-emerald-400">
                  {caseData.checks.filter(c => c.status === 'passed').length}/{caseData.checks.length}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  {caseData.checks.filter(c => c.status === 'passed').map((c, i) => (
                    <div key={i} className="w-2 h-2 rounded-full bg-emerald-400" />
                  ))}
                  {caseData.checks.filter(c => c.status === 'warning').map((c, i) => (
                    <div key={i} className="w-2 h-2 rounded-full bg-amber-400" />
                  ))}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <p className="text-sm text-slate-400 mb-1">Processing Engine</p>
                <p className="text-lg font-bold text-white">{caseData.examiner}</p>
                <p className="text-xs text-slate-500 mt-1">AI-Powered Analysis v2.1</p>
              </div>
            </div>
          </div>

          {/* Analysis Checks */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Analysis Checks</h2>
            <div className="space-y-1">
              {caseData.checks.map((check) => (
                <div key={check.name} className="flex items-center gap-4 p-3 rounded-lg bg-surface-100 hover:bg-surface-100/80 transition-colors">
                  {check.status === 'passed' && <CheckCircle className="w-5 h-5 text-emerald-400" />}
                  {check.status === 'warning' && <AlertTriangle className="w-5 h-5 text-amber-400" />}
                  {check.status === 'standby' && <Shield className="w-5 h-5 text-slate-500" />}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-white truncate">{check.name}</p>
                      {check.score !== null && (
                        <span className="text-xs font-mono text-slate-400">{check.score}/100</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">{check.details}</p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${
                    check.status === 'passed' ? 'bg-emerald-500/10 text-emerald-400' :
                    check.status === 'warning' ? 'bg-amber-500/10 text-amber-400' :
                    'bg-surface-100 text-slate-400'
                  }`}>
                    {check.status === 'passed' ? 'Pass' : check.status === 'warning' ? 'Review' : 'Standby'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Evidence */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Evidence & Artifacts</h2>
            <div className="space-y-2">
              {caseData.evidence.map((ev, i) => (
                <EvidenceRow key={i} evidence={ev} />
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Case Timeline</h2>
            <div className="space-y-0">
              {caseData.timeline.map((event, i) => (
                <div key={i} className="flex gap-4 pb-4 relative">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 rounded-full bg-primary-500 z-10 ring-4 ring-primary-500/20" />
                    {i < caseData.timeline.length - 1 && <div className="w-0.5 flex-1 bg-surface-200 mt-1" />}
                  </div>
                  <div className="flex-1 pb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500 font-mono">{event.time}</span>
                      <span className="text-xs bg-surface-100 text-slate-400 px-2 py-0.5 rounded-full">{event.actor}</span>
                    </div>
                    <p className="text-sm text-white mt-0.5">{event.event}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Subject Info */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-primary-400" />
              Subject Information
            </h2>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-100">
                <div className="w-10 h-10 rounded-lg bg-surface-200 flex items-center justify-center">
                  <User className="w-5 h-5 text-slate-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{caseData.metadata.fullName}</p>
                  <p className="text-xs text-slate-400">{caseData.metadata.surname}, {caseData.metadata.givenNames}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-lg bg-surface-100">
                  <p className="text-xs text-slate-400 mb-0.5">Date of Birth</p>
                  <p className="text-sm text-white font-medium">{caseData.metadata.dateOfBirth}</p>
                  <p className="text-xs text-slate-500">Age: {caseData.metadata.age}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface-100">
                  <p className="text-xs text-slate-400 mb-0.5">Sex</p>
                  <p className="text-sm text-white font-medium">{caseData.metadata.sex === 'M' ? 'Male' : 'Female'}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface-100">
                  <p className="text-xs text-slate-400 mb-0.5">Nationality</p>
                  <p className="text-sm text-white font-medium font-mono">{caseData.metadata.nationality}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface-100">
                  <p className="text-xs text-slate-400 mb-0.5">Issuing Authority</p>
                  <p className="text-sm text-white font-medium">{caseData.metadata.issuingAuthority}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Document Info */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary-400" />
              Document Information
            </h2>
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-surface-100">
                <p className="text-xs text-slate-400 mb-0.5">Document Number</p>
                <p className="text-sm text-white font-mono font-bold">{caseData.metadata.documentNumber}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-100">
                <p className="text-xs text-slate-400 mb-0.5">Issue Date</p>
                <p className="text-sm text-white font-medium">{caseData.metadata.documentIssue}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-100">
                <p className="text-xs text-slate-400 mb-0.5">Expiry Date</p>
                <p className="text-sm text-white font-medium">{caseData.metadata.documentExpiry}</p>
              </div>
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm text-emerald-400 font-medium">Valid (not expired)</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Expires: {caseData.metadata.documentExpiry}</p>
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-400" />
              Examiner Notes
            </h2>
            <div className="p-3 rounded-lg bg-surface-100 border border-surface-200/50">
              <p className="text-sm text-slate-300 whitespace-pre-wrap">{caseData.notes}</p>
            </div>
            <button className="btn-secondary text-sm w-full mt-3 justify-center">
              <Clock className="w-4 h-4" />
              Add Note
            </button>
          </div>

          {/* Quick Actions */}
          <div className="card border-primary-500/20">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <button className="w-full btn-secondary text-sm justify-start bg-surface-100 hover:bg-surface-200">
                <Eye className="w-4 h-4" />
                View Document
              </button>
              <button className="w-full btn-secondary text-sm justify-start bg-surface-100 hover:bg-surface-200">
                <Download className="w-4 h-4" />
                Download Report
              </button>
              <button className="w-full btn-secondary text-sm justify-start bg-surface-100 hover:bg-surface-200">
                <Clock className="w-4 h-4" />
                Assign to Review
              </button>
              <button className="w-full btn-primary text-sm justify-center">
                <Shield className="w-4 h-4" />
                Flag for Investigation
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
