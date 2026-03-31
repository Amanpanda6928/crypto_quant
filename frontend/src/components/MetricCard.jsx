import { useState } from 'react'

export default function MetricCard({ icon, label, value, sub, color = '#8b5cf6', trend, positive, loading = false }) {
  const [hovered, setHovered] = useState(false)

  if (loading) {
    return (
      <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 18, padding: '22px 24px' }}>
        <div className="skeleton" style={{ height: 12, width: '60%', marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 28, width: '45%', marginBottom: 8 }} />
        <div className="skeleton" style={{ height: 10, width: '80%' }} />
      </div>
    )
  }

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? 'linear-gradient(145deg,rgba(36,47,69,0.9),rgba(20,30,55,0.95))' : 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))',
        border: `1px solid ${hovered ? `${color}33` : 'rgba(71,85,105,0.35)'}`,
        borderRadius: 18, padding: '22px 24px', backdropFilter: 'blur(24px)',
        boxShadow: hovered ? `0 6px 30px ${color}22, 0 2px 10px rgba(0,0,0,0.3)` : '0 2px 10px rgba(0,0,0,0.25)',
        transition: 'all 0.25s cubic-bezier(0.4,0,0.2,1)',
        transform: hovered ? 'translateY(-2px)' : 'none',
        position: 'relative', overflow: 'hidden',
      }}
    >
      <div style={{ position: 'absolute', top: -30, right: -30, width: 120, height: 120, borderRadius: '50%', background: `${color}18`, filter: 'blur(30px)', pointerEvents: 'none', transition: 'opacity 0.3s', opacity: hovered ? 1 : 0.5 }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.12em' }}>{label}</div>
        <div style={{ fontSize: 22, width: 38, height: 38, borderRadius: 10, background: `${color}18`, border: `1px solid ${color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{icon}</div>
      </div>
      <div style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 30, fontFamily: "'Space Mono',monospace", lineHeight: 1, marginBottom: 8, letterSpacing: '-0.02em' }}>{value}</div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {sub && <div style={{ color: '#64748b', fontSize: 12 }}>{sub}</div>}
        {trend && (
          <div style={{ fontSize: 12, fontWeight: 700, fontFamily: "'Space Mono',monospace", color: positive !== false ? '#34d399' : '#f87171', background: positive !== false ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${positive !== false ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'}`, borderRadius: 6, padding: '2px 8px' }}>{trend}</div>
        )}
      </div>
      <div style={{ height: 2, borderRadius: 1, marginTop: 18, background: `linear-gradient(90deg,${color},${color}00)` }} />
    </div>
  )
}
