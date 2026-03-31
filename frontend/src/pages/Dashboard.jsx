import { useState, useEffect } from 'react'
import MetricCard from '../components/MetricCard'
import SignalCard from '../components/SignalCard'
import { fetchSuggestions, fetchMarketStatus, generateMockSignals } from '../services/api'
import { useAuth } from '../context/AuthContext'

function Badge({ label, variant }) {
  const map = {
    BULL: ['rgba(16,185,129,0.12)','rgba(16,185,129,0.3)','#34d399'],
    BEAR: ['rgba(239,68,68,0.12)','rgba(239,68,68,0.3)','#f87171'],
    LOW:  ['rgba(16,185,129,0.12)','rgba(16,185,129,0.3)','#34d399'],
    MEDIUM:['rgba(245,158,11,0.12)','rgba(245,158,11,0.3)','#fbbf24'],
    HIGH: ['rgba(239,68,68,0.12)','rgba(239,68,68,0.3)','#f87171'],
  }
  const [bg, bd, cl] = map[variant] || map.MEDIUM
  return <span style={{ background: bg, border: `1px solid ${bd}`, color: cl, borderRadius: 8, padding: '4px 12px', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: "'Space Mono',monospace" }}>{label}</span>
}

export default function Dashboard() {
  const { user } = useAuth()
  const [topSignals, setTopSignals] = useState([])
  const [market, setMarket]         = useState({ regime: 'BULL', volatility: 'MEDIUM', fearGreed: 68 })
  const [allSignals, setAllSignals] = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      const [suggestions, status] = await Promise.all([fetchSuggestions(), fetchMarketStatus()])
      setAllSignals(generateMockSignals())
      setTopSignals(suggestions)
      setMarket(status)
      setLoading(false)
    }
    load()
  }, [])

  const buyCount  = allSignals.filter(s => s.signal === 'BUY').length
  const sellCount = allSignals.filter(s => s.signal === 'SELL').length
  const holdCount = allSignals.filter(s => s.signal === 'HOLD').length
  const firstName = user?.name?.split(' ')[0] || 'Trader'

  return (
    <div style={{ animation: 'fadeUp 0.4s ease both' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32, paddingBottom: 22, borderBottom: '1px solid rgba(71,85,105,0.18)' }}>
        <div>
          <h1 style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 26, margin: '0 0 4px', fontFamily: "'Space Mono',monospace", letterSpacing: '-0.03em' }}>Good day, {firstName} 👋</h1>
          <p style={{ color: '#475569', fontSize: 13, margin: 0 }}>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Badge label={market.regime} variant={market.regime} />
          <Badge label={market.volatility} variant={market.volatility} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 12px', borderRadius: 20, background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#10b981', animation: 'pulseDot 2s infinite' }} />
            <span style={{ color: '#10b981', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', fontFamily: "'Space Mono',monospace" }}>LIVE</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 34 }}>
        <MetricCard loading={loading} icon="🐂" label="Market Regime"  value={market.regime}     sub="Current trend"         color="#10b981" />
        <MetricCard loading={loading} icon="⚡" label="Volatility"      value={market.volatility} sub={`Fear & Greed: ${market.fearGreed}`} color="#f59e0b" />
        <MetricCard loading={loading} icon="◈" label="Total Signals"   value={allSignals.length} sub={`${buyCount} BUY · ${sellCount} SELL · ${holdCount} HOLD`} color="#8b5cf6" />
        <MetricCard loading={loading} icon="🎯" label="High Confidence" value={allSignals.filter(s => s.confidence > 80).length} sub="Signals above 80%" color="#6366f1" />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <span style={{ fontSize: 20 }}>🔥</span>
        <h2 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 18, margin: 0, fontFamily: "'Space Mono',monospace" }}>Top Opportunities</h2>
        <span style={{ fontSize: 11, fontWeight: 700, color: '#a78bfa', background: 'rgba(139,92,246,0.12)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 6, padding: '2px 10px', fontFamily: "'Space Mono',monospace" }}>{topSignals.length} signals</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16, marginBottom: 34 }}>
        {loading
          ? Array(4).fill(0).map((_, i) => <div key={i} className="skeleton" style={{ height: 140, borderRadius: 18 }} />)
          : topSignals.map(s => <SignalCard key={s.id} signal={s} compact showDetails={false} />)
        }
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 18, padding: 26 }}>
          <h3 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14, margin: '0 0 20px', fontFamily: "'Space Mono',monospace" }}>Signal Breakdown</h3>
          {[ { label: 'BUY', color: '#10b981', count: buyCount }, { label: 'SELL', color: '#ef4444', count: sellCount }, { label: 'HOLD', color: '#f59e0b', count: holdCount }].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
              <span style={{ color: '#64748b', fontSize: 12, fontFamily: "'Space Mono',monospace", width: 36, flexShrink: 0 }}>{item.label}</span>
              <div style={{ flex: 1, height: 7, borderRadius: 4, background: 'rgba(15,23,42,0.7)', overflow: 'hidden' }}>
                <div style={{ width: `${allSignals.length ? (item.count / allSignals.length) * 100 : 0}%`, height: '100%', borderRadius: 4, background: item.color, transition: 'width 1s ease 0.3s' }} />
              </div>
              <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 800, fontFamily: "'Space Mono',monospace", width: 22, textAlign: 'right' }}>{item.count}</span>
            </div>
          ))}
        </div>
        <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 18, padding: 26 }}>
          <h3 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14, margin: '0 0 20px', fontFamily: "'Space Mono',monospace" }}>Live Metrics</h3>
          {[['Avg Confidence', `${Math.round(allSignals.reduce((a,s)=>a+s.confidence,0)/(allSignals.length||1))}%`],['Avg Probability',`${Math.round(allSignals.reduce((a,s)=>a+s.probability,0)/(allSignals.length||1))}%`],['BTC Dominance','52.4%'],['Fear & Greed',`${market.fearGreed} / 100`],['Coins Monitored',`${allSignals.length} / 30`],['Data Refresh','Every 5 min']].map(([l,v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '9px 0', borderBottom: '1px solid rgba(71,85,105,0.18)' }}>
              <span style={{ color: '#64748b', fontSize: 13 }}>{l}</span>
              <span style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 700, fontFamily: "'Space Mono',monospace" }}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
