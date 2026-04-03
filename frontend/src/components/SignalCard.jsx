import { useState } from 'react'

const SIGNAL_CONFIG = {
  BUY:  { glow:'rgba(16,185,129,0.22)',  border:'rgba(16,185,129,0.4)',  badgeBg:'rgba(16,185,129,0.15)',  badgeText:'#34d399', badgeBorder:'rgba(16,185,129,0.4)',  iconBg:'rgba(16,185,129,0.12)',  label:'BUY 🟢',  barColor:'#10b981' },
  SELL: { glow:'rgba(239,68,68,0.22)',   border:'rgba(239,68,68,0.4)',   badgeBg:'rgba(239,68,68,0.15)',   badgeText:'#f87171', badgeBorder:'rgba(239,68,68,0.4)',   iconBg:'rgba(239,68,68,0.12)',   label:'SELL 🔴', barColor:'#ef4444' },
  HOLD: { glow:'rgba(245,158,11,0.15)',  border:'rgba(245,158,11,0.35)', badgeBg:'rgba(245,158,11,0.12)',  badgeText:'#fbbf24', badgeBorder:'rgba(245,158,11,0.3)',  iconBg:'rgba(245,158,11,0.1)',   label:'HOLD 🟡', barColor:'#f59e0b' },
}

function timeAgo(iso) {
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago` 
  return `${Math.floor(mins / 60)}h ago` 
}

export default function SignalCard({ signal, compact = false, showDetails = true, timeframe = '1h' }) {
  const [hovered, setHovered] = useState(false)
  const cfg = SIGNAL_CONFIG[signal.signal] || SIGNAL_CONFIG.HOLD

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? 'linear-gradient(145deg,rgba(30,41,59,0.95),rgba(15,23,42,0.98))' : 'linear-gradient(145deg,rgba(30,41,59,0.75),rgba(15,23,42,0.88))',
        border: `1px solid ${hovered ? cfg.border : 'rgba(71,85,105,0.35)'}`,
        borderRadius: 18, padding: compact ? '14px 16px' : '20px 22px',
        backdropFilter: 'blur(24px)',
        boxShadow: hovered ? `0 8px 40px ${cfg.glow}, 0 2px 8px rgba(0,0,0,0.35)` : '0 2px 12px rgba(0,0,0,0.28)',
        transition: 'all 0.28s cubic-bezier(0.4,0,0.2,1)',
        transform: hovered ? 'translateY(-3px)' : 'none',
        cursor: 'pointer', position: 'relative', overflow: 'hidden',
      }}
    >
      <div style={{ position: 'absolute', top: -20, right: -20, width: 100, height: 100, borderRadius: '50%', background: cfg.glow, filter: 'blur(40px)', pointerEvents: 'none', opacity: hovered ? 1 : 0.4, transition: 'opacity 0.3s' }} />

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: compact ? 10 : 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 42, height: 42, borderRadius: 12, flexShrink: 0, background: `linear-gradient(135deg,${cfg.iconBg},rgba(15,23,42,0.9))`, border: `1px solid ${cfg.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800, color: cfg.badgeText, fontFamily: "'Space Mono',monospace" }}>
            {signal.coin.slice(0, 4)}
          </div>
          <div>
            <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: compact ? 14 : 15, fontFamily: "'Space Mono',monospace", lineHeight: 1.2 }}>{signal.coin}</div>
            <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>{signal.name}</div>
          </div>
        </div>
        <span style={{ background: cfg.badgeBg, border: `1px solid ${cfg.badgeBorder}`, color: cfg.badgeText, borderRadius: 9, padding: compact ? '3px 9px' : '4px 11px', fontSize: 11, fontWeight: 800, letterSpacing: '0.06em', fontFamily: "'Space Mono',monospace", flexShrink: 0 }}>
          {cfg.label}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: showDetails && !compact ? 16 : 0 }}>
        {[['Probability', signal.probability], ['Confidence', signal.confidence]].map(([label, value]) => (
          <div key={label} style={{ background: 'rgba(15,23,42,0.55)', borderRadius: 10, padding: '8px 12px' }}>
            <div style={{ color: '#64748b', fontSize: 10, marginBottom: 3, textTransform: 'uppercase', letterSpacing: '0.1em' }}>{label}</div>
            <div style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 18, fontFamily: "'Space Mono',monospace", lineHeight: 1 }}>{value}%</div>
            <div style={{ height: 2, background: 'rgba(71,85,105,0.4)', borderRadius: 1, marginTop: 6 }}>
              <div style={{ width: `${value}%`, height: '100%', borderRadius: 1, background: cfg.barColor }} />
            </div>
          </div>
        ))}
      </div>

      {showDetails && !compact && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {[['⚡', 'Momentum', signal.momentum], ['📈', 'Trend', signal.trend], ['📊', 'Volume', signal.volume]].map(([icon, label, text]) => (
            <div key={label} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', padding: '6px 10px', borderRadius: 8, background: 'rgba(15,23,42,0.4)' }}>
              <span style={{ fontSize: 12, flexShrink: 0, marginTop: 1 }}>{icon}</span>
              <div>
                <span style={{ color: '#64748b', fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginRight: 6 }}>{label}</span>
                <span style={{ color: '#94a3b8', fontSize: 11, lineHeight: 1.5 }}>{text}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI Future Prediction */}
      {signal.prediction && (
        <div style={{ 
          marginTop: showDetails && !compact ? 12 : 8,
          padding: '10px 12px', 
          borderRadius: 10, 
          background: 'rgba(167,139,250,0.08)', 
          border: '1px solid rgba(167,139,250,0.25)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#a78bfa', animation: 'pulse 1.5s infinite' }} />
            <span style={{ color: '#a78bfa', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              🤖 AI Prediction ({timeframe})
            </span>
            <span style={{ color: '#64748b', fontSize: 9, marginLeft: 'auto' }}>
              {signal.prediction.confidence}% confidence
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 700, fontFamily: "'Space Mono',monospace" }}>
              ${signal.prediction.target_price?.toFixed(2) || '—'}
            </span>
            <span style={{ 
              color: signal.prediction.predicted_change >= 0 ? '#34d399' : '#f87171', 
              fontSize: 11, 
              fontWeight: 700,
              background: signal.prediction.predicted_change >= 0 ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
              padding: '2px 6px',
              borderRadius: 4
            }}>
              {signal.prediction.predicted_change >= 0 ? '▲' : '▼'} {Math.abs(signal.prediction.predicted_change || 0).toFixed(2)}%
            </span>
          </div>
        </div>
      )}

      {signal.timestamp && (
        <div style={{ color: '#475569', fontSize: 10, marginTop: compact ? 8 : 12, fontFamily: "'Space Mono',monospace" }}>
          {timeAgo(signal.timestamp)}
        </div>
      )}
    </div>
  )
}
