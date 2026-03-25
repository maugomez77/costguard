import { useState, useEffect } from 'react'
import { Bot, CircleOff, Circle, Clock, Cpu } from 'lucide-react'
import { fetchWithDemo, api } from '../api'

function CircuitBadge({ state }) {
  if (state === 'open') return <span className="badge badge-red">OPEN</span>
  if (state === 'half_open') return <span className="badge badge-yellow">HALF-OPEN</span>
  return <span className="badge badge-green">CLOSED</span>
}

function timeAgo(dateStr) {
  if (!dateStr) return 'Never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Agents() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetchWithDemo(() => api.agents(), 'agents').then(setData)
  }, [])

  if (!data) return <div className="page-header"><h1>Loading...</h1></div>

  const agents = data.agents || []
  const openCircuits = agents.filter(a => a.circuit === 'open')
  const totalAgents = agents.length
  const activeAgents = agents.filter(a => {
    if (!a.last_seen) return false
    return Date.now() - new Date(a.last_seen).getTime() < 3600000
  }).length

  return (
    <>
      <div className="page-header">
        <h1>Agents</h1>
        <p>Monitor your AI agents and circuit breaker status</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Agents</div>
          <div className="stat-value">{totalAgents}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active (1hr)</div>
          <div className="stat-value" style={{ color: 'var(--green)' }}>{activeAgents}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Circuits Open</div>
          <div className="stat-value" style={{ color: openCircuits.length > 0 ? 'var(--red)' : 'var(--green)' }}>
            {openCircuits.length}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Agent Fleet</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Framework</th>
                <th>Providers</th>
                <th>Circuit</th>
                <th>Last Seen</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents.map(agent => (
                <tr key={agent.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Bot size={16} style={{ color: 'var(--accent)' }} />
                      <div>
                        <div style={{ color: 'var(--text-bright)', fontWeight: 600, fontSize: 14 }}>{agent.name}</div>
                        <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{agent.id}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-blue">{agent.framework}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {(agent.providers || []).map(p => (
                        <span key={p} style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 4,
                          background: 'var(--bg)', color: 'var(--text-dim)',
                        }}>
                          {p}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td>
                    <CircuitBadge state={agent.circuit} />
                    {agent.circuit_reason && (
                      <div style={{ fontSize: 11, color: 'var(--red)', marginTop: 4 }}>{agent.circuit_reason}</div>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}>
                      <Clock size={12} />
                      {timeAgo(agent.last_seen)}
                    </div>
                  </td>
                  <td>
                    {agent.circuit === 'open' ? (
                      <button className="btn btn-outline" style={{ fontSize: 12, padding: '4px 10px' }}>
                        Reset Circuit
                      </button>
                    ) : (
                      <button className="btn btn-danger" style={{ fontSize: 12, padding: '4px 10px' }}>
                        Open Circuit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {openCircuits.length > 0 && (
        <div className="card" style={{ marginTop: 16, borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <div className="card-header">
            <span className="card-title" style={{ color: 'var(--red)' }}>Open Circuit Breakers</span>
          </div>
          {openCircuits.map(agent => (
            <div key={agent.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 0', borderBottom: '1px solid var(--border)',
            }}>
              <div>
                <div style={{ color: 'var(--text-bright)', fontWeight: 600 }}>{agent.name}</div>
                <div style={{ color: 'var(--red)', fontSize: 13 }}>{agent.circuit_reason}</div>
                <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>Opened {timeAgo(agent.circuit_opened_at)}</div>
              </div>
              <button className="btn btn-primary" style={{ fontSize: 12 }}>Close Circuit</button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
