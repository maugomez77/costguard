import { useState, useEffect } from 'react'
import { DollarSign, Activity, TrendingUp, AlertTriangle, Zap } from 'lucide-react'
import { fetchWithDemo, api } from '../api'

const COLORS = ['#6366f1', '#3b82f6', '#22c55e', '#eab308', '#f97316', '#a855f7', '#ef4444']

export default function Dashboard() {
  const [spend, setSpend] = useState(null)
  const [period, setPeriod] = useState('month')

  useEffect(() => {
    fetchWithDemo(() => api.spend(period), 'spend').then(setSpend)
  }, [period])

  if (!spend) return <div className="page-header"><h1>Loading...</h1></div>

  const budgetColor = spend.budget_pct < 60 ? 'var(--green)' : spend.budget_pct < 85 ? 'var(--yellow)' : 'var(--red)'
  const providers = Object.entries(spend.by_provider).sort((a, b) => b[1] - a[1])
  const models = Object.entries(spend.by_model).sort((a, b) => b[1] - a[1])
  const maxProviderCost = providers.length ? providers[0][1] : 1
  const maxModelCost = models.length ? models[0][1] : 1

  return (
    <>
      <div className="page-header">
        <h1>Cost Dashboard</h1>
        <p>Real-time spend monitoring across all your AI agents</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Spend</div>
          <div className="stat-value" style={{ color: budgetColor }}>${spend.total_cost.toFixed(2)}</div>
          <div className="stat-sub">of ${spend.budget_monthly.toFixed(0)} budget</div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${Math.min(spend.budget_pct, 100)}%`, background: budgetColor }} />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">API Calls</div>
          <div className="stat-value">{spend.total_calls.toLocaleString()}</div>
          <div className="stat-sub">this {period}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Burn Rate</div>
          <div className="stat-value">${spend.burn_rate_daily.toFixed(2)}</div>
          <div className="stat-sub">per day</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Projected Monthly</div>
          <div className="stat-value">${spend.projected_monthly.toFixed(0)}</div>
          <div className="stat-sub">
            {spend.projected_monthly > spend.budget_monthly
              ? <span style={{ color: 'var(--red)' }}>Over budget by ${(spend.projected_monthly - spend.budget_monthly).toFixed(0)}</span>
              : <span style={{ color: 'var(--green)' }}>${(spend.budget_monthly - spend.projected_monthly).toFixed(0)} under budget</span>
            }
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <div className="period-selector">
          {['today', 'week', 'month'].map(p => (
            <button key={p} className={`period-btn ${period === p ? 'active' : ''}`} onClick={() => setPeriod(p)}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Spend by Provider</span>
          </div>
          {providers.map(([name, cost], i) => (
            <div className="bar-row" key={name}>
              <span className="bar-label">{name}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{
                    width: `${(cost / maxProviderCost) * 100}%`,
                    background: COLORS[i % COLORS.length],
                  }}
                >
                  ${cost.toFixed(2)}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Spend by Model</span>
          </div>
          {models.map(([name, cost], i) => (
            <div className="bar-row" key={name}>
              <span className="bar-label">{name}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{
                    width: `${(cost / maxModelCost) * 100}%`,
                    background: COLORS[i % COLORS.length],
                  }}
                >
                  ${cost.toFixed(2)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Budget Overview</span>
          <span className="badge" style={{
            background: spend.budget_pct < 60 ? 'var(--green-bg)' : spend.budget_pct < 85 ? 'var(--yellow-bg)' : 'var(--red-bg)',
            color: budgetColor,
          }}>
            {spend.budget_pct.toFixed(1)}% used
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
          <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>$0</span>
          <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>${spend.budget_monthly.toFixed(0)}</span>
        </div>
        <div className="progress-bar" style={{ height: 20, borderRadius: 10 }}>
          <div className="progress-fill" style={{
            width: `${Math.min(spend.budget_pct, 100)}%`,
            background: `linear-gradient(90deg, var(--green), ${budgetColor})`,
            borderRadius: 10,
          }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 16, gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Spent</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-bright)' }}>${spend.total_cost.toFixed(2)}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Remaining</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-bright)' }}>${(spend.budget_monthly - spend.total_cost).toFixed(2)}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Projected</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: spend.projected_monthly > spend.budget_monthly ? 'var(--red)' : 'var(--green)' }}>
              ${spend.projected_monthly.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
