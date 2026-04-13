import { useState, useEffect, useRef } from 'react'
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, Cell, ReferenceLine } from 'recharts'
import { fetchKlines, fetchPredictionByTimeframe } from '../services/api'

export default function LiveTradingChart({ symbol = 'BTC', color = '#f7931a' }) {
  const [data, setData] = useState([])
  const [futureData, setFutureData] = useState([])
  const [timeRange, setTimeRange] = useState('5m')
  const [price, setPrice] = useState(0)
  const [change, setChange] = useState(0)
  const [predictions, setPredictions] = useState({})
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef(null)

  const TIMEFRAMES = [
    { label: '15m', minutes: 15 },
    { label: '30m', minutes: 30 },
    { label: '1h', minutes: 60 }
  ]

  const timeRangeConfig = {
    '1m': { interval: '1m', points: 60, label: '1m', format: 'time' },
    '5m': { interval: '5m', points: 60, label: '5m', format: 'time' },
    '30m': { interval: '30m', points: 60, label: '30m', format: 'time' },
    '1H': { interval: '1h', points: 24, label: '1H', format: 'time' },
    '4H': { interval: '4h', points: 30, label: '4H', format: 'datetime' },
    '1D': { interval: '1d', points: 30, label: '1D', format: 'date' }
  }

  const formatTime = (timestamp, format) => {
    const date = new Date(timestamp)
    if (format === 'time') return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (format === 'date') return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const fetchRealData = async () => {
    try {
      setLoading(true)
      const config = timeRangeConfig[timeRange] || timeRangeConfig['5m']
      
      // Fetch real klines from backend
      const klinesData = await fetchKlines(symbol, config.interval, config.points)
      
      if (klinesData && klinesData.candles && klinesData.candles.length > 0) {
        const candles = klinesData.candles.map(c => ({
          time: formatTime(c.time || c.open_time, config.format),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
          volume: c.volume,
          timestamp: c.time || c.open_time
        }))
        
        setData(candles)
        const currentPrice = candles[candles.length - 1].close
        const firstPrice = candles[0].open
        setPrice(currentPrice)
        setChange(((currentPrice - firstPrice) / firstPrice) * 100)
        
        // Fetch real predictions from backend
        const timeframeMap = { '1m': '30m', '5m': '30m', '30m': '30m', '1H': '1h', '4H': '4h', '1D': '1d' }
        const predictionTimeframe = timeframeMap[timeRange] || '1h'
        
        const predictionData = await fetchPredictionByTimeframe(symbol, predictionTimeframe)
        
        if (predictionData && predictionData.prediction) {
          const pred = predictionData.prediction
          const newPredictions = {}
          
          TIMEFRAMES.forEach(tf => {
            const profitPercent = pred.predicted_change || 0
            const confidence = pred.confidence || 60
            const signal = pred.signal || 'HOLD'
            const targetPrice = pred.target_price || currentPrice * (1 + profitPercent / 100)
            
            newPredictions[tf.label] = {
              price: targetPrice,
              profit: profitPercent,
              confidence: confidence,
              signal: signal === 'BUY' && profitPercent > 2 ? 'STRONG_BUY' : 
                      signal === 'BUY' ? 'BUY' :
                      signal === 'SELL' && profitPercent < -2 ? 'STRONG_SELL' :
                      signal === 'SELL' ? 'SELL' : 'HOLD',
              direction: profitPercent > 0 ? 'up' : 'down'
            }
          })
          
          setPredictions(newPredictions)
          
          // Generate future candles based on prediction
          const future = generateFutureCandles(currentPrice, predictionData)
          setFutureData(future)
        }
      }
    } catch (error) {
      console.error('Failed to fetch real data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateFutureCandles = (lastClose, predictionData) => {
    const future = []
    let currentPrice = lastClose
    const candleCount = 12
    
    const pred = predictionData?.prediction || {}
    const targetPrice = pred.target_price || lastClose
    const totalChange = targetPrice - lastClose
    const changePerCandle = totalChange / candleCount
    
    for (let i = 1; i <= candleCount; i++) {
      const progress = i / candleCount
      const predictedClose = lastClose + (changePerCandle * i)
      const volatility = Math.abs(changePerCandle) * 0.3
      
      const open = i === 1 ? lastClose : future[future.length - 1].close
      const close = predictedClose + (Math.random() - 0.5) * volatility
      const high = Math.max(open, close) + Math.random() * volatility * 0.5
      const low = Math.min(open, close) - Math.random() * volatility * 0.5
      const volume = Math.random() * 1000 + 500
      
      future.push({
        time: `+${i * 5}m`,
        open: Math.round(open * 100) / 100,
        high: Math.round(high * 100) / 100,
        low: Math.round(low * 100) / 100,
        close: Math.round(close * 100) / 100,
        volume: Math.round(volume),
        isFuture: true
      })
    }
    return future
  }

  useEffect(() => {
    fetchRealData()
    
    // Refresh every 5 seconds
    intervalRef.current = setInterval(fetchRealData, 5000)
    
    return () => clearInterval(intervalRef.current)
  }, [symbol, timeRange])

  const timeRanges = Object.keys(timeRangeConfig)
  const isPositive = change >= 0
  const allData = [...data, ...futureData.map(d => ({ ...d, isFuture: true }))]
  
  const minLow = allData.length > 0 ? Math.min(...allData.map(d => d.low)) * 0.995 : 0
  const maxHigh = allData.length > 0 ? Math.max(...allData.map(d => d.high)) * 1.005 : 100

  const signalColors = {
    STRONG_BUY: '#10b981',
    BUY: '#34d399',
    HOLD: '#fbbf24',
    SELL: '#ef4444',
    STRONG_SELL: '#dc2626'
  }

  return (
    <div>
      {/* Main Chart */}
      <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 18, padding: 26, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: color }} />
            <div>
              <h3 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 16, margin: 0, fontFamily: "'Space Mono',monospace" }}>
                {symbol}/USDT
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                <span style={{ color: '#f1f5f9', fontSize: 20, fontWeight: 800, fontFamily: "'Space Mono',monospace" }}>
                  ${price.toFixed(symbol === 'BTC' ? 2 : 4)}
                </span>
                <span style={{ color: isPositive ? '#10b981' : '#ef4444', fontSize: 14, fontWeight: 600, background: isPositive ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', padding: '2px 8px', borderRadius: 6 }}>
                  {isPositive ? '+' : ''}{change.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: 8 }}>
            {timeRanges.map(range => (
              <button key={range} onClick={() => setTimeRange(range)}
                style={{ padding: '6px 14px', borderRadius: 8, background: timeRange === range ? 'rgba(139,92,246,0.2)' : 'transparent', border: `1px solid ${timeRange === range ? 'rgba(139,92,246,0.5)' : 'rgba(71,85,105,0.3)'}`, color: timeRange === range ? '#a78bfa' : '#64748b', cursor: 'pointer', fontSize: 12, fontWeight: 700, fontFamily: "'Space Mono',monospace", transition: 'all 0.2s ease' }}>
                {range}
              </button>
            ))}
          </div>
        </div>

        <div style={{ height: 320, marginTop: 10 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={allData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(71,85,105,0.2)" />
              <XAxis dataKey="time" stroke="#475569" tick={{ fill: '#475569', fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis stroke="#475569" tick={{ fill: '#475569', fontSize: 10 }} domain={[minLow, maxHigh]} tickFormatter={(val) => `$${val.toFixed(0)}`} />
              {data.length > 0 && <ReferenceLine x={data[data.length - 1]?.time} stroke="#8b5cf6" strokeDasharray="5 5" label={{ value: 'NOW', fill: '#8b5cf6', fontSize: 10, position: 'top' }} />}
              <Tooltip content={({ payload }) => {
                if (!payload || !payload.length) return null
                const d = payload[0].payload
                const isUp = d.close >= d.open
                return (
                  <div style={{ background: '#1e293b', border: '1px solid rgba(139,92,246,0.3)', borderRadius: 12, padding: 12, color: '#f1f5f9', fontSize: 12 }}>
                    <div style={{ color: d.isFuture ? '#8b5cf6' : '#64748b', marginBottom: 8, fontWeight: 700 }}>
                      {d.isFuture ? '🔮 PREDICTED' : d.time}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px' }}>
                      <span style={{ color: '#64748b' }}>Open:</span><span style={{ color: '#f1f5f9', fontWeight: 600 }}>${d.open.toFixed(2)}</span>
                      <span style={{ color: '#64748b' }}>High:</span><span style={{ color: '#10b981', fontWeight: 600 }}>${d.high.toFixed(2)}</span>
                      <span style={{ color: '#64748b' }}>Low:</span><span style={{ color: '#ef4444', fontWeight: 600 }}>${d.low.toFixed(2)}</span>
                      <span style={{ color: '#64748b' }}>Close:</span><span style={{ color: isUp ? '#10b981' : '#ef4444', fontWeight: 600 }}>${d.close.toFixed(2)}</span>
                    </div>
                  </div>
                )
              }} />
              <Bar dataKey="close" shape={(props) => {
                const { x, y, width, height, payload } = props
                const isUp = payload.close >= payload.open
                const candleColor = payload.isFuture ? '#8b5cf6' : (isUp ? '#10b981' : '#ef4444')
                const opacity = payload.isFuture ? 0.6 : 1
                const priceRange = payload.high - payload.low
                if (priceRange === 0) return null
                const bodyTop = y + (payload.high - Math.max(payload.open, payload.close)) / priceRange * height
                const bodyHeight = Math.abs(payload.close - payload.open) / priceRange * height || 1
                const wickX = x + width / 2
                return (
                  <g opacity={opacity}>
                    <line x1={wickX} y1={y} x2={wickX} y2={bodyTop} stroke={candleColor} strokeWidth={1} />
                    <line x1={wickX} y1={bodyTop + bodyHeight} x2={wickX} y2={y + height} stroke={candleColor} strokeWidth={1} />
                    <rect x={x + width * 0.25} y={bodyTop} width={width * 0.5} height={Math.max(bodyHeight, 1)} fill={candleColor} />
                  </g>
                )
              }}>
                {allData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.isFuture ? '#8b5cf6' : (entry.close >= entry.open ? '#10b981' : '#ef4444')} />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 15 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, background: '#10b981', borderRadius: 2 }} />
            <span style={{ color: '#64748b', fontSize: 11 }}>Up</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, background: '#ef4444', borderRadius: 2 }} />
            <span style={{ color: '#64748b', fontSize: 11 }}>Down</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 10, height: 10, background: '#8b5cf6', borderRadius: 2 }} />
            <span style={{ color: '#64748b', fontSize: 11 }}>Predicted (Future)</span>
          </div>
        </div>
      </div>

      {/* AI Predictions */}
      <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(139,92,246,0.3)', borderRadius: 18, padding: 22, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <span style={{ fontSize: 18 }}>🔮</span>
          <h3 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14, margin: 0, fontFamily: "'Space Mono',monospace" }}>
            AI Future Predictions (Next 1 Hour)
          </h3>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {TIMEFRAMES.map(tf => {
            const pred = predictions[tf.label]
            if (!pred) return null
            return (
              <div key={tf.label} style={{ background: 'rgba(15,23,42,0.6)', border: `1px solid ${signalColors[pred.signal]}40`, borderRadius: 12, padding: 14, textAlign: 'center' }}>
                <div style={{ color: '#64748b', fontSize: 11, marginBottom: 6 }}>{tf.label} Prediction</div>
                <div style={{ color: '#f1f5f9', fontSize: 18, fontWeight: 800, fontFamily: "'Space Mono',monospace" }}>
                  ${pred.price.toFixed(symbol === 'BTC' ? 2 : 4)}
                </div>
                <div style={{ color: pred.profit > 0 ? '#10b981' : '#ef4444', fontSize: 13, fontWeight: 700, marginTop: 4, background: pred.profit > 0 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', padding: '2px 8px', borderRadius: 6, display: 'inline-block' }}>
                  {pred.profit > 0 ? '+' : ''}{pred.profit.toFixed(2)}%
                </div>
                <div style={{ marginTop: 8, padding: '4px 10px', borderRadius: 6, background: `${signalColors[pred.signal]}20`, color: signalColors[pred.signal], fontSize: 11, fontWeight: 700, display: 'inline-block' }}>
                  {pred.signal} • {pred.confidence.toFixed(0)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
