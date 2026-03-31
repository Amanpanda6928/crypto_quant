import { useState, useEffect, useMemo } from 'react'
import SignalCard from '../components/SignalCard'
import { fetchSignalsBatch, ALL_COINS } from '../services/api'

const TIMEFRAMES = [
  { value: '15m', label: '15m', desc: 'Short' },
  { value: '30m', label: '30m', desc: 'Medium' },
  { value: '1h', label: '1h', desc: 'Balanced' },
  { value: '4h', label: '4h', desc: 'Low Noise' },
  { value: '1d', label: '1d', desc: 'High Acc' }
]

export default function Signals() {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [signalFilter, setSignalFilter] = useState('ALL')
  const [timeframe, setTimeframe] = useState('1h')
  const [minConf, setMinConf] = useState(0)
  const [sortBy, setSortBy] = useState('confidence')
  const [searchQ, setSearchQ] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  // Fetch live signals on mount and every 15 minutes
  useEffect(() => {
    const loadSignals = async () => {
      setLoading(true)
      try {
        // Add USDT suffix for API
        const symbols = ALL_COINS.map(c => c.symbol + 'USDT')
        const data = await fetchSignalsBatch(symbols, timeframe)
        console.log('Fetched signals:', data)
        
        if (!data || data.length === 0) {
          console.warn('No signals returned from API')
          setSignals([])
        } else {
          // Transform to match SignalCard expected format with timeframe-specific data
          const formatted = data.map(s => {
            // Get prediction for selected timeframe
            const tf = timeframe
            const predictionKey = `prediction_${tf}`
            const prediction = s[predictionKey] || s.prediction_1h || {}
            
            return {
              id: s.symbol,
              coin: s.symbol.replace('USDT', ''),
              name: ALL_COINS.find(c => c.symbol === s.symbol.replace('USDT', ''))?.name || s.symbol,
              signal: prediction.signal || s.signal,
              probability: prediction.confidence || s.confidence,
              confidence: prediction.confidence || s.confidence,
              momentum: s.live_data ? `${s.live_data.price_change_24h > 0 ? '+' : ''}${s.live_data.price_change_24h}%` : null,
              trend: prediction.target_price ? `Target: $${prediction.target_price}` : null,
              predictedChange: prediction.predicted_change,
              volume: s.live_data ? `Vol: $${(s.live_data.volume_24h / 1e6).toFixed(2)}M` : null,
              timestamp: s.timestamp,
              live_data: s.live_data,
              prediction: prediction,
              timeframe: tf
            }
          })
          setSignals(formatted)
        }
      } catch (error) {
        console.error('Failed to load signals:', error)
        setSignals([])
      } finally {
        setLastUpdated(new Date())
        setLoading(false)
      }
    }
    
    loadSignals()
    const interval = setInterval(loadSignals, 24 * 60 * 60 * 1000) // Refresh every 1 day
    return () => clearInterval(interval)
  }, [timeframe])

  const filtered = useMemo(() => {
    let r = [...signals]
    if (signalFilter !== 'ALL') r = r.filter(s => s.signal === signalFilter)
    if (minConf > 0) r = r.filter(s => s.confidence >= minConf)
    if (searchQ.trim()) { const q = searchQ.toLowerCase(); r = r.filter(s => s.coin.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)) }
    r.sort((a, b) => sortBy === 'coin' ? a.coin.localeCompare(b.coin) : b[sortBy] - a[sortBy])
    return r
  }, [signals, signalFilter, minConf, searchQ, sortBy])

  const counts = useMemo(() => ({ BUY: signals.filter(s=>s.signal==='BUY').length, SELL: signals.filter(s=>s.signal==='SELL').length, HOLD: signals.filter(s=>s.signal==='HOLD').length }), [signals])
  const labelStyle = { color: '#64748b', fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.1em' }

  return (
    <div style={{ animation: 'fadeUp 0.4s ease both' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 30, paddingBottom: 22, borderBottom: '1px solid rgba(71,85,105,0.18)' }}>
        <div>
          <h1 style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 26, margin: '0 0 4px', fontFamily: "'Space Mono',monospace", letterSpacing: '-0.03em' }}>Signal Feed</h1>
          <p style={{ color: '#475569', fontSize: 13, margin: 0 }}>
            AI-generated trading signals across 20 cryptocurrencies
            {lastUpdated && <span style={{ color: '#10b981', marginLeft: 8 }}>● Live</span>}
          </p>
          {lastUpdated && (
            <p style={{ color: '#64748b', fontSize: 11, margin: '4px 0 0' }}>
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {[['BUY','#10b981','rgba(16,185,129,0.1)','rgba(16,185,129,0.25)'],['SELL','#f87171','rgba(239,68,68,0.1)','rgba(239,68,68,0.25)'],['HOLD','#fbbf24','rgba(245,158,11,0.1)','rgba(245,158,11,0.25)']].map(([s,c,bg,bd]) => (
            <div key={s} style={{ background: bg, border: `1px solid ${bd}`, borderRadius: 10, padding: '6px 14px', textAlign: 'center' }}>
              <div style={{ color: c, fontWeight: 800, fontSize: 16, fontFamily: "'Space Mono',monospace", lineHeight: 1 }}>{counts[s]}</div>
              <div style={{ color: c, fontSize: 10, opacity: 0.7, letterSpacing: '0.08em' }}>{s}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '230px 1fr', gap: 24 }}>
        <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 16, padding: 20, position: 'sticky', top: 24, height: 'fit-content' }}>
          <h3 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 12, margin: '0 0 20px', fontFamily: "'Space Mono',monospace", letterSpacing: '0.12em', textTransform: 'uppercase' }}>⬡ Filters</h3>

          <div style={{ marginBottom: 22 }}>
            <label style={labelStyle}>Search Coin</label>
            <input type="text" value={searchQ} onChange={e => setSearchQ(e.target.value)} placeholder="BTC, Ethereum…" style={{ width: '100%', padding: '9px 12px', borderRadius: 10, boxSizing: 'border-box', background: 'rgba(10,15,30,0.7)', border: '1px solid rgba(71,85,105,0.4)', color: '#f1f5f9', fontSize: 13, outline: 'none', fontFamily: 'inherit' }} />
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={labelStyle}>Signal Type</label>
            {['ALL','BUY','SELL','HOLD'].map(t => (
              <button key={t} onClick={() => setSignalFilter(t)} style={{ width: '100%', padding: '8px 12px', borderRadius: 10, marginBottom: 5, textAlign: 'left', background: signalFilter===t?'rgba(139,92,246,0.15)':'transparent', border: `1px solid ${signalFilter===t?'rgba(139,92,246,0.4)':'rgba(71,85,105,0.3)'}`, color: signalFilter===t?'#a78bfa':'#64748b', cursor: 'pointer', fontSize: 13, fontWeight: signalFilter===t?700:400, transition: 'all 0.15s ease' }}>
                {t==='ALL'?'⬡ All Signals':t==='BUY'?'🟢 BUY':t==='SELL'?'🔴 SELL':'🟡 HOLD'}
              </button>
            ))}
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={{ ...labelStyle, display: 'flex', justifyContent: 'space-between' }}>
              <span>Min Confidence</span>
              <span style={{ color: '#a78bfa', fontFamily: "'Space Mono',monospace" }}>{minConf}%</span>
            </label>
            <input type="range" min={0} max={95} step={5} value={minConf} onChange={e => setMinConf(+e.target.value)} />
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={labelStyle}>Timeframe</label>
            <select 
              value={timeframe} 
              onChange={(e) => setTimeframe(e.target.value)}
              style={{ width: '100%', padding: '9px 12px', borderRadius: 10, background: 'rgba(10,15,30,0.8)', border: '1px solid rgba(71,85,105,0.4)', color: '#f1f5f9', fontSize: 13, cursor: 'pointer', outline: 'none', fontFamily: 'inherit' }}
            >
              {TIMEFRAMES.map(tf => (
                <option key={tf.value} value={tf.value}>{tf.label} - {tf.desc}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={labelStyle}>Sort By</label>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{ width: '100%', padding: '9px 12px', borderRadius: 10, background: 'rgba(10,15,30,0.8)', border: '1px solid rgba(71,85,105,0.4)', color: '#f1f5f9', fontSize: 13, cursor: 'pointer', outline: 'none', fontFamily: 'inherit' }}>
              <option value="confidence">Confidence</option>
              <option value="probability">Probability</option>
              <option value="coin">Coin Name</option>
            </select>
          </div>

          <div style={{ padding: 12, borderRadius: 12, background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.15)', textAlign: 'center' }}>
            <div style={{ color: '#a78bfa', fontWeight: 800, fontSize: 24, fontFamily: "'Space Mono',monospace" }}>{filtered.length}</div>
            <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>signals found</div>
          </div>
          {(signalFilter !== 'ALL' || minConf > 0 || searchQ || timeframe !== '1h') && (
            <button onClick={() => { setSignalFilter('ALL'); setMinConf(0); setSearchQ(''); setTimeframe('1h') }} style={{ width: '100%', marginTop: 10, padding: 8, borderRadius: 10, background: 'transparent', border: '1px solid rgba(71,85,105,0.3)', color: '#64748b', cursor: 'pointer', fontSize: 12, transition: 'all 0.15s ease' }}>↺ Reset Filters</button>
          )}
        </div>

        <div>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {Array(6).fill(0).map((_,i) => <div key={i} className="skeleton" style={{ height: 220, borderRadius: 18 }} />)}
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '80px 20px', color: '#475569' }}>
              <div style={{ fontSize: 48, marginBottom: 14, opacity: 0.4 }}>◎</div>
              <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>No signals match</div>
              <div style={{ fontSize: 14 }}>Try adjusting your filters</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {filtered.map((s, i) => (
                <div key={s.id} style={{ animation: `fadeUp 0.35s ease ${i * 0.04}s both` }}>
                  <SignalCard signal={s} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
