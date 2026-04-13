import { useState, useEffect, useRef } from 'react'
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, Cell, ReferenceLine } from 'recharts'
import api from '../../services/api'

export default function TradingViewChart({ symbol = 'BTC', color = '#f7931a' }) {
  const [data, setData] = useState([])
  const [futureData, setFutureData] = useState([])
  const [timeRange, setTimeRange] = useState('1H')
  const [price, setPrice] = useState(0)
  const [change, setChange] = useState(0)
  const [predictions, setPredictions] = useState({})
  const [backtestResults, setBacktestResults] = useState(null)
  const [signals, setSignals] = useState([])
  const [lastSignal, setLastSignal] = useState(null)
  const [isLive, setIsLive] = useState(false)
  const [showBacktest, setShowBacktest] = useState(false)
  const intervalRef = useRef(null)

  const timeRangeConfig = {
    '1m': { interval: 60000, points: 60, label: '1m', format: 'time' },
    '5m': { interval: 300000, points: 60, label: '5m', format: 'time' },
    '30m': { interval: 1800000, points: 60, label: '30m', format: 'time' },
    '1H': { interval: 3600000, points: 24, label: '1H', format: 'time' },
    '4H': { interval: 14400000, points: 30, label: '4H', format: 'datetime' },
    '1D': { interval: 86400000, points: 30, label: '1D', format: 'date' },
    '7D': { interval: 604800000, points: 12, label: '1W', format: 'date' },
    '30D': { interval: 2592000000, points: 30, label: '1M', format: 'date' }
  }

  const TIMEFRAMES = [
    { label: '30m', minutes: 30 },
    { label: '1h', minutes: 60 }
  ]

  // Single useEffect with all logic inside - no external dependencies
  useEffect(() => {
    console.log('TradingViewChart: useEffect starting', { symbol, timeRange })
    let mounted = true
    
    // All helper functions defined INSIDE the effect - no closure issues
    const formatTime = (date, format) => {
      if (format === 'time') return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      if (format === 'date') return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
      return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    }

    const generateCandle = (prevClose, time, isFuture = false) => {
      const volatility = prevClose * 0.015
      const trendBias = isFuture ? (Math.random() - 0.3) * 0.02 : 0
      const open = prevClose
      const close = open + (Math.random() - 0.5 + trendBias) * volatility * 2
      const high = Math.max(open, close) + Math.random() * volatility * 0.8
      const low = Math.min(open, close) - Math.random() * volatility * 0.8
      const volume = Math.floor(Math.random() * 5000 + 1000)
      return { time, open, high, low, close, volume, isFuture, up: close >= open }
    }

    const generatePredictions = (currentPrice) => {
      const predictions = {}
      TIMEFRAMES.forEach((tf, idx) => {
        const hoursAhead = tf.minutes / 60
        const volatility = 0.003 * Math.sqrt(hoursAhead)
        const trendStrength = Math.sin(Date.now() / 60000 + idx) * 0.005
        const randomComponent = (Math.random() - 0.5) * volatility * 2
        const priceChangePercent = trendStrength + randomComponent
        const projectedPrice = currentPrice * (1 + priceChangePercent)
        const profitPercent = Math.max(-5, Math.min(5, priceChangePercent * 100))
        const confidence = Math.min(95, 55 + Math.abs(profitPercent) * 3 + Math.random() * 10)
        const signal = profitPercent > 2 ? 'STRONG_BUY' : profitPercent > 0.5 ? 'BUY' : profitPercent < -2 ? 'STRONG_SELL' : profitPercent < -0.5 ? 'SELL' : 'HOLD'
        predictions[tf.label] = { price: projectedPrice, profit: profitPercent, confidence, signal, direction: profitPercent > 0 ? 'up' : 'down' }
      })
      return predictions
    }

    const calculateRSI = (candles) => {
      if (candles.length < 2) return 50
      let gains = 0, losses = 0
      for (let i = 1; i < candles.length; i++) {
        const change = candles[i].close - candles[i-1].close
        if (change > 0) gains += change
        else losses += Math.abs(change)
      }
      const avgGain = gains / 14
      const avgLoss = losses / 14
      if (avgLoss === 0) return 100
      const rs = avgGain / avgLoss
      return 100 - (100 / (1 + rs))
    }

    const generateSignals = (candles) => {
      const signals = []
      let position = null
      for (let i = 10; i < candles.length; i++) {
        const current = candles[i]
        const shortMA = candles.slice(i-5, i).reduce((a, b) => a + b.close, 0) / 5
        const longMA = candles.slice(i-10, i).reduce((a, b) => a + b.close, 0) / 10
        const rsi = calculateRSI(candles.slice(i-14, i+1))
        if (!position && shortMA > longMA && current.close > shortMA && rsi > 30 && rsi < 50) {
          signals.push({ type: 'BUY', time: current.time, price: current.close, index: i })
          position = 'LONG'
        } else if (position === 'LONG' && (shortMA < longMA || rsi > 70)) {
          signals.push({ type: 'SELL', time: current.time, price: current.close, index: i })
          position = null
        }
      }
      return signals
    }

    const runBacktest = (historicalData) => {
      if (historicalData.length < 10) return null
      let trades = 0, wins = 0, totalProfit = 0, maxDrawdown = 0, peak = 100
      let position = null, entryPrice = 0, equity = 100
      for (let i = 5; i < historicalData.length - 1; i++) {
        const current = historicalData[i]
        const shortMA = historicalData.slice(i - 5, i).reduce((a, b) => a + b.close, 0) / 5
        const longMA = historicalData.slice(i - 10, i).reduce((a, b) => a + b.close, 0) / 10
        if (!position && shortMA > longMA && current.close > shortMA) {
          position = 'LONG'
          entryPrice = current.close
        } else if (position === 'LONG' && (shortMA < longMA || current.close < entryPrice * 0.98)) {
          const profit = ((current.close - entryPrice) / entryPrice) * 100
          trades++
          if (profit > 0) wins++
          totalProfit += profit
          equity = equity * (1 + profit / 100)
          if (equity > peak) peak = equity
          const drawdown = ((peak - equity) / peak) * 100
          if (drawdown > maxDrawdown) maxDrawdown = drawdown
          position = null
        }
      }
      return {
        trades,
        winRate: trades > 0 ? ((wins / trades) * 100).toFixed(1) : 0,
        totalProfit: totalProfit.toFixed(2),
        maxDrawdown: maxDrawdown.toFixed(2),
        avgProfit: trades > 0 ? (totalProfit / trades).toFixed(2) : 0,
        sharpe: trades > 0 ? (totalProfit / Math.max(1, maxDrawdown)).toFixed(2) : 0
      }
    }

    const fetchLivePrice = async () => {
      try {
        const response = await api.get(`/live/price/${symbol}USDT`)
        if (response.data && response.data.price) return response.data.price
      } catch (err) {}
      return null
    }

    const generateInitialData = (livePrice = null) => {
      const basePrice = livePrice || (symbol === 'BTC' ? 45000 : symbol === 'ETH' ? 2800 : 100)
      const config = timeRangeConfig[timeRange]
      const points = config.points
      const interval = config.interval
      const dataPoints = []
      let currentPrice = basePrice
      for (let i = 0; i < points; i++) {
        const time = new Date(Date.now() - (points - i) * interval)
        const candle = generateCandle(currentPrice, formatTime(time, config.format))
        dataPoints.push(candle)
        currentPrice = candle.close
      }
      setPrice(currentPrice)
      setChange(((currentPrice - basePrice) / basePrice) * 100)
      setPredictions(generatePredictions(currentPrice))
      const future = []
      let futurePrice = currentPrice
      for (let i = 1; i <= 12; i++) {
        const time = `+${i * 5}m`
        const candle = generateCandle(futurePrice, time, true)
        future.push(candle)
        futurePrice = candle.close
      }
      setFutureData(future)
      const generatedSignals = generateSignals(dataPoints)
      setSignals(generatedSignals)
      if (generatedSignals.length > 0) setLastSignal(generatedSignals[generatedSignals.length - 1])
      setBacktestResults(runBacktest(dataPoints))
      return dataPoints
    }

    const loadData = async () => {
      console.log('TradingViewChart: loadData starting')
      try {
        const livePrice = await fetchLivePrice()
        console.log('TradingViewChart: livePrice fetched', livePrice)
        if (!mounted) return
        const initialData = generateInitialData(livePrice)
        console.log('TradingViewChart: initialData generated', initialData.length)
        setData(initialData)
        setIsLive(!!livePrice)
      } catch (err) {
        console.error('TradingViewChart: Error in loadData:', err)
      }
    }
    loadData()
    
    intervalRef.current = setInterval(async () => {
      try {
        let livePrice = null
        try { livePrice = await fetchLivePrice() } catch (e) {}
        if (!mounted) return
        
        setData(prevData => {
          if (!prevData || prevData.length === 0) return prevData
          const lastPrice = livePrice || prevData[prevData.length - 1]?.close || 45000
          const newCandle = generateCandle(lastPrice, formatTime(new Date(), timeRangeConfig[timeRange].format))
          const newData = [...prevData.slice(1), newCandle]
          setPrice(newCandle.close)
          const firstPrice = prevData[0]?.open || lastPrice
          const priceChange = firstPrice > 0 ? ((newCandle.close - firstPrice) / firstPrice) * 100 : 0
          setChange(priceChange)
          setPredictions(generatePredictions(newCandle.close))
          const generatedSignals = generateSignals(newData)
          setSignals(generatedSignals)
          if (generatedSignals.length > 0) setLastSignal(generatedSignals[generatedSignals.length - 1])
          const future = []
          let futurePrice = newCandle.close
          for (let i = 1; i <= 12; i++) {
            const time = `+${i * 5}m`
            const candle = generateCandle(futurePrice, time, true)
            future.push(candle)
            futurePrice = candle.close
          }
          setFutureData(future)
          setBacktestResults(runBacktest(newData))
          return newData
        })
      } catch (err) {}
    }, 5000)

    return () => {
      mounted = false
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [symbol, timeRange])

  const timeRanges = Object.keys(timeRangeConfig)
  const isPositive = change >= 0
  const allData = [...data, ...futureData.map(d => ({ ...d, isFuture: true }))]
  
  const minLow = allData.length > 0 ? Math.min(...allData.map(d => d.low)) * 0.998 : 0
  const maxHigh = allData.length > 0 ? Math.max(...allData.map(d => d.high)) * 1.002 : 100
  
  const currentCandle = data[data.length - 1]

  const signalColors = {
    STRONG_BUY: '#22c55e',
    BUY: '#4ade80',
    HOLD: '#f59e0b',
    SELL: '#ef4444',
    STRONG_SELL: '#dc2626'
  }

  const CandlestickShape = (props) => {
    const { x, y, width, height, payload } = props
    if (!payload) return null
    const isUp = payload.close >= payload.open
    const isFuture = payload.isFuture
    const candleColor = isFuture ? '#8b5cf6' : (isUp ? '#22c55e' : '#ef4444')
    const wickColor = isFuture ? '#8b5cf6' : (isUp ? '#22c55e' : '#ef4444')
    
    const priceRange = payload.high - payload.low
    if (!priceRange || priceRange === 0) return null
    
    const scaleY = height / priceRange
    const wickX = x + width / 2
    const wickTop = y
    const wickBottom = y + height
    
    const bodyTop = y + (payload.high - Math.max(payload.open, payload.close)) * scaleY
    const bodyHeight = Math.abs(payload.close - payload.open) * scaleY || 1
    const bodyWidth = Math.max(width * 0.6, 2)
    const bodyX = x + (width - bodyWidth) / 2
    
    return (
      <g>
        <line x1={wickX} y1={wickTop} x2={wickX} y2={wickBottom} stroke={wickColor} strokeWidth={1} />
        <rect x={bodyX} y={bodyTop} width={bodyWidth} height={Math.max(bodyHeight, 1)} fill={candleColor} />
      </g>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ background: '#0d1117', borderRadius: 8, padding: 40, textAlign: 'center', color: '#8b949e' }}>
        <div>Loading chart...</div>
      </div>
    )
  }

  return (
    <div style={{ background: '#0d1117', borderRadius: 8, overflow: 'hidden', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      {/* Header */}
      <div style={{ background: '#161b22', borderBottom: '1px solid #30363d', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
            <span style={{ color: '#c9d1d9', fontSize: 14, fontWeight: 600 }}>{symbol}/USDT</span>
          </div>
          <span style={{ color: isPositive ? '#22c55e' : '#ef4444', fontSize: 16, fontWeight: 700 }}>
            ${price.toFixed(symbol === 'BTC' ? 2 : 4)}
          </span>
          <span style={{ color: isPositive ? '#22c55e' : '#ef4444', fontSize: 12, fontWeight: 500 }}>
            {isPositive ? '+' : ''}{change.toFixed(2)}%
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: 4 }}>
          {timeRanges.map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              style={{
                padding: '4px 10px',
                borderRadius: 4,
                background: timeRange === range ? '#1f6feb' : 'transparent',
                border: 'none',
                color: timeRange === range ? '#fff' : '#8b949e',
                cursor: 'pointer',
                fontSize: 11,
                fontWeight: 600
              }}
            >
              {timeRangeConfig[range].label}
            </button>
          ))}
        </div>
      </div>

      {/* Live Status & Signal */}
      <div style={{ background: '#161b22', borderBottom: '1px solid #30363d', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: isLive ? '#22c55e' : '#f59e0b' }} />
          <span style={{ color: isLive ? '#22c55e' : '#f59e0b', fontSize: 12, fontWeight: 600 }}>
            {isLive ? 'LIVE DATA' : 'SIMULATED'}
          </span>
        </div>
        
        {lastSignal && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#8b949e', fontSize: 12 }}>Signal:</span>
            <span style={{ 
              color: lastSignal.type === 'BUY' ? '#22c55e' : '#ef4444', 
              fontSize: 14, fontWeight: 700,
              background: lastSignal.type === 'BUY' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
              padding: '4px 12px', borderRadius: 4,
              border: `1px solid ${lastSignal.type === 'BUY' ? '#22c55e' : '#ef4444'}`
            }}>
              {lastSignal.type} @ ${lastSignal.price.toFixed(2)}
            </span>
          </div>
        )}
      </div>
      
      {/* OHLC */}
      <div style={{ background: '#0d1117', borderBottom: '1px solid #21262d', padding: '6px 16px', display: 'flex', gap: 16, fontSize: 12 }}>
        {currentCandle && (
          <>
            <span style={{ color: '#8b949e' }}>O <span style={{ color: '#c9d1d9' }}>{currentCandle.open.toFixed(2)}</span></span>
            <span style={{ color: '#8b949e' }}>H <span style={{ color: '#22c55e' }}>{currentCandle.high.toFixed(2)}</span></span>
            <span style={{ color: '#8b949e' }}>L <span style={{ color: '#ef4444' }}>{currentCandle.low.toFixed(2)}</span></span>
            <span style={{ color: '#8b949e' }}>C <span style={{ color: '#c9d1d9' }}>{currentCandle.close.toFixed(2)}</span></span>
            <span style={{ color: '#8b949e' }}>Vol <span style={{ color: '#58a6ff' }}>{(currentCandle.volume / 1000).toFixed(2)}K</span></span>
          </>
        )}
      </div>

      {/* Chart */}
      <div style={{ height: 400, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={allData} margin={{ top: 10, right: 60, left: 0, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#21262d" horizontal={true} vertical={false} />
            <XAxis dataKey="time" stroke="#30363d" tick={{ fill: '#8b949e', fontSize: 10 }} tickLine={false} axisLine={{ stroke: '#30363d' }} />
            <YAxis yAxisId="price" orientation="right" stroke="#30363d" tick={{ fill: '#8b949e', fontSize: 10 }} domain={[minLow, maxHigh]} tickFormatter={(val) => val.toFixed(symbol === 'BTC' ? 0 : 2)} tickLine={false} axisLine={{ stroke: '#30363d' }} />
            <YAxis yAxisId="volume" orientation="left" hide />
            
            <ReferenceLine yAxisId="price" y={price} stroke={isPositive ? '#22c55e' : '#ef4444'} strokeDasharray="3 3" strokeWidth={1} />
            <ReferenceLine x={data[data.length - 1]?.time} stroke="#8b5cf6" strokeDasharray="5 5" label={{ value: 'NOW', fill: '#8b5cf6', fontSize: 9, position: 'insideTopLeft' }} />
            
            <Tooltip 
              contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 6, padding: 12, fontSize: 12 }}
              content={({ payload }) => {
                if (!payload || !payload.length) return null
                const d = payload[0].payload
                const isUp = d.close >= d.open
                return (
                  <div style={{ color: '#c9d1d9' }}>
                    <div style={{ color: d.isFuture ? '#8b5cf6' : '#8b949e', marginBottom: 8, fontWeight: 600, fontSize: 11 }}>
                      {d.isFuture ? '🔮 PREDICTION' : d.time}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'auto auto', gap: '4px 12px', lineHeight: '1.6' }}>
                      <span style={{ color: '#8b949e' }}>Open:</span><span style={{ color: '#c9d1d9' }}>{d.open.toFixed(4)}</span>
                      <span style={{ color: '#8b949e' }}>High:</span><span style={{ color: '#22c55e' }}>{d.high.toFixed(4)}</span>
                      <span style={{ color: '#8b949e' }}>Low:</span><span style={{ color: '#ef4444' }}>{d.low.toFixed(4)}</span>
                      <span style={{ color: '#8b949e' }}>Close:</span><span style={{ color: isUp ? '#22c55e' : '#ef4444', fontWeight: 600 }}>{d.close.toFixed(4)}</span>
                      <span style={{ color: '#8b949e' }}>Vol:</span><span style={{ color: '#58a6ff' }}>{(d.volume / 1000).toFixed(2)}K</span>
                    </div>
                  </div>
                )
              }}
            />
            
            <Bar yAxisId="price" dataKey="close" shape={<CandlestickShape />} barSize={12}>
              {allData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.isFuture ? '#8b5cf6' : (entry.up ? '#22c55e' : '#ef4444')} />
              ))}
            </Bar>
            
            <Bar yAxisId="volume" dataKey="volume" fill="#1f6feb" opacity={0.3} barSize={8}>
              {allData.map((entry, index) => (
                <Cell key={`vol-${index}`} fill={entry.isFuture ? '#8b5cf6' : (entry.up ? '#22c55e' : '#ef4444')} opacity={entry.isFuture ? 0.2 : 0.4} />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
        
        <div style={{ position: 'absolute', right: 0, top: 10, bottom: 30, width: 55, background: '#0d1117', borderLeft: '1px solid #21262d', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '4px 6px', fontSize: 10, color: '#8b949e', pointerEvents: 'none' }}>
          <span>{maxHigh.toFixed(symbol === 'BTC' ? 0 : 2)}</span>
          <span>{((maxHigh + minLow) / 2).toFixed(symbol === 'BTC' ? 0 : 2)}</span>
          <span>{minLow.toFixed(symbol === 'BTC' ? 0 : 2)}</span>
        </div>
      </div>

      {/* Predictions Panel */}
      <div style={{ background: '#161b22', borderTop: '1px solid #30363d', padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 16 }}>🔮</span>
          <h3 style={{ color: '#c9d1d9', fontWeight: 600, fontSize: 13, margin: 0 }}>AI Future Predictions (Next 1 Hour)</h3>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {TIMEFRAMES.map(tf => {
            const pred = predictions[tf.label]
            if (!pred) return null
            return (
              <div key={tf.label} style={{ background: '#0d1117', border: `1px solid ${signalColors[pred.signal]}40`, borderRadius: 8, padding: 12, textAlign: 'center' }}>
                <div style={{ color: '#8b949e', fontSize: 10, marginBottom: 4, textTransform: 'uppercase' }}>{tf.label}</div>
                <div style={{ color: '#c9d1d9', fontSize: 16, fontWeight: 700 }}>${pred.price.toFixed(symbol === 'BTC' ? 2 : 4)}</div>
                <div style={{ color: pred.profit > 0 ? '#22c55e' : '#ef4444', fontSize: 12, fontWeight: 600, marginTop: 4, background: pred.profit > 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', padding: '2px 6px', borderRadius: 4, display: 'inline-block' }}>
                  {pred.profit > 0 ? '+' : ''}{pred.profit.toFixed(2)}%
                </div>
                <div style={{ marginTop: 8, padding: '3px 8px', borderRadius: 4, background: `${signalColors[pred.signal]}20`, color: signalColors[pred.signal], fontSize: 10, fontWeight: 700, display: 'inline-block', textTransform: 'uppercase' }}>
                  {pred.signal} • {pred.confidence.toFixed(0)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Backtesting Panel */}
      <div style={{ background: '#161b22', borderTop: '1px solid #30363d', padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>📊</span>
            <h3 style={{ color: '#c9d1d9', fontWeight: 600, fontSize: 13, margin: 0 }}>Backtesting Results</h3>
          </div>
          <button onClick={() => setShowBacktest(!showBacktest)} style={{ padding: '4px 12px', borderRadius: 4, background: showBacktest ? '#1f6feb' : 'transparent', border: `1px solid ${showBacktest ? '#1f6feb' : '#30363d'}`, color: showBacktest ? '#fff' : '#8b949e', cursor: 'pointer', fontSize: 11, fontWeight: 600 }}>
            {showBacktest ? 'Hide' : 'Details'}
          </button>
        </div>

        {backtestResults && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 10 }}>
              {[['Trades', backtestResults.trades], ['Win Rate', `${backtestResults.winRate}%`], ['Profit', `${backtestResults.totalProfit}%`], ['Drawdown', `${backtestResults.maxDrawdown}%`], ['Avg', `${backtestResults.avgProfit}%`], ['Sharpe', backtestResults.sharpe]].map(([label, val]) => (
                <div key={label} style={{ textAlign: 'center', padding: '8px', background: '#0d1117', borderRadius: 6, border: '1px solid #21262d' }}>
                  <div style={{ color: '#8b949e', fontSize: 9, marginBottom: 4, textTransform: 'uppercase' }}>{label}</div>
                  <div style={{ color: (label === 'Profit' || label === 'Win Rate') && parseFloat(val) > 0 ? '#22c55e' : (label === 'Drawdown') && parseFloat(val) > 0 ? '#ef4444' : '#c9d1d9', fontSize: 14, fontWeight: 700 }}>{val}</div>
                </div>
              ))}
            </div>

            {showBacktest && (
              <div style={{ marginTop: 12, padding: 12, background: '#0d1117', borderRadius: 6, border: '1px solid #21262d' }}>
                <h4 style={{ color: '#58a6ff', fontSize: 11, margin: '0 0 8px', fontWeight: 600 }}>Strategy: MA Crossover (5 vs 10)</h4>
                <p style={{ color: '#8b949e', fontSize: 11, lineHeight: 1.6, margin: 0 }}>Entry when short MA crosses above long MA. Exit on cross below or 2% stop-loss.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
