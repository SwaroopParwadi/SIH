import { useState } from 'react'
import { TrendingUp, Brain, Trophy, BarChart3, Shoot, Target, RefreshCw, Calendar, Download } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, Cell } from 'recharts'

const METRICS = {
  accuracy: { value: 96.2, unit: '%', target: 95, trend: '+2.1%', positive: true },
  precision: { value: 94.8, unit: '%', target: 93, trend: '+1.5%', positive: true },
  recall: { value: 93.5, unit: '%', target: 92, trend: '+3.2%', positive: true },
  f1Score: { value: 94.1, unit: '%', target: 93, trend: '+2.8%', positive: true },
  rocAuc: { value: 0.987, unit: '', target: 0.98, trend: '+0.005', positive: true },
  inferenceTime: { value: 0.34, unit: 's', target: 0.5, trend: '-18%', positive: true },
}

const CONFUSION_MATRIX = {
  truePositive: 287,
  falsePositive: 15,
  trueNegative: 291,
  falseNegative: 7,
  total: 600,
}

const TRAINING_HISTORY = {
  epochs: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
  trainAccuracy: [0.72, 0.81, 0.88, 0.92, 0.94, 0.95, 0.96, 0.965, 0.97, 0.973, 0.975, 0.977, 0.978, 0.979, 0.98],
  valAccuracy: [0.70, 0.78, 0.84, 0.89, 0.91, 0.92, 0.925, 0.93, 0.935, 0.938, 0.94, 0.941, 0.94, 0.94, 0.938],
  trainLoss: [1.2, 0.85, 0.62, 0.48, 0.38, 0.32, 0.28, 0.25, 0.23, 0.21, 0.19, 0.18, 0.17, 0.16, 0.15],
  valLoss: [1.25, 0.92, 0.72, 0.58, 0.46, 0.40, 0.37, 0.35, 0.34, 0.33, 0.32, 0.325, 0.33, 0.34, 0.35],
}

const MANIPULATION_TYPE_PERFORMANCE = [
  { type: 'Text Change', samples: 125, accuracy: 94.4, detected: 118, undetected: 7, color: '#F59E0B' },
  { type: 'Photo Change', samples: 110, accuracy: 96.4, detected: 106, undetected: 4, color: '#3B82F6' },
  { type: 'Number Change', samples: 95, accuracy: 92.6, detected: 88, undetected: 7, color: '#10B981' },
  { type: 'Date Change', samples: 80, accuracy: 90.0, detected: 72, undetected: 8, color: '#8B5CF6' },
  { type: 'Copy Paste', samples: 100, accuracy: 95.0, detected: 95, undetected: 5, color: '#F43F5E' },
  { type: 'Clone', samples: 110, accuracy: 93.6, detected: 103, undetected: 7, color: '#06B6D4' },
  { type: 'Compression', samples: 90, accuracy: 88.9, detected: 80, undetected: 10, color: '#F97316' },
  { type: 'Mixed', samples: 90, accuracy: 92.2, detected: 83, undetected: 7, color: '#EC4899' },
]

const MODEL_VERSIONS = [
  { version: 'v1.0', date: '2026-06-15', accuracy: 87.3, f1: 86.1, status: 'deprecated', notes: 'Initial release, baseline model' },
  { version: 'v1.5', date: '2026-07-20', accuracy: 91.2, f1: 90.4, status: 'deprecated', notes: 'Added data augmentation' },
  { version: 'v2.0', date: '2026-08-10', accuracy: 94.1, f1: 93.2, status: 'deprecated', notes: 'Architecture upgrade, ensemble methods' },
  { version: 'v2.1', date: '2026-09-05', accuracy: 96.2, f1: 94.1, status: 'active', notes: 'Current production model' },
]

export default function ModelPerformance() {
  const [activeTab, setActiveTab] = useState('overview')

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'training', label: 'Training History', icon: TrendingUp },
    { id: 'detection', label: 'Detection by Type', icon: Target },
    { id: 'versions', label: 'Model Versions', icon: RefreshCw },
  ]

  const confusionMatrixData = [
    { category: 'Actual Positive', 'Predicted Positive': CONFUSION_MATRIX.truePositive, 'Predicted Negative': CONFUSION_MATRIX.falseNegative },
    { category: 'Actual Negative', 'Predicted Positive': CONFUSION_MATRIX.falsePositive, 'Predicted Negative': CONFUSION_MATRIX.trueNegative },
  ]

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Model Performance</h1>
          <p className="text-slate-400 text-sm mt-1">AI model metrics, training history, and detection capabilities</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Brain className="w-4 h-4" />
          <span>Model: DetectionNet-v2.1</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 ml-2" />
          <span className="text-emerald-400">Active</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 mb-6 border-b border-surface-200">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {Object.entries(METRICS).map(([key, metric]) => (
              <div key={key} className="card">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-sm text-slate-400 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                  <Trophy className="w-4 h-4 text-amber-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-white">{metric.value}</span>
                  <span className="text-slate-400">{metric.unit}</span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  {metric.positive ? (
                    <TrendingUp className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <TrendingUp className="w-3 h-3 text-rose-400 rotate-180" />
                  )}
                  <span className={`text-xs font-medium ${metric.positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {metric.trend} vs target
                  </span>
                </div>
                <div className="mt-3">
                  <div className="flex-1 h-1.5 bg-surface-200 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-500"
                      style={{ width: `${Math.min(100, (metric.value / (metric.target * 1.1)) * 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-slate-500">
                    <span>0</span>
                    <span className="text-emerald-400">Target: {metric.target}{metric.unit}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Confusion Matrix */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-4">Confusion Matrix</h2>
              <p className="text-sm text-slate-400 mb-4">Test set: 600 samples (300 authentic, 300 manipulated)</p>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="text-left text-xs text-slate-400 uppercase pb-2"></th>
                      <th className="text-left text-xs text-emerald-400 uppercase pb-2">Predicted Positive</th>
                      <th className="text-left text-xs text-rose-400 uppercase pb-2">Predicted Negative</th>
                    </tr>
                  </thead>
                  <tbody>
                    {confusionMatrixData.map(row => (
                      <tr key={row.category} className="border-b border-surface-200">
                        <td className="py-3 text-sm text-slate-300">{row.category}</td>
                        <td className={`py-3 text-sm font-mono ${row['Predicted Positive'] > row['Predicted Negative'] ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {row['Predicted Positive']}
                        </td>
                        <td className={`py-3 text-sm font-mono ${row['Predicted Negative'] > row['Predicted Positive'] ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {row['Predicted Negative']}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                <div className="p-2 rounded bg-emerald-500/10">
                  <p className="text-xs text-slate-400">True Positive Rate</p>
                  <p className="text-lg font-bold text-emerald-400">{CONFUSION_MATRIX.truePositive / 300 * 100}%</p>
                </div>
                <div className="p-2 rounded bg-rose-500/10">
                  <p className="text-xs text-slate-400">False Positive Rate</p>
                  <p className="text-lg font-bold text-rose-400">{CONFUSION_MATRIX.falsePositive / 300 * 100}%</p>
                </div>
                <div className="p-2 rounded bg-surface-100">
                  <p className="text-xs text-slate-400">Overall Accuracy</p>
                  <p className="text-lg font-bold text-white">{METRICS.accuracy}%</p>
                </div>
              </div>
            </div>

            {/* Detection Rate by Category */}
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-4">Detection by Manipulation Type</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-surface-200">
                      <th className="text-left text-xs text-slate-400 uppercase pb-3">Manipulation</th>
                      <th className="text-right text-xs text-slate-400 uppercase pb-3">Samples</th>
                      <th className="text-right text-xs text-slate-400 uppercase pb-3">Detected</th>
                      <th className="text-right text-xs text-slate-400 uppercase pb-3">Missed</th>
                      <th className="text-right text-xs text-slate-400 uppercase pb-3">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MANIPULATION_TYPE_PERFORMANCE.map(type => (
                      <tr key={type.type} className="border-b border-surface-200/50">
                        <td className="py-3 flex items-center gap-2">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: type.color }} />
                          <span className="text-sm text-white">{type.type}</span>
                        </td>
                        <td className="py-3 text-sm text-slate-300 text-right">{type.samples}</td>
                        <td className="py-3 text-sm text-emerald-400 text-right">{type.detected}</td>
                        <td className="py-3 text-sm text-rose-400 text-right">{type.undetected}</td>
                        <td className="py-3 text-sm text-right">
                          <span className={`font-medium ${type.accuracy >= 93 ? 'text-emerald-400' : type.accuracy >= 90 ? 'text-amber-400' : 'text-rose-400'}`}>
                            {type.accuracy}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'training' && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-4">Accuracy Over Epochs</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={TRAINING_HISTORY.epochs.map((ep, i) => ({
                    epoch: `E${ep}`,
                    'Training': TRAINING_HISTORY.trainAccuracy[i],
                    'Validation': TRAINING_HISTORY.valAccuracy[i],
                  }))}>
                    <XAxis dataKey="epoch" stroke="#64748b" fontSize={12} />
                    <YAxis domain={[0, 1]} stroke="#64748b" fontSize={12} tickFormatter={v => `${Math.round(v * 100)}%`} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
                      formatter={(value) => [`${Math.round(value * 100)}%`, '']}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="Training" stroke="#3B82F6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Validation" stroke="#10B981" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold text-white mb-4">Loss Over Epochs</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={TRAINING_HISTORY.epochs.map((ep, i) => ({
                    epoch: `E${ep}`,
                    'Training': TRAINING_HISTORY.trainLoss[i],
                    'Validation': TRAINING_HISTORY.valLoss[i],
                  }))}>
                    <XAxis dataKey="epoch" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="Training" stroke="#3B82F6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Validation" stroke="#F43F5E" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Training Summary</h2>
              <Calendar className="w-5 h-5 text-slate-500" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-white">15</p>
                <p className="text-xs text-slate-400">Epochs Trained</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">2,000</p>
                <p className="text-xs text-slate-400">Total Samples</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">94.0%</p>
                <p className="text-xs text-slate-400">Best Val Accuracy</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">0.34s</p>
                <p className="text-xs text-slate-400">Avg Inference Time</p>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'detection' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Detection Performance by Manipulation Type</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MANIPULATION_TYPE_PERFORMANCE} layout="vertical">
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" fontSize={12} tickFormatter={v => `${v}%`} />
                <YAxis dataKey="type" type="category" width={120} stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
                  formatter={(value, name) => [`${value}%`, name === 'accuracy' ? 'Accuracy' : '']}
                />
                <Bar dataKey="accuracy" radius={[0, 4, 4, 0]} maxBarSize={32}>
                  {MANIPULATION_TYPE_PERFORMANCE.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'versions' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Model Version History</h2>
          <div className="space-y-3">
            {MODEL_VERSIONS.map((v) => (
              <div key={v.version} className="flex items-center gap-4 p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  v.status === 'active' ? 'bg-emerald-500/10' : 'bg-surface-200'
                }`}>
                  <Brain className={`w-5 h-5 ${v.status === 'active' ? 'text-emerald-400' : 'text-slate-500'}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-white">{v.version}</span>
                    {v.status === 'active' && (
                      <span className="badge badge-low text-xs">Active</span>
                    )}
                    {v.status === 'deprecated' && (
                      <span className="badge bg-surface-100 text-slate-400 text-xs">Deprecated</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400">{v.date}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{v.notes}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-emerald-400">{v.accuracy}%</p>
                  <p className="text-xs text-slate-500">F1: {v.f1}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
