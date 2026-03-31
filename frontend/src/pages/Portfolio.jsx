import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { ALL_COINS, fetchPortfolio, savePortfolio, generateMockSignals } from '../services/api'

const SIG_CFG = {
  BUY:  { color: '#34d399', border: 'rgba(16,185,129,0.4)', bg: 'rgba(16,185,129,0.12)' },
  SELL: { color: '#f87171', border: 'rgba(239,68,68,0.4)',  bg: 'rgba(239,68,68,0.12)'  },
  HOLD: { color: '#fbbf24', border: 'rgba(245,158,11,0.35)',bg: 'rgba(245,158,11,0.1)'  },
}

export default function Portfolio() {
  const [selected, setSelected] = useState([])
  const [saved, setSaved]       = useState([])
  const [signals, setSignals]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)

  useEffect(() => {
    async function load() {
      const [portfolio, sigs] = await Promise.all([fetchPortfolio(), Promise.resolve(generateMockSignals())])
      setSelected(portfolio.coins || [])
      setSaved(portfolio.coins || [])
      setSignals(sigs)
      setLoading(false)
    }
    load()
  }, [])

  const toggle = sym => setSelected(p => p.includes(sym) ? p.filter(s => s !== sym) : [...p, sym])

  const handleSave = async () => {
    setSaving(true)
    try { await savePortfolio(selected); setSaved([...selected]); toast.success(`Portfolio saved! Tracking ${selected.length} coins.`) }
    catch { toast.error('Failed to save portfolio.') }
    finally { setSaving(false) }
  }

  const getSignal = sym => signals.find(s => s.coin === sym)

  return (
    <div style={{ animation: 'fadeUp 0.4s ease both' }}>
      <div style={{ marginBottom: 32, paddingBottom: 22, borderBottom: '1px solid rgba(71,85,105,0.18)' }}>
        <h1 style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 26, margin: '0 0 4px', fontFamily: "'Space Mono',monospace", letterSpacing: '-0.03em' }}>Portfolio</h1>
        <p style={{ color: '#475569', fontSize: 13, margin: 0 }}>Select coins to monitor and receive AI signals for</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 28 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
            <h2 style={{ color: '#94a3b8', fontSize: 12, fontWeight: 700, margin: 0, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Select Coins</h2>
            <span style={{ color: '#a78bfa', fontSize: 12, fontFamily: "'Space Mono',monospace" }}>{selected.length} / {ALL_COINS.length}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 20 }}>
            {ALL_COINS.map(coin => {
              const isSel = selected.includes(coin.symbol)
              const sig   = getSignal(coin.symbol)
              return (
                <button key={coin.symbol} onClick={() => toggle(coin.symbol)} title={coin.name} style={{ padding: '10px 8px', borderRadius: 12, cursor: 'pointer', background: isSel?'rgba(139,92,246,0.14)':'rgba(15,23,42,0.6)', border: `1px solid ${isSel?'rgba(139,92,246,0.45)':'rgba(71,85,105,0.3)'}`, transition: 'all 0.18s ease', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: coin.color }} />
                  <span style={{ color: isSel?'#a78bfa':'#64748b', fontFamily: "'Space Mono',monospace", fontWeight: 700, fontSize: 11 }}>{coin.symbol}</span>
                  {sig && <span style={{ fontSize: 9, fontWeight: 700, color: sig.signal==='BUY'?'#34d399':sig.signal==='SELL'?'#f87171':'#fbbf24' }}>{sig.signal}</span>}
                  {isSel && <span style={{ fontSize: 10, color: '#a78bfa' }}>✓</span>}
                </button>
              )
            })}
          </div>
          <div style={{ display: 'flex', gap: 10, marginBottom: 18 }}>
            <button onClick={() => setSelected(ALL_COINS.map(c=>c.symbol))} style={{ flex: 1, padding: 8, borderRadius: 10, background: 'transparent', border: '1px solid rgba(71,85,105,0.35)', color: '#64748b', cursor: 'pointer', fontSize: 12 }}>Select All</button>
            <button onClick={() => setSelected([])} style={{ flex: 1, padding: 8, borderRadius: 10, background: 'transparent', border: '1px solid rgba(71,85,105,0.35)', color: '#64748b', cursor: 'pointer', fontSize: 12 }}>Clear All</button>
          </div>
          <button onClick={handleSave} disabled={saving} style={{ width: '100%', padding: 14, borderRadius: 14, fontWeight: 800, fontSize: 14, background: saving?'rgba(139,92,246,0.35)':'linear-gradient(135deg,#8b5cf6,#6366f1)', border: 'none', color: '#fff', cursor: saving?'not-allowed':'pointer', boxShadow: saving?'none':'0 10px 35px rgba(139,92,246,0.35)', fontFamily: "'Space Mono',monospace", letterSpacing: '0.08em', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, transition: 'all 0.2s ease' }}>
            {saving ? <><div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />SAVING…</> : `SAVE PORTFOLIO (${selected.length} coins)`}
          </button>
        </div>

        <div>
          <h2 style={{ color: '#94a3b8', fontSize: 12, fontWeight: 700, margin: '0 0 18px', letterSpacing: '0.12em', textTransform: 'uppercase' }}>Current Portfolio</h2>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>{Array(5).fill(0).map((_,i)=><div key={i} className="skeleton" style={{height:68,borderRadius:14}}/>)}</div>
          ) : saved.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '50px 20px', color: '#475569' }}><div style={{fontSize:36,marginBottom:10,opacity:.35}}>◎</div><div>No coins saved yet</div></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {saved.map((sym, i) => {
                const coin = ALL_COINS.find(c => c.symbol === sym)
                const sig  = getSignal(sym)
                const c    = sig ? SIG_CFG[sig.signal] : null
                return (
                  <div key={sym} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 18px', background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 14, animation: `fadeUp 0.3s ease ${i*0.05}s both` }}>
                    <div style={{ width: 38, height: 38, borderRadius: 11, flexShrink: 0, background: `${coin?.color||'#8b5cf6'}22`, border: `1px solid ${coin?.color||'#8b5cf6'}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <div style={{ width: 10, height: 10, borderRadius: '50%', background: coin?.color||'#8b5cf6' }} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14, fontFamily: "'Space Mono',monospace" }}>{sym}</div>
                      <div style={{ color: '#64748b', fontSize: 11, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{coin?.name}</div>
                    </div>
                    {c ? <span style={{ flexShrink: 0, background: c.bg, border: `1px solid ${c.border}`, color: c.color, borderRadius: 8, padding: '4px 12px', fontSize: 11, fontWeight: 800, fontFamily: "'Space Mono',monospace" }}>{sig.signal}</span> : <span style={{color:'#475569',fontSize:11}}>—</span>}
                    {sig && <div style={{flexShrink:0,textAlign:'right'}}><div style={{color:'#f1f5f9',fontSize:13,fontWeight:700,fontFamily:"'Space Mono',monospace"}}>{sig.confidence}%</div><div style={{color:'#475569',fontSize:10}}>conf.</div></div>}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
