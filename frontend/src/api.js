const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const apiKey = localStorage.getItem('cg_api_key') || 'cg_demo_costguard_2026'
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
      ...options.headers,
    },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  health: () => request('/health'),
  spend: (period = 'month') => request(`/v1/spend?period=${period}`),
  agents: () => request('/v1/agents'),
  agentDetail: (id) => request(`/v1/agents/${id}`),
  alerts: (resolved) =>
    request(`/v1/alerts${resolved !== undefined ? `?resolved=${resolved}` : ''}`),
  ingest: (data) => request('/v1/ingest', { method: 'POST', body: JSON.stringify(data) }),
  circuit: (agentId, action, reason) =>
    request(`/v1/agents/${agentId}/circuit`, {
      method: 'POST',
      body: JSON.stringify({ action, reason }),
    }),
  plans: () => request('/v1/billing/plans'),
  predict: () => request('/v1/predict'),
  zombies: () => request('/v1/zombies'),
  webhook: (config) => request('/v1/webhook', { method: 'PUT', body: JSON.stringify(config) }),
  rotateKey: () => request('/v1/rotate-key', { method: 'POST' }),
  createProject: (name, budget, hardLimit) =>
    request(`/v1/projects?name=${encodeURIComponent(name)}&budget_monthly=${budget}${hardLimit ? `&hard_limit=${hardLimit}` : ''}`, { method: 'POST' }),
}

// Demo data for when no backend is connected
export const demoData = {
  spend: {
    project_id: 'proj-demo-001',
    period: 'month',
    total_cost: 847.32,
    total_calls: 24531,
    burn_rate_daily: 33.89,
    by_provider: { openai: 412.50, anthropic: 318.20, google: 89.42, deepseek: 27.20 },
    by_model: {
      'gpt-4o': 285.30, 'claude-sonnet-4': 243.10, 'gpt-4o-mini': 127.20,
      'claude-haiku-3.5': 75.10, 'gemini-2.5-flash': 89.42, 'deepseek-v3': 27.20,
    },
    by_agent: {
      'agent-001': 312.40, 'agent-002': 198.50, 'agent-003': 156.30,
      'agent-004': 102.12, 'agent-005': 78.00,
    },
    budget_monthly: 1500,
    budget_pct: 56.5,
    projected_monthly: 1016.70,
  },
  agents: {
    agents: [
      { id: 'agent-001', name: 'research-agent', framework: 'langchain', providers: ['openai', 'anthropic'], circuit: 'closed', last_seen: '2026-03-25T14:30:00Z', created_at: '2026-03-01T10:00:00Z' },
      { id: 'agent-002', name: 'customer-support', framework: 'crewai', providers: ['openai'], circuit: 'closed', last_seen: '2026-03-25T14:28:00Z', created_at: '2026-03-05T08:00:00Z' },
      { id: 'agent-003', name: 'code-reviewer', framework: 'custom', providers: ['anthropic'], circuit: 'open', circuit_reason: 'Budget exceeded $500 limit', circuit_opened_at: '2026-03-25T12:00:00Z', last_seen: '2026-03-25T12:00:00Z', created_at: '2026-03-10T12:00:00Z' },
      { id: 'agent-004', name: 'data-analyst', framework: 'autogen', providers: ['openai', 'google'], circuit: 'closed', last_seen: '2026-03-25T14:25:00Z', created_at: '2026-03-12T09:00:00Z' },
      { id: 'agent-005', name: 'content-writer', framework: 'langchain', providers: ['anthropic'], circuit: 'closed', last_seen: '2026-03-25T14:20:00Z', created_at: '2026-03-15T11:00:00Z' },
    ],
  },
  alerts: {
    alerts: [
      { id: 'alert-001', alert_type: 'cost_spike', level: 'critical', message: 'Cost spike: $2.45/hr vs $0.82/hr avg (3.0x)', agent_id: 'agent-001', created_at: '2026-03-25T14:15:00Z', resolved: false },
      { id: 'alert-002', alert_type: 'budget_90', level: 'critical', message: 'Budget at 92.3% — approaching limit', agent_id: 'agent-003', created_at: '2026-03-25T11:30:00Z', resolved: false },
      { id: 'alert-003', alert_type: 'circuit_open', level: 'critical', message: 'Circuit OPEN for agent code-reviewer', agent_id: 'agent-003', created_at: '2026-03-25T12:00:00Z', resolved: false },
      { id: 'alert-004', alert_type: 'budget_80', level: 'warning', message: 'Budget at 82.1%', agent_id: 'agent-002', created_at: '2026-03-25T10:00:00Z', resolved: false },
      { id: 'alert-005', alert_type: 'volume_spike', level: 'warning', message: 'Volume spike: 450 calls/hr vs 85/hr avg (5.3x)', agent_id: 'agent-004', created_at: '2026-03-25T09:00:00Z', resolved: true },
    ],
  },
  plans: {
    plans: [
      { name: 'starter', price: 29, max_agents: 10, max_calls_monthly: 100000, predictions_enabled: false },
      { name: 'pro', price: 79, max_agents: 50, max_calls_monthly: 1000000, predictions_enabled: true },
      { name: 'business', price: 199, max_agents: 999999, max_calls_monthly: 10000000, predictions_enabled: true },
    ],
  },
}

// Try API first, fall back to demo data
export async function fetchWithDemo(apiCall, demoKey) {
  try {
    return await apiCall()
  } catch {
    return demoData[demoKey]
  }
}
