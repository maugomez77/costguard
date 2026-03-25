import { useState, useEffect } from 'react'
import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react'
import { fetchWithDemo, api } from '../api'

const levelConfig = {
  critical: { icon: AlertTriangle, color: 'var(--red)', bg: 'var(--red-bg)', label: 'CRITICAL' },
  warning: { icon: AlertCircle, color: 'var(--yellow)', bg: 'var(--yellow-bg)', label: 'WARNING' },
  info: { icon: Info, color: 'var(--blue)', bg: 'var(--blue-bg)', label: 'INFO' },
}

const typeLabels = {
  cost_spike: 'Cost Spike',
  volume_spike: 'Volume Spike',
  budget_80: 'Budget 80%',
  budget_90: 'Budget 90%',
  budget_100: 'Budget Exceeded',
  circuit_open: 'Circuit Open',
  zombie_agent: 'Zombie Agent',
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Alerts() {
  const [data, setData] = useState(null)
  const [filter, setFilter] = useState('active')

  useEffect(() => {
    fetchWithDemo(() => api.alerts(), 'alerts').then(setData)
  }, [])

  if (!data) return <div className="page-header"><h1>Loading...</h1></div>

  const allAlerts = data.alerts || []
  const filtered = filter === 'active'
    ? allAlerts.filter(a => !a.resolved)
    : filter === 'resolved'
    ? allAlerts.filter(a => a.resolved)
    : allAlerts

  const criticalCount = allAlerts.filter(a => a.level === 'critical' && !a.resolved).length
  const warningCount = allAlerts.filter(a => a.level === 'warning' && !a.resolved).length

  return (
    <>
      <div className="page-header">
        <h1>Alerts</h1>
        <p>Real-time alerts for budget, cost spikes, and circuit breakers</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card" style={{ borderLeft: '3px solid var(--red)' }}>
          <div className="stat-label">Critical</div>
          <div className="stat-value" style={{ color: 'var(--red)' }}>{criticalCount}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid var(--yellow)' }}>
          <div className="stat-label">Warning</div>
          <div className="stat-value" style={{ color: 'var(--yellow)' }}>{warningCount}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid var(--green)' }}>
          <div className="stat-label">Resolved</div>
          <div className="stat-value" style={{ color: 'var(--green)' }}>{allAlerts.filter(a => a.resolved).length}</div>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <div className="period-selector">
          {['active', 'resolved', 'all'].map(f => (
            <button key={f} className={`period-btn ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Alert Feed ({filtered.length})</span>
        </div>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-dim)' }}>
            <CheckCircle size={40} style={{ marginBottom: 12, color: 'var(--green)' }} />
            <div>No alerts to show</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filtered.map(alert => {
              const config = levelConfig[alert.level] || levelConfig.info
              const Icon = config.icon
              return (
                <div key={alert.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                  padding: 14, borderRadius: 'var(--radius-sm)',
                  background: config.bg, border: `1px solid ${config.color}22`,
                }}>
                  <Icon size={18} style={{ color: config.color, marginTop: 2, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: config.color }}>{config.label}</span>
                        <span style={{ fontSize: 11, color: 'var(--text-dim)', background: 'var(--bg)', padding: '1px 6px', borderRadius: 4 }}>
                          {typeLabels[alert.alert_type] || alert.alert_type}
                        </span>
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{timeAgo(alert.created_at)}</span>
                    </div>
                    <div style={{ fontSize: 14, color: 'var(--text-bright)' }}>{alert.message}</div>
                    {alert.resolved && (
                      <span className="badge badge-green" style={{ marginTop: 6 }}>Resolved</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </>
  )
}
