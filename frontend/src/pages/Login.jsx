import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, register } = useAuth()
  const [mode, setMode]       = useState('login')        // 'login' | 'register'
  const [name, setName]       = useState('')
  const [email, setEmail]     = useState('')
  const [pass, setPass]       = useState('')
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState(null)
  const [error, setError]     = useState('')

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!email.trim() || !pass.trim()) { setError('Please fill in all fields.'); return }
    if (mode === 'register' && !name.trim()) { setError('Please enter your name.'); return }
    setError(''); setLoading(true)
    try {
      if (mode === 'login') await login(email.trim(), pass)
      else                  await register(name.trim(), email.trim(), pass)
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = (field) => ({
    width: '100%', padding: '13px 16px', borderRadius: 13, boxSizing: 'border-box',
    background: 'rgba(10,15,30,0.7)',
    border: `1px solid ${focused === field ? 'rgba(139,92,246,0.6)' : 'rgba(71,85,105,0.4)'}`,
    color: '#f1f5f9', fontSize: 14, outline: 'none', transition: 'all 0.2s ease',
    fontFamily: "'DM Sans', sans-serif",
    boxShadow: focused === field ? '0 0 0 3px rgba(139,92,246,0.12)' : 'none',
  })

  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(ellipse 120% 80% at 50% -10%,rgba(139,92,246,0.14) 0%,#0a0f1e 55%),#060a14', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', padding: '20px' }}>
      <div style={{ position: 'absolute', top: '12%', left: '8%', width: 380, height: 380, borderRadius: '50%', background: 'rgba(99,102,241,0.05)', filter: 'blur(90px)', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', bottom: '15%', right: '6%', width: 320, height: 320, borderRadius: '50%', background: 'rgba(139,92,246,0.07)', filter: 'blur(70px)', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', backgroundImage: 'linear-gradient(rgba(139,92,246,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(139,92,246,0.04) 1px,transparent 1px)', backgroundSize: '60px 60px' }} />

      <div style={{ position: 'relative', zIndex: 10, background: 'linear-gradient(145deg,rgba(30,41,59,0.65),rgba(15,23,42,0.88))', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 26, padding: '48px 46px', width: '100%', maxWidth: 440, backdropFilter: 'blur(50px)', boxShadow: '0 40px 100px rgba(0,0,0,0.55)' }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ width: 60, height: 60, borderRadius: 18, margin: '0 auto 18px', background: 'linear-gradient(135deg,#8b5cf6,#6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, boxShadow: '0 10px 40px rgba(139,92,246,0.45)' }}>⬡</div>
          <h1 style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 26, margin: '0 0 6px', fontFamily: "'Space Mono', monospace", letterSpacing: '-0.02em' }}>NEXUS AI</h1>
          <p style={{ color: '#64748b', fontSize: 13, margin: 0 }}>Crypto trading intelligence platform</p>
        </div>

        {/* Mode tabs */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 28, background: 'rgba(15,23,42,0.6)', padding: 4, borderRadius: 12 }}>
          {[['login', 'Sign In'], ['register', 'Register']].map(([m, label]) => (
            <button key={m} onClick={() => { setMode(m); setError('') }} style={{ flex: 1, padding: '9px', borderRadius: 9, fontSize: 13, fontWeight: mode === m ? 700 : 400, cursor: 'pointer', background: mode === m ? 'linear-gradient(135deg,rgba(139,92,246,0.3),rgba(99,102,241,0.2))' : 'transparent', border: `1px solid ${mode === m ? 'rgba(139,92,246,0.4)' : 'transparent'}`, color: mode === m ? '#a78bfa' : '#64748b', transition: 'all 0.2s ease' }}>
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {mode === 'register' && (
            <div>
              <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 7, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Full Name</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Arjun Sharma" onFocus={() => setFocused('name')} onBlur={() => setFocused(null)} style={inputStyle('name')} />
            </div>
          )}
          <div>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 7, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Username / Email</label>
            <input type="text" value={email} onChange={e => setEmail(e.target.value)} placeholder="admin or user@example.com" onFocus={() => setFocused('email')} onBlur={() => setFocused(null)} style={inputStyle('email')} />
          </div>
          <div>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 7, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Password</label>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="••••••••••" onFocus={() => setFocused('pass')} onBlur={() => setFocused(null)} style={inputStyle('pass')} />
          </div>

          {error && (
            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '10px 14px', color: '#fca5a5', fontSize: 13 }}>
              {typeof error === 'object' ? (error.message || error.detail || JSON.stringify(error)) : String(error)}
            </div>
          )}

          <button type="submit" disabled={loading} style={{ width: '100%', padding: '15px', borderRadius: 13, marginTop: 4, background: loading ? 'rgba(139,92,246,0.35)' : 'linear-gradient(135deg,#8b5cf6,#6366f1)', border: 'none', color: '#fff', fontSize: 14, fontWeight: 800, cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.2s ease', boxShadow: loading ? 'none' : '0 10px 35px rgba(139,92,246,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, fontFamily: "'Space Mono', monospace", letterSpacing: '0.08em' }}>
            {loading
              ? <><div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />{mode === 'login' ? 'AUTHENTICATING…' : 'CREATING ACCOUNT…'}</>
              : mode === 'login' ? 'SIGN IN →' : 'CREATE ACCOUNT →'
            }
          </button>
        </form>

        {/* Backend info */}
        <div style={{ marginTop: 24, padding: '12px 14px', background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.15)', borderRadius: 12 }}>
          <div style={{ color: '#8b5cf6', fontSize: 10, fontWeight: 700, marginBottom: 4, letterSpacing: '0.1em', textTransform: 'uppercase' }}>FastAPI Backend</div>
          <div style={{ color: '#64748b', fontSize: 11, lineHeight: 1.6 }}>
            Connects to <span style={{ color: '#a78bfa', fontFamily: "'Space Mono',monospace" }}>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
