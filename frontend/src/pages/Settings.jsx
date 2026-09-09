import { useState } from 'react'
import { Settings as SettingsIcon, Save, RefreshCw, Database, Lock, Globe, Eye, Bell, Shield, AlertTriangle, CheckCircle, ChevronRight } from 'lucide-react'

const initialSettings = {
  system: {
    appName: 'SecureDoc AI',
    environment: 'production',
    debugMode: false,
    maintenanceMode: false,
    timezone: 'UTC',
    dateFormat: 'YYYY-MM-DD',
    defaultRiskThreshold: 55,
    autoFlagThreshold: 80,
  },
  riskLevels: {
    low: { max: 30, label: 'Low Risk', color: '#10B981', autoApprove: true },
    suspicious: { max: 70, label: 'Suspicious', color: '#F59E0B', autoReview: true },
    high: { max: 100, label: 'High Risk', color: '#F43F5E', autoFlag: true },
  },
  notifications: {
    email: true,
    slack: true,
    highRiskAlerts: true,
    suspiciousAlerts: true,
    dailyReport: true,
    weeklyReport: false,
  },
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('system')
  const [settings, setSettings] = useState(initialSettings)
  const [saved, setSaved] = useState(false)

  const tabs = [
    { id: 'system', label: 'System Configuration', icon: SettingsIcon },
    { id: 'risk', label: 'Risk Thresholds', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ]

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-slate-400 text-sm mt-1">Configure system parameters and preferences</p>
        </div>
        {saved && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 animate-pulse">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-emerald-400">Settings saved successfully</span>
          </div>
        )}
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

      {/* Save/Cancel bar */}
      <div className="flex items-center justify-between mb-6 p-4 rounded-lg bg-surface-100 border border-surface-200">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Database className="w-4 h-4" />
          <span>MongoDB Atlas</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 ml-2" />
          <span className="text-emerald-400">Connected</span>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleSave} className="btn-primary">
            <Save className="w-4 h-4" />
            Save Changes
          </button>
          <button className="btn-secondary text-sm">Reset to Defaults</button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Globe className="w-5 h-5 text-primary-400" />
              Application Settings
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Application Name</label>
                <input
                  type="text"
                  value={settings.system.appName}
                  onChange={(e) => setSettings({ ...settings, system: { ...settings.system, appName: e.target.value } })}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Environment</label>
                <select
                  value={settings.system.environment}
                  onChange={(e) => setSettings({ ...settings, system: { ...settings.system, environment: e.target.value } })}
                  className="input-field appearance-none cursor-pointer"
                >
                  <option value="production" className="bg-surface-50">Production</option>
                  <option value="staging" className="bg-surface-50">Staging</option>
                  <option value="development" className="bg-surface-50">Development</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Timezone</label>
                <select
                  value={settings.system.timezone}
                  onChange={(e) => setSettings({ ...settings, system: { ...settings.system, timezone: e.target.value } })}
                  className="input-field appearance-none cursor-pointer"
                >
                  <option value="UTC" className="bg-surface-50">UTC</option>
                  <option value="Asia/Kolkata" className="bg-surface-50">Asia/Kolkata (IST)</option>
                  <option value="America/New_York" className="bg-surface-50">America/New_York</option>
                  <option value="Europe/London" className="bg-surface-50">Europe/London</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Date Format</label>
                <select
                  value={settings.system.dateFormat}
                  onChange={(e) => setSettings({ ...settings, system: { ...settings.system, dateFormat: e.target.value } })}
                  className="input-field appearance-none cursor-pointer"
                >
                  <option value="YYYY-MM-DD" className="bg-surface-50">YYYY-MM-DD</option>
                  <option value="DD-MM-YYYY" className="bg-surface-50">DD-MM-YYYY</option>
                  <option value="MM-DD-YYYY" className="bg-surface-50">MM-DD-YYYY</option>
                </select>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-primary-400" />
              System Behavior
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <div>
                  <p className="text-sm font-medium text-white">Debug Mode</p>
                  <p className="text-xs text-slate-400">Enable detailed logging and verbose output</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, system: { ...settings.system, debugMode: !settings.system.debugMode } })}
                  className={`w-11 h-6 rounded-full transition-colors ${settings.system.debugMode ? 'bg-primary-500' : 'bg-surface-200'}`}
                >
                  <span className={`inline-block w-5 h-5 rounded-full bg-white shadow transition-transform ${settings.system.debugMode ? 'translate-x-5' : 'translate-x-0.5'}`} />
                </button>
              </div>
              <div className="flex items-center justify-between p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <div>
                  <p className="text-sm font-medium text-white">Maintenance Mode</p>
                  <p className="text-xs text-slate-400">Disable new screenings while performing maintenance</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, system: { ...settings.system, maintenanceMode: !settings.system.maintenanceMode } })}
                  className={`w-11 h-6 rounded-full transition-colors ${settings.system.maintenanceMode ? 'bg-primary-500' : 'bg-surface-200'}`}
                >
                  <span className={`inline-block w-5 h-5 rounded-full bg-white shadow transition-transform ${settings.system.maintenanceMode ? 'translate-x-5' : 'translate-x-0.5'}`} />
                </button>
              </div>
            </div>
          </div>

          <div className="card border-amber-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Default Thresholds
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Default Risk Threshold</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={settings.system.defaultRiskThreshold}
                  onChange={(e) => setSettings({ ...settings, system: { ...settings.system, defaultRiskThreshold: parseInt(e.target.value) } })}
                  className="input-field"
                />
                <p className="text-xs text-slate-500 mt-1">Score above this value triggers suspicious classification</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Auto-Flag Threshold</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={settings.system.autoFlagThreshold}
                  onChange={(e) => setSettings({ ...settings, system: { ...settings.system, autoFlagThreshold: parseInt(e.target.value) } })}
                  className="input-field"
                />
                <p className="text-xs text-slate-500 mt-1">Score above this value auto-flags for investigation</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Lock className="w-5 h-5 text-primary-400" />
              Database Connection
            </h2>
            <div className="p-4 rounded-lg bg-surface-100 border border-surface-200/50">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <Database className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">MongoDB Atlas (Free M0)</p>
                    <p className="text-xs text-slate-400">securedoc@cluster0.xxxxx.mongodb.net</p>
                  </div>
                </div>
                <span className="badge badge-low text-xs">Connected</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Connection Status</span>
                <span className="text-emerald-400 font-medium">Healthy</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-slate-400">Database</span>
                <span className="text-white font-mono">{process.env.MONGODB_DATABASE || 'securedoc'}</span>
              </div>
            </div>
            <button className="btn-secondary text-sm w-full mt-3 justify-center">
              <RefreshCw className="w-4 h-4" />
              Reconnect
            </button>
          </div>
        </div>
      )}

      {activeTab === 'risk' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Risk Level Configurations</h2>
            <div className="space-y-4">
              {Object.entries(settings.riskLevels).map(([key, level]) => (
                <div key={key} className="p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                  <div className="flex items-center gap-4 mb-4">
                    <div className={`w-4 h-4 rounded-full`} style={{ backgroundColor: level.color }} />
                    <div>
                      <p className="text-lg font-bold text-white capitalize">{level.label}</p>
                      <p className="text-sm text-slate-400">Score range: {key === 'high' ? '71-100' : key === 'suspicious' ? '31-70' : '0-30'}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Max Score</label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={level.max}
                        onChange={(e) => {
                          const newLevel = { ...level, max: parseInt(e.target.value) }
                          setSettings({
                            ...settings,
                            riskLevels: { ...settings.riskLevels, [key]: newLevel }
                          })
                        }}
                        className="input-field text-center"
                      />
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-surface-200">
                      <span className="text-xs text-slate-400">Auto-Review</span>
                      <button
                        onClick={() => {
                          const newLevel = { ...level, autoReview: key === 'suspicious' ? !level.autoReview : level.autoReview }
                          setSettings({ ...settings, riskLevels: { ...settings.riskLevels, [key]: newLevel } })
                        }}
                        className={`w-9 h-5 rounded-full transition-colors ${level.autoReview && key === 'suspicious' ? 'bg-primary-500' : 'bg-surface-100'}`}
                        disabled={key !== 'suspicious'}
                      >
                        <span className={`inline-block w-4 h-4 rounded-full bg-white shadow transition-transform ${level.autoReview && key === 'suspicious' ? 'translate-x-4' : 'translate-x-0.5'}`} />
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-surface-200">
                      <span className="text-xs text-slate-400">Flag</span>
                      <button
                        onClick={() => {
                          const newLevel = { ...level, autoFlag: key === 'high' ? !level.autoFlag : level.autoFlag }
                          setSettings({ ...settings, riskLevels: { ...settings.riskLevels, [key]: newLevel } })
                        }}
                        className={`w-9 h-5 rounded-full transition-colors ${level.autoFlag && key === 'high' ? 'bg-primary-500' : 'bg-surface-100'}`}
                        disabled={key !== 'high'}
                      >
                        <span className={`inline-block w-4 h-4 rounded-full bg-white shadow transition-transform ${level.autoFlag && key === 'high' ? 'translate-x-4' : 'translate-x-0.5'}`} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'notifications' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Notification Preferences</h2>
          <div className="space-y-3">
            {Object.entries(settings.notifications).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between p-4 rounded-lg bg-surface-100 border border-surface-200/50">
                <div>
                  <p className="text-sm font-medium text-white capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                  <p className="text-xs text-slate-400">
                    {key === 'email' && 'Send notifications to configured email addresses'}
                    {key === 'slack' && 'Send notifications to Slack integration channel'}
                    {key === 'highRiskAlerts' && 'Trigger alert when case is flagged as high risk'}
                    {key === 'suspiciousAlerts' && 'Trigger alert when case is flagged as suspicious'}
                    {key === 'dailyReport' && 'Send daily summary report of all screenings'}
                    {key === 'weeklyReport' && 'Send weekly summary report of all screenings'}
                  </p>
                </div>
                <button
                  onClick={() => setSettings({
                    ...settings,
                    notifications: { ...settings.notifications, [key]: !value }
                  })}
                  className={`w-11 h-6 rounded-full transition-colors ${value ? 'bg-primary-500' : 'bg-surface-200'}`}
                >
                  <span className={`inline-block w-5 h-5 rounded-full bg-white shadow transition-transform ${value ? 'translate-x-5' : 'translate-x-0.5'}`} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
