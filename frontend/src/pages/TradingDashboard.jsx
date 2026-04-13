import { useState, useEffect, useRef, useCallback, memo } from 'react'
import {
  fetchLivePrice,
  fetchBinanceKlines,
  fetchMultiplePrices,
  fetchBalance,
  fetchTradingStatus,
  fetchMarketStatus,
  fetchSignals,
  fetchPredictions,
  placeLiveOrder,
  ALL_COINS,
} from '../services/api'

// ─── Trading coins (all 17) ───────────────────────────────────────────────────
const TRADE_COINS = ALL_COINS

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmtPrice(n) {
  if (!n) return '$0.00'
  if (n >= 10000) return '$' + n.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (n >= 1)     return '$' + n.toFixed(4)
  if (n >= 0.0001)return '$' + n.toFixed(6)
  return '$' + n.toFixed(9)
}
function fmtLarge(n) {
  if (!n) return '$0'
  if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B'
  if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return '$' + (n / 1e3).toFixed(1) + 'K'
  return '$' + n.toFixed(2)
}
function fmtPct(n) {
  const v = (n ?? 0).toFixed(2)
  return (n >= 0 ? '+' : '') + v + '%'
}
function pctColor(n) { return n >= 0 ? '#34d399' : '#f87171' }

// ─── Simulated trades from live price ────────────────────────────────────────
function buildTrades(price, count = 12) {
  return Array.from({ length: count }, (_, i) => ({
    p:  price * (1 + (Math.random() - 0.5) * 0.0008),
    sz: +(Math.random() * 1.5 + 0.01).toFixed(4),
    up: Math.random() > 0.48,
    t:  new Date(Date.now() - i * 6500).toLocaleTimeString('en-US', { hour12: false }),
  }))
}

// ─── Mini sparkline from price history (memoized) ───────────────────────────
const Spark = memo(function Spark({ prices, color, w = 60, h = 22 }) {
  if (!prices || prices.length < 2) return <div style={{ width: w, height: h }} />
  const mn = Math.min(...prices), mx = Math.max(...prices), rng = mx - mn || 1
  const pts = prices.map((v, i) => `${(i / (prices.length - 1)) * w},${h - ((v - mn) / rng) * (h - 2) + 1}`)
  const fill = `0,${h} ${pts.join(' ')} ${w},${h}` 
  return (
    <svg width={w} height={h} style={{ display: 'block', flexShrink: 0 }}>
      <polygon points={fill} fill={color} opacity=".15" />
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  )
})

// ─── Canvas price chart with candlesticks ─────────────────
function PriceChart({ history, candles, predictions, loading }) {
  const ref = useRef(null)
  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width  = rect.width  * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
    const W = rect.width, H = rect.height

    ctx.clearRect(0, 0, W, H)

    // Use candles if available, otherwise fall back to history
    const chartData = candles && candles.length > 0 ? candles : history.map((p, i) => ({ open: p, high: p, low: p, close: p }))
    
    if (loading || chartData.length < 2) {
      ctx.fillStyle = 'rgba(71,85,105,0.15)'
      ctx.font = '12px DM Sans, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(loading ? 'Loading…' : 'No data', W / 2, H / 2)
      return
    }

    // Calculate min/max from candle data
    const allHighs = chartData.map(c => c.high)
    const allLows = chartData.map(c => c.low)
    const mn = Math.min(...allLows), mx = Math.max(...allHighs), rng = mx - mn || 1
    
    const padT = 10, padB = 8, padL = 4, padR = 52
    const candleWidth = Math.max(2, (W - padL - padR) / chartData.length * 0.7)
    
    const toX = (i) => padL + (i / (chartData.length - 1)) * (W - padL - padR)
    const toY = v => padT + (1 - (v - mn) / rng) * (H - padT - padB)

    // Grid
    for (let i = 0; i <= 4; i++) {
      const y = padT + (i / 4) * (H - padT - padB)
      ctx.strokeStyle = 'rgba(71,85,105,0.15)'
      ctx.lineWidth = 0.5
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke()
      ctx.fillStyle = '#475569'
      ctx.font = '9px Space Mono, monospace'
      ctx.textAlign = 'left'
      ctx.fillText(fmtPrice(mx - (i / 4) * rng).replace('$', ''), W - padR + 4, y + 3)
    }

    // Draw candlesticks
    chartData.forEach((candle, i) => {
      const x = toX(i)
      const yOpen = toY(candle.open)
      const yClose = toY(candle.close)
      const yHigh = toY(candle.high)
      const yLow = toY(candle.low)
      
      const isUp = candle.close >= candle.open
      const color = isUp ? '#10b981' : '#ef4444'
      
      // Wick
      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(x, yHigh)
      ctx.lineTo(x, yLow)
      ctx.stroke()
      
      // Body
      const bodyTop = Math.min(yOpen, yClose)
      const bodyHeight = Math.max(1, Math.abs(yClose - yOpen))
      ctx.fillStyle = color
      ctx.fillRect(x - candleWidth/2, bodyTop, candleWidth, bodyHeight)
    })

    // Current price indicator
    const lastCandle = chartData[chartData.length - 1]
    if (lastCandle) {
      const lastY = toY(lastCandle.close)
      ctx.beginPath()
      ctx.arc(toX(chartData.length - 1), lastY, 4, 0, Math.PI * 2)
      ctx.fillStyle = lastCandle.close >= lastCandle.open ? '#10b981' : '#ef4444'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1.5
      ctx.stroke()
      
      // Price label
      ctx.fillStyle = '#f1f5f9'
      ctx.font = '10px Space Mono, monospace'
      ctx.textAlign = 'left'
      ctx.fillText(fmtPrice(lastCandle.close), W - padR + 4, lastY + 3)
    }

    // Predictions (if any)
    if (predictions && predictions.length > 0) {
      const predColor = '#a78bfa'
      const lastX = toX(chartData.length - 1)
      const lastPrice = chartData[chartData.length - 1]?.close
      
      ctx.beginPath()
      ctx.strokeStyle = predColor
      ctx.lineWidth = 2
      ctx.setLineDash([5, 3])
      ctx.moveTo(lastX, toY(lastPrice))
      
      predictions.forEach((p, i) => {
        const predX = lastX + (i + 1) * 20
        const predY = toY(p.close)
        ctx.lineTo(predX, predY)
      })
      ctx.stroke()
      ctx.setLineDash([])
    }
  }, [history, candles, predictions, loading])

  return <canvas ref={ref} style={{ width: '100%', height: 190, display: 'block', cursor: 'crosshair' }} />
}

// ─── Signal badge (memoized) ─────────────────────────────────────────────────
const SigBadge = memo(function SigBadge({ signal, size = 'sm' }) {
  const cfg = {
    BUY:  ['rgba(16,185,129,0.15)','rgba(16,185,129,0.4)','#34d399'],
    SELL: ['rgba(239,68,68,0.15)', 'rgba(239,68,68,0.4)', '#f87171'],
    HOLD: ['rgba(245,158,11,0.12)','rgba(245,158,11,0.35)','#fbbf24'],
  }
  const [bg, bd, cl] = cfg[signal] || cfg.HOLD
  const dot = signal === 'BUY' ? '▲' : signal === 'SELL' ? '▼' : '—'
  return (
    <span style={{ background: bg, border: `1px solid ${bd}`, color: cl, borderRadius: 8, padding: size === 'lg' ? '5px 14px' : '3px 9px', fontSize: size === 'lg' ? 13 : 10, fontWeight: 800, letterSpacing: '0.06em', fontFamily: "'Space Mono', monospace" }}>
      {signal} {dot}
    </span>
  )
})

const card = { background: 'linear-gradient(145deg,rgba(30,41,59,0.85),rgba(15,23,42,0.92))', border: '1px solid rgba(71,85,105,0.3)', borderRadius: 16 }
const mono = { fontFamily: "'Space Mono', monospace" }

// ─── Main Component ───────────────────────────────────────────────────────────
export default function TradingDashboard() {
  const [activeCoin, setActiveCoin]       = useState(TRADE_COINS[0])
  const [prices, setPrices]               = useState({})      // { BTC: { price, change24h, ... } }
  const [priceHistory, setPriceHistory]   = useState({})      // { BTC: [12345, 12400, ...] }
  const [klinesData, setKlinesData]       = useState({})      // { BTC: { candles: [] } }
  const [predictions, setPredictions]     = useState([])     // All coins predictions
  const [balance, setBalance]             = useState(null)
  const [tradingStatus, setTradingStatus] = useState(null)
  const [marketStatus, setMarketStatus]   = useState(null)
  const [signals, setSignals]             = useState([])
  const [orderSide, setOrderSide]         = useState('BUY')
  const [orderType, setOrderType]         = useState('MARKET')
  const [orderAmt, setOrderAmt]           = useState('500')
  const [openOrders, setOpenOrders]       = useState([])
  const [orderMsg, setOrderMsg]           = useState({ text: '', color: '' })
  const [loadingPrices, setLoadingPrices] = useState(true)
  const [placingOrder, setPlacingOrder]   = useState(false)
  const [error, setError]                 = useState('')
  const [lastUpdated, setLastUpdated]     = useState(null)
  const priceIntervalRef  = useRef(null)
  const singlePriceRef    = useRef(null)
  const klinesRef         = useRef(null)
  const tvScriptRef       = useRef(null)
  const [currentIv, setCurrentIv] = useState('60')
  const [predictionTimeframe, setPredictionTimeframe] = useState('1h')

  const TIMEFRAMES = [
    { value: '30m', label: '30m', desc: 'Short' },
    { value: '1h', label: '1h', desc: 'Balanced' },
    { value: '4h', label: '4h', desc: 'Low Noise' },
    { value: '1d', label: '1d', desc: 'High Acc' }
  ]

  // ── Load all data on mount ──
  useEffect(() => {
    loadAllPrices()
    loadSupportingData()
    loadPredictions()
  }, [])

  // ── Consolidated fast polling every 5 seconds for active coin only ──
  useEffect(() => {
    const fastPoll = async () => {
      // Only update active coin price (fast)
      await loadSinglePrice(activeCoin.symbol)
      // Update klines every 3rd poll (15s)
      if (Date.now() % 3 === 0) {
        const data = await fetchBinanceKlines(activeCoin.symbol, '1h', 100)
        if (data?.candles?.length > 0) {
          setKlinesData(prev => ({ ...prev, [activeCoin.symbol]: data }))
        }
      }
    }
    
    fastPoll() // Run immediately
    const interval = setInterval(fastPoll, 5000) // Every 5 seconds
    return () => clearInterval(interval)
  }, [activeCoin.symbol])

  // ── Background slow polling for all coins every 60s ──
  useEffect(() => {
    const interval = setInterval(loadAllPrices, 60000)
    return () => clearInterval(interval)
  }, [])

  // ── Load TradingView Chart (debounced) ──
  useEffect(() => {
    const timer = setTimeout(() => {
      loadTradingViewChart()
    }, 300) // Small delay to prevent rapid reloads
    return () => clearTimeout(timer)
  }, [activeCoin.symbol, currentIv])

  const loadTradingViewChart = useCallback(() => {
    const container = document.getElementById('tv-container')
    if (!container) return

    // Check if chart is already loaded for this coin/interval
    const existingWidget = container.querySelector('.tradingview-widget-container')
    if (existingWidget && container.dataset.loadedFor === `${activeCoin.symbol}-${currentIv}`) {
      return // Skip reload if already loaded
    }
    container.dataset.loadedFor = `${activeCoin.symbol}-${currentIv}`

    // Clear old widget
    while (container.firstChild) {
      container.removeChild(container.firstChild)
    }
    if (tvScriptRef.current) {
      tvScriptRef.current.remove()
      tvScriptRef.current = null
    }

    // Show loading briefly
    const loading = document.createElement('div')
    loading.id = 'chart-loading'
    loading.style.cssText = 'position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;background:#0f172a;z-index:10;'
    loading.innerHTML = `
      <div style="width:32px;height:32px;border:2px solid rgba(71,85,105,0.3);border-top-color:#a78bfa;border-radius:50%;animation:spin 0.7s linear infinite"></div>
      <div style="font-family:'Space Mono',monospace;font-size:12px;color:#64748b">Loading ${activeCoin.symbol}...</div>
    `
    container.appendChild(loading)

    // Create widget container
    const wrapper = document.createElement('div')
    wrapper.className = 'tradingview-widget-container'
    wrapper.style.cssText = 'width:100%;height:100%;'
    const inner = document.createElement('div')
    inner.className = 'tradingview-widget-container__widget'
    inner.style.cssText = 'width:100%;height:100%;'
    wrapper.appendChild(inner)
    container.appendChild(wrapper)

    // Create script
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.async = true
    script.type = 'text/javascript'
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: 'BINANCE:' + activeCoin.symbol + 'USDT',
      interval: currentIv,
      timezone: 'Etc/UTC',
      theme: 'dark',
      style: '1',
      locale: 'en',
      allow_symbol_change: false,
      calendar: false,
      support_host: 'https://www.tradingview.com',
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: true,
      studies: ['STD;MACD', 'STD;RSI'],
      withdateranges: true,
      hide_side_toolbar: false,
      details: false
    })
    wrapper.appendChild(script)
    tvScriptRef.current = script

    // Hide loading after 1.5s (reduced from 2s)
    setTimeout(() => {
      const ld = document.getElementById('chart-loading')
      if (ld) ld.style.opacity = '0'
      setTimeout(() => { if (ld && ld.parentNode) ld.parentNode.removeChild(ld) }, 300)
    }, 1500)
  }, [activeCoin.symbol, currentIv])

  const setIv = (iv) => {
    setCurrentIv(iv)
  }

  // ── Fetch all 10 prices in parallel ──
  const loadAllPrices = useCallback(async () => {
    try {
      const symbols = TRADE_COINS.map(c => c.symbol)
      const results = await fetchMultiplePrices(symbols)
      const newPrices = {}
      results.forEach(r => {
        if (r?.symbol) newPrices[r.symbol] = r
      })
      setPrices(prev => {
        // Build price history from ticks
        const newHistory = { ...prev._history || {} }
        Object.entries(newPrices).forEach(([sym, data]) => {
          if (data.price) {
            newHistory[sym] = [...(newHistory[sym] || []), data.price].slice(-60)
          }
        })
        return { ...newPrices, _history: newHistory }
      })
      setLastUpdated(new Date())
      setLoadingPrices(false)
      setError('')
    } catch (err) {
      console.error('loadAllPrices failed:', err)
      setError('Could not reach backend. Is FastAPI running?')
      setLoadingPrices(false)
    }
  }, [])

  // ── Fetch single coin price (for faster updates on active coin) ──
  const loadSinglePrice = useCallback(async (symbol) => {
    const data = await fetchLivePrice(symbol)
    if (!data) return
    setPrices(prev => {
      const history = prev._history || {}
      const coinHistory = [...(history[symbol] || []), data.price].slice(-60)
      return {
        ...prev,
        [symbol]: data,
        _history: { ...history, [symbol]: coinHistory }
      }
    })
    setPriceHistory(prev => ({
      ...prev,
      [symbol]: [...(prev[symbol] || []), data.price].slice(-60),
    }))
  }, [])

  // ── Load balance, status, market, signals ──
  const loadSupportingData = useCallback(async () => {
    const [bal, status, market, sigs] = await Promise.allSettled([
      fetchBalance(),
      fetchTradingStatus(),
      fetchMarketStatus(),
      fetchSignals(),
    ])
    if (bal.status === 'fulfilled')    setBalance(bal.value)
    if (status.status === 'fulfilled') setTradingStatus(status.value)
    if (market.status === 'fulfilled') setMarketStatus(market.value)
    if (sigs.status === 'fulfilled')   setSignals(sigs.value)
  }, [])

  // ── Load AI predictions for all coins ──
  const loadPredictions = useCallback(async () => {
    const preds = await fetchPredictions()
    setPredictions(preds)
  }, [])

  // ── Derived values ──
  const activeLive    = prices[activeCoin.symbol]
  const livePrice     = activeLive?.price     ?? 0
  const change24h     = activeLive?.change24h ?? 0
  const change1h      = activeLive?.change1h  ?? 0
  const coinHistory   = prices._history?.[activeCoin.symbol] || priceHistory[activeCoin.symbol] || []
  const activeSignal  = signals.find(s => s.coin === activeCoin.symbol)
  const sigDisplay    = activeSignal || { signal: livePrice ? (change24h > 1 ? 'BUY' : change24h < -1 ? 'SELL' : 'HOLD') : 'HOLD', probability: 70, confidence: 72 }
  const estQty        = livePrice ? (+(parseFloat(orderAmt || 0) / livePrice).toFixed(6)).toString() : '0'

  const sigColors = {
    BUY:  { bg:'rgba(16,185,129,0.1)',  bd:'rgba(16,185,129,0.25)', cl:'#34d399', bar:'#10b981' },
    SELL: { bg:'rgba(239,68,68,0.1)',   bd:'rgba(239,68,68,0.25)',  cl:'#f87171', bar:'#ef4444' },
    HOLD: { bg:'rgba(245,158,11,0.08)', bd:'rgba(245,158,11,0.2)',  cl:'#fbbf24', bar:'#f59e0b' },
  }
  const sc = sigColors[sigDisplay.signal] || sigColors.HOLD

  // ── Place order via API ──
  const placeOrder = async () => {
    const amt = parseFloat(orderAmt)
    if (!amt || amt <= 0) { setOrderMsg({ text: 'Enter a valid amount', color: '#f87171' }); return }
    if (!livePrice)        { setOrderMsg({ text: 'Price not available yet', color: '#f87171' }); return }
    setPlacingOrder(true)
    try {
      const qty = +(amt / livePrice).toFixed(6)
      const result = await placeLiveOrder({
        symbol:    activeCoin.symbol,
        side:      orderSide,
        quantity:  qty,
        orderType: orderType,
        price:     orderType !== 'MARKET' ? livePrice : null,
      })
      const order = { ...result, amt, coin: activeCoin.symbol }
      setOpenOrders(p => [order, ...p])
      setOrderMsg({ text: `${orderSide} ${qty} ${activeCoin.symbol} @ ${fmtPrice(livePrice)} — ID: ${result.orderId}`, color: '#34d399' })
      // Refresh balance after order
      setTimeout(async () => {
        const bal = await fetchBalance()
        setBalance(bal)
      }, 2000)
    } catch (err) {
      setOrderMsg({ text: err.message || 'Order failed', color: '#f87171' })
    } finally {
      setPlacingOrder(false)
      setTimeout(() => setOrderMsg({ text: '', color: '' }), 5000)
    }
  }

  const label10 = { color: '#64748b', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em' }

  return (
    <div style={{ animation: 'fadeUp 0.4s ease both', fontFamily: "'DM Sans', sans-serif" }}>

      {/* ── Error banner ── */}
      {error && (
        <div style={{ marginBottom: 16, padding: '10px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, color: '#fca5a5', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>⚠️</span> {error}
          <button onClick={loadAllPrices} style={{ marginLeft: 'auto', padding: '3px 10px', borderRadius: 7, background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171', cursor: 'pointer', fontSize: 11 }}>Retry</button>
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, paddingBottom: 18, borderBottom: '1px solid rgba(71,85,105,0.18)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <h1 style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 24, margin: 0, ...mono, letterSpacing: '-0.03em' }}>Live Trading</h1>
            <span style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '3px 10px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 20 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block', animation: 'pulseDot 2s infinite' }} />
              <span style={{ color: '#10b981', fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', ...mono }}>LIVE</span>
            </span>
            <select 
              value={predictionTimeframe} 
              onChange={(e) => setPredictionTimeframe(e.target.value)}
              style={{ padding: '4px 10px', borderRadius: 6, background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)', color: '#a78bfa', fontSize: 11, cursor: 'pointer', ...mono }}
            >
              {TIMEFRAMES.map(tf => <option key={tf.value} value={tf.value}>{tf.label}</option>)}
            </select>
            {tradingStatus && (
              <span style={{ background: tradingStatus.connected ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${tradingStatus.connected ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`, color: tradingStatus.connected ? '#34d399' : '#f87171', fontSize: 10, fontWeight: 700, borderRadius: 7, padding: '2px 9px', ...mono }}>
                {tradingStatus.exchange} · {tradingStatus.mode.toUpperCase()}
              </span>
            )}
          </div>
          <p style={{ color: '#475569', fontSize: 12, margin: 0 }}>
            FastAPI backend · {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : 'Connecting…'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 20 }}>
          {marketStatus && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ ...label10, marginBottom: 2 }}>Regime</div>
              <div style={{ color: marketStatus.regime === 'BULL' ? '#34d399' : '#f87171', fontWeight: 800, fontSize: 14, ...mono }}>{marketStatus.regime} · {marketStatus.volatility}</div>
            </div>
          )}
        </div>
      </div>

      {/* ── Coin Tabs ── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 18, overflowX: 'auto', paddingBottom: 4, scrollbarWidth: 'none' }}>
        {TRADE_COINS.map(coin => {
          const live   = prices[coin.symbol]
          const active = coin.symbol === activeCoin.symbol
          const up     = (live?.change24h ?? 0) >= 0
          const hist   = prices._history?.[coin.symbol] || []
          return (
            <button key={coin.symbol} onClick={() => setActiveCoin(coin)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderRadius: 12, cursor: 'pointer', flexShrink: 0, background: active ? 'rgba(139,92,246,0.18)' : 'rgba(15,23,42,0.6)', border: `1px solid ${active ? 'rgba(139,92,246,0.45)' : 'rgba(71,85,105,0.3)'}`, transition: 'all 0.18s ease' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: coin.color }} />
              <div>
                <div style={{ color: active ? '#a78bfa' : '#94a3b8', ...mono, fontWeight: 700, fontSize: 12, lineHeight: 1 }}>{coin.symbol}</div>
                {loadingPrices
                  ? <div style={{ width: 36, height: 8, borderRadius: 3, background: 'rgba(71,85,105,0.3)', marginTop: 3 }} />
                  : <div style={{ color: up ? '#34d399' : '#f87171', fontSize: 10, fontWeight: 700, ...mono, marginTop: 1 }}>
                      {live?.price ? fmtPct(live.change24h) : '—'}
                    </div>
                }
              </div>
              <Spark prices={hist} color={up ? '#10b981' : '#ef4444'} />
            </button>
          )
        })}
      </div>

      {/* ── Main Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16 }}>

        {/* LEFT */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* TradingView Chart */}
          <div style={{ ...card, padding: 0, overflow: 'hidden', minHeight: 500 }}>
            {/* Interval Bar */}
            <div style={{ padding: '10px 16px', borderBottom: '1px solid rgba(71,85,105,0.18)', display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ color: '#64748b', fontSize: 11, fontFamily: mono.fontFamily, marginRight: 6 }}>TF:</span>
              {[
                {l:'30m',v:'30'},{l:'1h',v:'60'},{l:'4h',v:'240'},{l:'1d',v:'D'}
              ].map(({l,v}) => (
                <button 
                  key={v} 
                  onClick={() => setIv(v)}
                  style={{ 
                    padding: '4px 10px', borderRadius: 6, border: `0.5px solid ${currentIv === v ? '#a78bfa' : 'rgba(71,85,105,0.3)'}`, 
                    background: currentIv === v ? '#a78bfa' : 'transparent', 
                    color: currentIv === v ? '#fff' : '#94a3b8',
                    fontFamily: mono.fontFamily, fontSize: 11, cursor: 'pointer',
                    transition: 'all 0.15s'
                  }}
                >{l}</button>
              ))}
            </div>
            <div id="tv-container" style={{ width: '100%', height: 500, position: 'relative' }} />
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* AI Signal from /api/signals */}
          <div style={{ background: sc.bg, border: `1px solid ${sc.bd}`, borderRadius: 16, padding: '14px 16px' }}>
            <div style={{ ...label10, marginBottom: 10 }}>AI Signal · {activeCoin.symbol}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <SigBadge signal={sigDisplay.signal} size="lg" />
              <span style={{ color: sc.cl, ...mono, fontSize: 12, fontWeight: 700 }}>{sigDisplay.probability}% prob</span>
            </div>
            <div style={{ height: 3, background: 'rgba(71,85,105,0.3)', borderRadius: 2, marginBottom: 10 }}>
              <div style={{ width: `${sigDisplay.confidence}%`, height: '100%', background: sc.bar, borderRadius: 2 }} />
            </div>
            {sigDisplay.momentum && <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>⚡ {sigDisplay.momentum}</div>}
            {sigDisplay.trend     && <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>📈 {sigDisplay.trend}</div>}
            {sigDisplay.volume    && <div style={{ color: '#64748b', fontSize: 11 }}>📊 {sigDisplay.volume}</div>}
            {!sigDisplay.momentum && activeLive && (
              <>
                <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>⚡ 24h: {fmtPct(change24h)}, 1h: {fmtPct(change1h)}</div>
                <div style={{ color: '#64748b', fontSize: 11 }}>📊 Vol: {fmtLarge(activeLive.volume24h)}</div>
              </>
            )}
          </div>

          {/* 1h Analysis from /api/live/klines */}
          {klinesData[activeCoin.symbol]?.analysis && (
            <div style={{ ...card, padding: '14px 16px' }}>
              <div style={{ ...label10, marginBottom: 10 }}>1h Technical Analysis</div>
              {(() => {
                const a = klinesData[activeCoin.symbol].analysis
                const trendColor = a.trend === 'BULLISH' ? '#34d399' : a.trend === 'BEARISH' ? '#f87171' : '#fbbf24'
                return (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ color: '#64748b', fontSize: 11 }}>Trend</span>
                      <span style={{ color: trendColor, fontSize: 12, fontWeight: 700, ...mono }}>{a.trend}</span>
                    </div>
                    <div style={{ height: 3, background: 'rgba(71,85,105,0.3)', borderRadius: 2, marginBottom: 10 }}>
                      <div style={{ width: `${a.trend_score}%`, height: '100%', background: trendColor, borderRadius: 2 }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                      <span style={{ color: '#64748b', fontSize: 10 }}>Trend Score</span>
                      <span style={{ color: trendColor, fontSize: 10, fontWeight: 700, ...mono }}>{a.trend_score}/100</span>
                    </div>
                    {[
                      ['SMA 7', fmtPrice(a.sma_7)],
                      ['SMA 20', fmtPrice(a.sma_20)],
                      ['24h Change', fmtPct(a.price_change_24h)],
                      ['Volatility', `${a.volatility}%`],
                      ['Support', fmtPrice(a.support)],
                      ['Resistance', fmtPrice(a.resistance)],
                      ['High 24h', fmtPrice(a.high_24h)],
                      ['Low 24h', fmtPrice(a.low_24h)],
                      ['Volume Δ', fmtPct(a.volume_change)],
                    ].map(([l, v]) => (
                      <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderTop: '1px solid rgba(71,85,105,0.1)' }}>
                        <span style={{ color: '#64748b', fontSize: 10 }}>{l}</span>
                        <span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 600, ...mono }}>{v}</span>
                      </div>
                    ))}
                  </>
                )
              })()}
            </div>
          )}

          {/* AI Predictions for All Coins */}
          {predictions.length > 0 && (
            <div style={{ ...card, padding: '14px 16px', maxHeight: 400, overflow: 'auto' }}>
              <div style={{ ...label10, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#a78bfa', animation: 'pulse 2s infinite' }} />
                AI {predictionTimeframe} Predictions · All Coins
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {predictions.map((pred) => {
                  const coin = ALL_COINS.find(c => c.symbol === pred.symbol)
                  const isUp = pred.change_percent >= 0
                  const sigCfg = {
                    BUY: { bg: 'rgba(16,185,129,0.15)', bd: 'rgba(16,185,129,0.4)', cl: '#34d399' },
                    SELL: { bg: 'rgba(239,68,68,0.15)', bd: 'rgba(239,68,68,0.4)', cl: '#f87171' },
                    HOLD: { bg: 'rgba(245,158,11,0.12)', bd: 'rgba(245,158,11,0.35)', cl: '#fbbf24' },
                  }
                  const cfg = sigCfg[pred.signal] || sigCfg.HOLD
                  // Get prediction for selected timeframe
                  const tf = predictionTimeframe
                  const predictionKey = `prediction_${tf}`
                  const prediction = pred[predictionKey] || pred.prediction_1h || {}
                  return (
                    <div 
                      key={pred.symbol} 
                      onClick={() => setActiveCoin(coin)}
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        padding: '8px 10px', 
                        background: 'rgba(15,23,42,0.5)', 
                        border: `1px solid ${activeCoin.symbol === pred.symbol ? 'rgba(139,92,246,0.5)' : 'rgba(71,85,105,0.2)'}`, 
                        borderRadius: 10,
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 7, height: 7, borderRadius: '50%', background: coin?.color || '#8b5cf6' }} />
                        <span style={{ color: '#f1f5f9', fontSize: 12, fontWeight: 700, ...mono, width: 45 }}>{pred.symbol}</span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ color: isUp ? '#34d399' : '#f87171', fontSize: 11, fontWeight: 700, ...mono }}>
                          {isUp ? '▲' : '▼'} {Math.abs(pred.change_percent).toFixed(2)}%
                        </div>
                        <div style={{ color: '#64748b', fontSize: 9, ...mono }}>
                          {fmtPrice(prediction.target_price || pred.prediction_1h)}
                        </div>
                      </div>
                      <div style={{ 
                        background: cfg.bg, 
                        border: `1px solid ${cfg.bd}`, 
                        color: cfg.cl, 
                        fontSize: 9, 
                        fontWeight: 700, 
                        padding: '2px 6px', 
                        borderRadius: 5,
                        ...mono,
                        minWidth: 45,
                        textAlign: 'center'
                      }}>
                        {pred.signal}
                      </div>
                      <div style={{ width: 35, textAlign: 'right' }}>
                        <div style={{ color: '#a78bfa', fontSize: 9, fontWeight: 700, ...mono }}>
                          {prediction.confidence || pred.confidence}%
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Market Status from /api/market/status */}
          {marketStatus && (
            <div style={{ ...card, padding: '14px 16px' }}>
              <div style={{ ...label10, marginBottom: 10 }}>Market Status</div>
              {[
                ['Regime',       marketStatus.regime,     marketStatus.regime === 'BULL' ? '#34d399' : '#f87171'],
                ['Volatility',   marketStatus.volatility, marketStatus.volatility === 'LOW' ? '#34d399' : marketStatus.volatility === 'HIGH' ? '#f87171' : '#fbbf24'],
                ['Fear & Greed', `${marketStatus.fearGreed}/100`, pctColor(marketStatus.fearGreed - 50)],
                ['BTC Dom.',     `${marketStatus.dominance?.toFixed(1)}%`, '#f7931a'],
              ].map(([l, v, c]) => (
                <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(71,85,105,0.12)' }}>
                  <span style={{ color: '#64748b', fontSize: 11 }}>{l}</span>
                  <span style={{ color: c, fontSize: 11, fontWeight: 700, ...mono }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
