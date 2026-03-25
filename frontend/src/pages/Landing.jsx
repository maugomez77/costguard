import { Link } from 'react-router-dom'
import { Shield, Zap, AlertTriangle, Activity, Bot, DollarSign, ArrowRight, Check } from 'lucide-react'

const features = [
  {
    icon: DollarSign,
    title: 'Real-Time Cost Tracking',
    desc: 'Monitor spend across OpenAI, Anthropic, Google, DeepSeek, and Groq in real-time. Know exactly where every dollar goes.',
  },
  {
    icon: Zap,
    title: 'Circuit Breakers',
    desc: 'Automatic shutdown when costs exceed your limits. Never wake up to a surprise $10K bill again.',
  },
  {
    icon: AlertTriangle,
    title: 'Instant Alerts',
    desc: 'Cost spikes, volume anomalies, and budget warnings delivered via webhook to Slack, Discord, or SMS.',
  },
  {
    icon: Bot,
    title: 'Zombie Detection',
    desc: 'Find agents stuck in loops burning money with no output. Automatically flag and kill runaway processes.',
  },
  {
    icon: Activity,
    title: 'AI Predictions',
    desc: 'Claude-powered cost forecasting predicts next month\'s spend and suggests optimizations.',
  },
  {
    icon: Shield,
    title: '5-Minute Setup',
    desc: 'Drop-in SDK wraps your OpenAI or Anthropic client. Pre-built integrations for LangChain, CrewAI, AutoGen.',
  },
]

export default function Landing() {
  return (
    <div style={{ width: '100%' }}>
      {/* Nav */}
      <nav style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '16px 40px', borderBottom: '1px solid var(--border)',
        maxWidth: 1200, margin: '0 auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Shield size={28} strokeWidth={2.5} style={{ color: 'var(--accent)' }} />
          <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-bright)' }}>Cost Guard</span>
        </div>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <Link to="/pricing" style={{ fontSize: 14, color: 'var(--text)' }}>Pricing</Link>
          <Link to="/dashboard" className="btn btn-primary" style={{ fontSize: 14 }}>
            Live Demo <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{
        maxWidth: 800, margin: '0 auto', padding: '100px 40px 80px', textAlign: 'center',
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          background: 'var(--red-bg)', color: 'var(--red)', padding: '6px 14px',
          borderRadius: 100, fontSize: 13, fontWeight: 600, marginBottom: 24,
        }}>
          <AlertTriangle size={14} />
          Stop your AI agents from burning through your budget
        </div>
        <h1 style={{
          fontSize: 52, fontWeight: 800, color: 'var(--text-bright)', lineHeight: 1.15,
          marginBottom: 20, letterSpacing: '-1px',
        }}>
          Real-Time Cost Monitoring for{' '}
          <span style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AI Agents
          </span>
        </h1>
        <p style={{ fontSize: 18, color: 'var(--text)', maxWidth: 560, margin: '0 auto 32px', lineHeight: 1.7 }}>
          Circuit breakers, budget enforcement, and cost spike alerts.
          Set up in 5 minutes. Never worry about runaway API costs again.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <Link to="/dashboard" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: 16 }}>
            Try Live Demo <ArrowRight size={16} />
          </Link>
          <Link to="/pricing" className="btn btn-outline" style={{ padding: '14px 28px', fontSize: 16 }}>
            View Pricing
          </Link>
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 12 }}>No signup required for demo</p>
      </section>

      {/* Code snippet */}
      <section style={{ maxWidth: 600, margin: '0 auto', padding: '0 40px 80px' }}>
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)',
          padding: 24, fontFamily: 'ui-monospace, monospace', fontSize: 14, lineHeight: 2,
        }}>
          <div style={{ color: 'var(--text-dim)', marginBottom: 4 }}># Install</div>
          <div style={{ color: 'var(--text-bright)' }}>pip install costguard</div>
          <div style={{ height: 16 }} />
          <div style={{ color: 'var(--text-dim)' }}># 3 lines to protect your budget</div>
          <div><span style={{ color: '#c084fc' }}>from</span> <span style={{ color: 'var(--text-bright)' }}>costguard.sdk</span> <span style={{ color: '#c084fc' }}>import</span> CostGuard</div>
          <div>guard = CostGuard(api_key=<span style={{ color: '#22c55e' }}>"cg_..."</span>)</div>
          <div>guard.wrap_openai(client)</div>
        </div>
      </section>

      {/* Features */}
      <section style={{ maxWidth: 1000, margin: '0 auto', padding: '0 40px 80px' }}>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: 'var(--text-bright)', textAlign: 'center', marginBottom: 48 }}>
          Everything you need to control AI costs
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card" style={{ padding: 24 }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: 'rgba(99, 102, 241, 0.1)', display: 'flex',
                alignItems: 'center', justifyContent: 'center', marginBottom: 14,
              }}>
                <Icon size={20} style={{ color: 'var(--accent)' }} />
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-bright)', marginBottom: 8 }}>{title}</div>
              <div style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.6 }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Social proof */}
      <section style={{
        maxWidth: 800, margin: '0 auto', padding: '40px', textAlign: 'center',
        borderTop: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 48, marginBottom: 40 }}>
          {[
            { val: '25+', label: 'AI Models Supported' },
            { val: '6', label: 'Providers' },
            { val: '<5min', label: 'Setup Time' },
            { val: '$29', label: 'Starting Price' },
          ].map(({ val, label }) => (
            <div key={label}>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-bright)' }}>{val}</div>
              <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{
        maxWidth: 600, margin: '0 auto 80px', padding: '48px 40px',
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', textAlign: 'center',
      }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-bright)', marginBottom: 12 }}>
          Ready to stop overpaying for AI?
        </h2>
        <p style={{ fontSize: 14, color: 'var(--text)', marginBottom: 24 }}>
          Start monitoring your AI costs in under 5 minutes.
        </p>
        <Link to="/dashboard" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: 16 }}>
          Try the Live Demo <ArrowRight size={16} />
        </Link>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border)', padding: '24px 40px',
        textAlign: 'center', fontSize: 13, color: 'var(--text-dim)',
      }}>
        Cost Guard &copy; 2026 &mdash; Real-time cost monitoring for AI agents
      </footer>
    </div>
  )
}
