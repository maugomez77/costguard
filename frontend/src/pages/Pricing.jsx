import { useState, useEffect } from 'react'
import { Check, Zap, Star, Building } from 'lucide-react'
import { fetchWithDemo, api } from '../api'

const planDetails = {
  starter: {
    icon: Zap,
    color: '#3b82f6',
    features: [
      'Up to 10 agents',
      '100K API calls/month',
      '2 webhook integrations',
      'Real-time cost dashboard',
      'Circuit breakers',
      'Email alerts',
    ],
  },
  pro: {
    icon: Star,
    color: '#a855f7',
    popular: true,
    features: [
      'Up to 50 agents',
      '1M API calls/month',
      '10 webhook integrations',
      'AI-powered predictions',
      'Zombie agent detection',
      'Cost optimization tips',
      'Slack & SMS alerts',
      'Team management',
    ],
  },
  business: {
    icon: Building,
    color: '#f97316',
    features: [
      'Unlimited agents',
      '10M API calls/month',
      '50 webhook integrations',
      'AI-powered predictions',
      'Custom compliance rules',
      'Priority support',
      'SSO & audit logs',
      'Dedicated account manager',
      'Custom integrations',
      'SLA guarantee',
    ],
  },
}

export default function Pricing() {
  const [plans, setPlans] = useState(null)

  useEffect(() => {
    fetchWithDemo(() => api.plans(), 'plans').then(setPlans)
  }, [])

  if (!plans) return <div className="page-header"><h1>Loading...</h1></div>

  return (
    <>
      <div className="page-header" style={{ textAlign: 'center', marginBottom: 40 }}>
        <h1>Simple, Transparent Pricing</h1>
        <p>Stop your AI agents from burning through your budget</p>
      </div>

      <div className="grid-3">
        {(plans.plans || []).map(plan => {
          const details = planDetails[plan.name] || planDetails.starter
          const Icon = details.icon
          return (
            <div
              key={plan.name}
              className="card"
              style={{
                position: 'relative',
                border: details.popular ? '2px solid var(--accent)' : undefined,
              }}
            >
              {details.popular && (
                <div style={{
                  position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)',
                  background: 'var(--accent)', color: 'white', padding: '3px 14px',
                  borderRadius: 100, fontSize: 11, fontWeight: 700,
                }}>
                  MOST POPULAR
                </div>
              )}
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12, margin: '0 auto 12px',
                  background: `${details.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Icon size={24} style={{ color: details.color }} />
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-bright)', textTransform: 'capitalize' }}>
                  {plan.name}
                </div>
                <div style={{ marginTop: 8 }}>
                  <span style={{ fontSize: 40, fontWeight: 800, color: 'var(--text-bright)' }}>${plan.price}</span>
                  <span style={{ fontSize: 14, color: 'var(--text-dim)' }}>/month</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
                {details.features.map(f => (
                  <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <Check size={16} style={{ color: 'var(--green)', flexShrink: 0 }} />
                    <span style={{ color: 'var(--text)' }}>{f}</span>
                  </div>
                ))}
              </div>

              <button
                className={details.popular ? 'btn btn-primary' : 'btn btn-outline'}
                style={{ width: '100%', justifyContent: 'center', padding: 12 }}
              >
                {details.popular ? 'Start Free Trial' : 'Get Started'}
              </button>
            </div>
          )
        })}
      </div>

      <div className="card" style={{ textAlign: 'center', marginTop: 24 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-bright)', marginBottom: 8 }}>
          5-Minute Integration
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-dim)', marginBottom: 16 }}>
          Add Cost Guard to any Python project with just 3 lines of code
        </div>
        <div style={{
          background: 'var(--bg)', borderRadius: 'var(--radius-sm)', padding: 20,
          textAlign: 'left', fontFamily: 'ui-monospace, monospace', fontSize: 13,
          color: 'var(--text)', lineHeight: 1.8, overflow: 'auto',
        }}>
          <div><span style={{ color: '#c084fc' }}>from</span> costguard.sdk <span style={{ color: '#c084fc' }}>import</span> CostGuard</div>
          <div style={{ color: 'var(--text-dim)' }}></div>
          <div>guard = CostGuard(api_key=<span style={{ color: '#22c55e' }}>"cg_..."</span>)</div>
          <div>guard.wrap_openai(client)  <span style={{ color: 'var(--text-dim)' }}># That's it!</span></div>
        </div>
      </div>
    </>
  )
}
