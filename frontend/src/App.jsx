import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Shield, BarChart3, Bot, AlertTriangle, Zap, CreditCard, Settings } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import Alerts from './pages/Alerts'
import Pricing from './pages/Pricing'
import Landing from './pages/Landing'
import './App.css'

const navItems = [
  { path: '/dashboard', icon: BarChart3, label: 'Dashboard' },
  { path: '/agents', icon: Bot, label: 'Agents' },
  { path: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { path: '/pricing', icon: CreditCard, label: 'Pricing' },
]

function Sidebar() {
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <Shield size={28} strokeWidth={2.5} />
        <span>Cost Guard</span>
      </div>
      <div className="sidebar-nav">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
      <div className="sidebar-footer">
        <div className="sidebar-badge">
          <Zap size={14} />
          <span>Demo Mode</span>
        </div>
      </div>
    </nav>
  )
}

function AppLayout({ children }) {
  return (
    <>
      <Sidebar />
      <main className="main-content">
        {children}
      </main>
    </>
  )
}

export default function App() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

  if (isLanding) return <Landing />

  return (
    <AppLayout>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/pricing" element={<Pricing />} />
      </Routes>
    </AppLayout>
  )
}
