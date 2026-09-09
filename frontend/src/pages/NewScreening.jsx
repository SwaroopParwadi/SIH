import { useState } from 'react'
import { Upload, FileText, Shield, AlertTriangle, CheckCircle, X, ArrowRight, Loader2 } from 'lucide-react'

const DOC_TYPES = [
  'Passport',
  'National ID Card',
  'Driver License',
  'Visa',
  'Residence Permit',
  'Employment Card',
  'Student ID',
  'Birth Certificate',
]

const COUNTRIES = [
  'IND', 'USA', 'GBR', 'CAN', 'AUS', 'DEU', 'FRA', 'JPN', 'SGP', 'BRA',
  'MEX', 'ISR', 'NOR', 'SWE', 'CHE', 'NLD', 'POL', 'ESP', 'ITA', 'KOR',
]

const RISK_THRESHOLDS = [
  { label: 'Low Risk', max: 30, color: 'bg-emerald-500' },
  { label: 'Suspicious', max: 70, color: 'bg-amber-500' },
  { label: 'High Risk', max: 100, color: 'bg-rose-500' },
]

function RiskMeter({ score }) {
  const segment = RISK_THRESHOLDS.find(r => score <= r.max) || RISK_THRESHOLDS[2]

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400">Risk Assessment</span>
        <span className={`text-lg font-bold ${score <= 30 ? 'text-emerald-400' : score <= 70 ? 'text-amber-400' : 'text-rose-400'}`}>
          {score}
        </span>
      </div>
      <div className="relative h-3 bg-surface-100 rounded-full overflow-hidden">
        {/* Low segment */}
        <div className="absolute inset-y-0 left-0 w-1/3 bg-emerald-500/30" />
        {/* Suspicious segment */}
        <div className="absolute inset-y-0 left-1/3 w-1/3 bg-amber-500/30" />
        {/* High segment */}
        <div className="absolute inset-y-0 left-2/3 w-1/3 bg-rose-500/30" />
        {/* Indicator */}
        <div
          className={`absolute top-0 bottom-0 w-1 rounded-full transition-all ${segment.color}`}
          style={{ left: `${(score / 100) * 100}%`, transform: 'translateX(-50%)' }}
        />
      </div>
      <div className="flex justify-between mt-1.5 text-xs text-slate-500">
        <span>Low (0-30)</span>
        <span>Suspicious (31-70)</span>
        <span>High (71-100)</span>
      </div>
    </div>
  )
}

export default function NewScreening() {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [documentType, setDocumentType] = useState('')
  const [countryCode, setCountryCode] = useState('')
  const [subjectName, setSubjectName] = useState('')
  const [caseReference, setCaseReference] = useState('')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [riskScore, setRiskScore] = useState(23)
  const [preview, setPreview] = useState(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      setUploadedFile(file)
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (event) => setPreview(event.target.result)
        reader.readAsDataURL(file)
      }
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setUploadedFile(file)
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (event) => setPreview(event.target.result)
        reader.readAsDataURL(file)
      }
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    await new Promise(resolve => setTimeout(resolve, 1800))
    setLoading(false)
    setStep(3)
  }

  const handleStartNew = () => {
    setStep(1)
    setDocumentType('')
    setCountryCode('')
    setSubjectName('')
    setCaseReference('')
    setUploadedFile(null)
    setPreview(null)
    setRiskScore(Math.floor(Math.random() * 40) + 5)
  }

  if (step === 3) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-8 p-6 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <CheckCircle className="w-8 h-8 text-emerald-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Screening Complete</h1>
            <p className="text-slate-400 text-sm mt-1">Case {caseReference} has been processed successfully.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Document Preview */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Document Preview</h2>
            {preview && (
              <div className="relative rounded-lg overflow-hidden bg-surface-100">
                <img src={preview} alt="Uploaded document" className="w-full h-auto max-h-80 object-contain" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
                <div className="absolute bottom-3 left-3">
                  <span className="badge bg-surface-100 text-slate-300 border-surface-200">{documentType}</span>
                </div>
              </div>
            )}
          </div>

          {/* Results */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Screening Results</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-100">
                <span className="text-slate-400 text-sm">Case Reference</span>
                <span className="text-white font-mono">{caseReference}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-100">
                <span className="text-slate-400 text-sm">Subject</span>
                <span className="text-white font-medium">{subjectName}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-100">
                <span className="text-slate-400 text-sm">Document Type</span>
                <span className="text-white">{documentType}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-100">
                <span className="text-slate-400 text-sm">Country</span>
                <span className="text-white font-mono">{countryCode}</span>
              </div>

              <div className="pt-4 border-t border-surface-200">
                <RiskMeter score={riskScore} />
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg bg-surface-100">
                <div>
                  <p className="text-sm text-slate-400">Overall Verdict</p>
                  <p className={`text-lg font-bold ${riskScore <= 30 ? 'text-emerald-400' : riskScore <= 70 ? 'text-amber-400' : 'text-rose-400'}`}>
                    {riskScore <= 30 ? 'LOW RISK — Likely Authentic' : riskScore <= 70 ? 'SUSPICIOUS — Requires Review' : 'HIGH RISK — Flag for Investigation'}
                  </p>
                </div>
                <Shield className={`w-8 h-8 ${riskScore <= 30 ? 'text-emerald-400' : riskScore <= 70 ? 'text-amber-400' : 'text-rose-400'}`} />
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-center mt-8">
          <button onClick={handleStartNew} className="btn-primary">
            <Upload className="w-4 h-4" />
            Start New Screening
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">New Screening</h1>
        <p className="text-slate-400 text-sm mt-1">Upload a document to begin AI-powered verification</p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-2 mb-8">
        {['Upload', 'Details', 'Results'].map((label, i) => {
          const num = i + 1
          const isActive = step === num || (step > num && i < step - 1)
          const isComplete = step > num

          return (
            <div key={label} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                isComplete ? 'bg-emerald-500 text-white' :
                isActive ? 'bg-primary-500 text-white' :
                'bg-surface-100 text-slate-500'
              }`}>
                {isComplete ? <CheckCircle className="w-4 h-4" /> : num}
              </div>
              <span className={`text-sm font-medium ${isActive ? 'text-white' : 'text-slate-500'}`}>{label}</span>
              {i < 2 && (
                <div className={`flex-1 h-0.5 ${step > num + 1 ? 'bg-emerald-500' : 'bg-surface-100'}`} />
              )}
            </div>
          )
        })}
      </div>

      {/* Step 1: Upload */}
      {step === 1 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Upload Document</h2>
          <p className="text-sm text-slate-400 mb-6">
            Supported formats: JPEG, PNG, TIFF. Maximum size: 10MB.
          </p>

          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput').click()}
            className={`relative border-2 border-dashed rounded-xl p-12 cursor-pointer transition-all duration-200 ${
              dragActive ? 'border-primary-500 bg-primary-500/5' : 'border-surface-200 bg-surface-100 hover:bg-surface-100/50'
            }`}
          >
            <input
              id="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/tiff"
              onChange={handleFileInput}
              className="hidden"
            />
            <Upload className={`w-12 h-12 mx-auto mb-4 transition-colors ${dragActive ? 'text-primary-400' : 'text-slate-500'}`} />
            <p className="text-center text-white font-medium mb-1">
              {uploadedFile ? uploadedFile.name : 'Drag & drop document here'}
            </p>
            <p className="text-center text-sm text-slate-400">or click to browse</p>
            {uploadedFile && (
              <p className="text-center text-xs text-emerald-400 mt-2">{uploadedFile.size > 1024 * 1024 ? `${(uploadedFile.size / 1024 / 1024).toFixed(1)} MB` : `${(uploadedFile.size / 1024).toFixed(0)} KB`}</p>
            )}
          </div>

          {preview && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-white mb-3">Preview</h3>
              <div className="rounded-lg overflow-hidden bg-surface-100 border border-surface-200">
                <img src={preview} alt="Preview" className="w-full max-h-64 object-contain" />
              </div>
            </div>
          )}

          {!uploadedFile && (
            <p className="text-sm text-slate-500 mt-4 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Demo mode: No actual upload required. Click "Continue" to proceed.
            </p>
          )}

          <div className="flex justify-end mt-6">
            <button
              onClick={() => setStep(2)}
              className="btn-primary"
              disabled={!uploadedFile}
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Details */}
      {step === 2 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Case Details</h2>
          <p className="text-sm text-slate-400 mb-6">Provide subject and document information</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Case Reference</label>
              <input
                type="text"
                value={caseReference}
                onChange={(e) => setCaseReference(e.target.value.toUpperCase())}
                placeholder="SD-2026-XXXX"
                className="input-field font-mono"
              />
              <p className="text-xs text-slate-500 mt-1">Auto-generated if left blank</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Subject Name</label>
              <input
                type="text"
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
                placeholder="Full name of subject"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Document Type</label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="input-field appearance-none cursor-pointer"
              >
                <option value="" className="bg-surface-50">Select document type</option>
                {DOC_TYPES.map(dt => (
                  <option key={dt} value={dt} className="bg-surface-50">{dt}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Country of Issue</label>
              <select
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
                className="input-field appearance-none cursor-pointer"
              >
                <option value="" className="bg-surface-50">Select country</option>
                {COUNTRIES.map(c => (
                  <option key={c} value={c} className="bg-surface-50">{c}</option>
                ))}
              </select>
            </div>

            {uploadedFile && preview && (
              <div className="pt-4 border-t border-surface-200">
                <h3 className="text-sm font-medium text-white mb-3">Document Preview</h3>
                <div className="rounded-lg overflow-hidden bg-surface-100 border border-surface-200">
                  <img src={preview} alt="Preview" className="w-full max-h-48 object-contain" />
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between mt-6">
            <button onClick={() => setStep(1)} className="btn-secondary">
              <X className="w-4 h-4" />
              Back
            </button>
            <button
              onClick={handleSubmit}
              className="btn-primary"
              disabled={!documentType || !countryCode}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  Analyze Document
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
