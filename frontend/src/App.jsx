import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, FileSearch, ClipboardCheck, History, FileText, BarChart3, ScrollText, Settings, Shield, LogOut, Menu, X } from 'lucide-react'
import { useState, useEffect } from 'react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/screening', label: 'New Screening', icon: FileSearch },
  { path: '/results', label: 'Analysis Results', icon: ClipboardCheck },
  { path: '/history', label: 'Case History', icon: History },
  { path: '/cases', label: 'Case Details', icon: FileText },
  { path: '/performance', label: 'Model Performance', icon: BarChart3 },
  { path: '/audit', label: 'Audit', icon: ScrollText },
  { path: '/settings', label: 'Settings', icon: Settings },
]

function Layout({ children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-surface-DEFAULT">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-surface-50 border-r border-surface-200 z-40 transform transition-transform duration-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-surface-200">
            <div className="w-9 h-9 rounded-lg bg-primary-500 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">SecureDoc AI</h1>
              <p className="text-xs text-slate-400">Document Screening System</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = item.path === '/' ? window.location.pathname === '/' : window.location.pathname.startsWith(item.path)

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive: active }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                      active
                        ? 'bg-primary-500/10 text-primary-400 border-l-2 border-primary-400 -ml-0.5 pl-[14px]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-surface-100'
                    }`
                  }
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="px-4 py-4 border-t border-surface-200">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-100">
              <LogOut className="w-4 h-4 text-slate-500" />
              <span className="text-xs text-slate-400">SIH 2026 Prototype</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Mobile sidebar */}
      <div
        className={`fixed left-0 top-0 h-full w-64 bg-surface-50 border-r border-surface-200 z-40 transform transition-transform duration-200 lg:hidden ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between px-6 py-5 border-b border-surface-200">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-primary-500 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">SecureDoc AI</h1>
              </div>
            </div>
            <button onClick={() => setMobileMenuOpen(false)} className="text-slate-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive: active }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                      active
                        ? 'bg-primary-500/10 text-primary-400'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-surface-100'
                    }`
                  }
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Mobile menu button */}
      <button
        onClick={() => setMobileMenuOpen(true)}
        className="fixed top-4 left-4 z-50 lg:hidden w-10 h-10 rounded-lg bg-surface-50 border border-surface-200 flex items-center justify-center text-slate-400 hover:text-white"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Main content */}
      <main className="lg:ml-64 min-h-screen">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screening" element={<NewScreening />} />
        <Route path="/results" element={<AnalysisResults />} />
        <Route path="/history" element={<CaseHistory />} />
        <Route path="/cases/:id" element={<CaseDetails />} />
        <Route path="/performance" element={<ModelPerformance />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
