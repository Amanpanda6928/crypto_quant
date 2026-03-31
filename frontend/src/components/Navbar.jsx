import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard',    icon: '⬡' },
  { path: '/trading',   label: 'Live Trading', icon: '⚡', badge: 'LIVE' },
  { path: '/signals',   label: 'Signals',      icon: '◈' },
  { path: '/portfolio', label: 'Portfolio',    icon: '◎' },
  { path: '/analytics', label: 'Analytics',    icon: '◑' },
]
const ADMIN_ITEM = { path: '/admin', label: 'Admin', icon: '⚙' }

const PLAN_COLORS = {
  ELITE: { bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.3)',  text: '#fbbf24' },
  PRO:   { bg: 'rgba(139,92,246,0.12)', border: 'rgba(139,92,246,0.3)', text: '#a78bfa' },
  FREE:  { bg: 'rgba(100,116,139,0.12)',border: 'rgba(100,116,139,0.3)',text: '#94a3b8' },
}

function NavItem({ item, active, onClick }) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 14px', borderRadius: 12,
        background: active ? 'linear-gradient(135deg,rgba(139,92,246,0.18),rgba(99,102,241,0.08))' : hovered ? 'rgba(139,92,246,0.06)' : 'transparent',
        border: `1px solid ${active ? 'rgba(139,92,246,0.3)' : 'transparent'}`,
        color: active ? '#a78bfa' : hovered ? '#94a3b8' : '#64748b',
        cursor: 'pointer', width: '100%', textAlign: 'left',
        transition: 'all 0.18s ease', fontSize: 13.5,
        fontWeight: active ? 600 : 400,
      }}
    >
      <span style={{ fontSize: 15, opacity: active ? 1 : 0.65, width: 18, textAlign: 'center', flexShrink: 0 }}>
        {item.icon}
      </span>
      <span style={{ flex: 1 }}>{item.label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {item.badge && (
          <span style={{
            fontSize: 8, fontWeight: 800, letterSpacing: '0.1em',
            color: '#10b981', background: 'rgba(16,185,129,0.12)',
            border: '1px solid rgba(16,185,129,0.3)',
            borderRadius: 4, padding: '1px 5px',
            fontFamily: "'Space Mono', monospace",
          }}>{item.badge}</span>
        )}
        {active && <div style={{ width: 5, height: 5, borderRadius: '50%', background: '#8b5cf6', boxShadow: '0 0 6px #8b5cf6' }} />}
      </div>
    </button>
  )
}

export default function Navbar() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [logoutHovered, setLogoutHovered] = useState(false)

  const items = isAdmin ? [...NAV_ITEMS, ADMIN_ITEM] : NAV_ITEMS
  const plan = user?.plan || 'FREE'
  const planStyle = PLAN_COLORS[plan] || PLAN_COLORS.FREE
  const initials = user?.name ? user.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'U'

  return (
    <aside style={{
      width: 240, minHeight: '100vh', position: 'fixed', left: 0, top: 0, zIndex: 200,
      background: 'linear-gradient(180deg,rgba(10,15,30,0.98) 0%,rgba(6,10,20,0.99) 100%)',
      borderRight: '1px solid rgba(71,85,105,0.2)', backdropFilter: 'blur(40px)',
      display: 'flex', flexDirection: 'column', padding: '24px 14px',
    }}>
      <div style={{ paddingLeft: 8, marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }} onClick={() => navigate('/dashboard')}>
          <div style={{ width: 38, height: 38, borderRadius: 11, background: 'linear-gradient(135deg,#8b5cf6,#6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, boxShadow: '0 4px 20px rgba(139,92,246,0.45)', flexShrink: 0 }}>⬡</div>
          <div>
            <div style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 15, fontFamily: "'Space Mono',monospace", lineHeight: 1 }}>NEXUS</div>
            <div style={{ color: '#8b5cf6', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', marginTop: 3 }}>AI TRADING</div>
          </div>
        </div>
      </div>

      <div style={{ color: '#475569', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', paddingLeft: 12, marginBottom: 8 }}>Main Menu</div>

      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
        {items.map(item => (
          <NavItem key={item.path} item={item} active={pathname === item.path} onClick={() => navigate(item.path)} />
        ))}
        <div style={{ height: 1, background: 'rgba(71,85,105,0.2)', margin: '12px 8px' }} />
        <div style={{ padding: '10px 12px', borderRadius: 12, background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.12)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ color: '#64748b', fontSize: 11 }}>Market</span>
            <span style={{ color: '#34d399', fontSize: 11, fontWeight: 700, fontFamily: "'Space Mono',monospace" }}>BULL 🐂</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#64748b', fontSize: 11 }}>Volatility</span>
            <span style={{ color: '#fbbf24', fontSize: 11, fontWeight: 700, fontFamily: "'Space Mono',monospace" }}>MEDIUM ⚡</span>
          </div>
        </div>
      </nav>

      <div style={{ borderTop: '1px solid rgba(71,85,105,0.2)', paddingTop: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', marginBottom: 10, borderRadius: 12, background: 'rgba(15,23,42,0.5)' }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', flexShrink: 0, background: 'linear-gradient(135deg,#8b5cf6,#6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800, color: '#fff', fontFamily: "'Space Mono',monospace", boxShadow: '0 2px 10px rgba(139,92,246,0.3)' }}>{initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.name || 'User'}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 2 }}>
              <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: planStyle.text, background: planStyle.bg, border: `1px solid ${planStyle.border}`, borderRadius: 5, padding: '1px 6px', fontFamily: "'Space Mono',monospace" }}>{plan}</span>
              {isAdmin && <span style={{ fontSize: 10, color: '#f59e0b' }}>ADMIN</span>}
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          onMouseEnter={() => setLogoutHovered(true)}
          onMouseLeave={() => setLogoutHovered(false)}
          style={{ width: '100%', padding: '9px 14px', borderRadius: 11, background: logoutHovered ? 'rgba(239,68,68,0.12)' : 'rgba(239,68,68,0.06)', border: `1px solid ${logoutHovered ? 'rgba(239,68,68,0.35)' : 'rgba(239,68,68,0.18)'}`, color: logoutHovered ? '#fca5a5' : '#f87171', cursor: 'pointer', fontSize: 13, fontWeight: 500, transition: 'all 0.2s ease', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
        >
          <span style={{ fontSize: 14 }}>⎋</span> Sign Out
        </button>
      </div>
    </aside>
  )
}
