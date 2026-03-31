import { useState, useEffect, useRef } from 'react'
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, Cell, ReferenceLine } from 'recharts'

export default function LiveTradingChart({ symbol = 'BTC', color = '#f7931a' }) {
  const [data, setData] = useState([])
  const [futureData, setFutureData] = useState([])
  const [timeRange, setTimeRange] = useState('5m')
  const [price, setPrice] = useState(0)
  const [change, setChange] = useState(0)
  const [predictions, setPredictions] = useState({})
  const [backtestResults, setBacktestResults] = useState(null)
  const [showBacktest, setShowBacktest] = useState(false)
  const intervalRef = useRef(null)

  const TIMEFRAMES = [
    { label: '5m', minutes: 5 },
    { label: '15m', minutes: 15 },
    { label: '30m', minutes: 30 },
    { label: '1h', minutes: 60 }
  ]

  const generateCandle = (prevClose, time, isFuture = false) => {
    const volatility = prevClose * 0.015
    const trendBias = isFuture ? (Math.random() - 0.3) * 0.02 : 0
    const open = prevClose
    const close = open + (Math.random() - 0.5 + trendBias) * volatility * 2
    const high = Math.max(open, close) + Math.random() * volatility * 0.8
    const low = Math.min(open, close) - Math.random() * volatility * 0.8
    const volume = Math.random() * 1000 + 500
    return { time, open, high, low, close, volume, isFuture }
  }

  const generatePredictions = (currentPrice) => {
    const predictions = {}
    let projectedPrice = currentPrice
    
    TIMEFRAMES.forEach((tf, idx) => {
      const hoursAhead = tf.minutes / 60
      const baseVolatility = 0.003 * Math.sqrt(hoursAhead)
      const volatility = baseVolatility
      
      const trendStrength = Math.sin(Date.now() / 60000 + idx) * 0.005
      const randomComponent = (Math.random() - 0.5) * volatility * 2
      
      const priceChangePercent = trendStrength + randomComponent
      projectedPrice = currentPrice * (1 + priceChangePercent)
      
      const profitPercent = Math.max(-5, Math.min(5, priceChangePercent * 100))
      
      const confidence = Math.min(95, 55 + Math.abs(profitPercent) * 3 + Math.random() * 10)
      const signal = profitPercent > 2 ? 'STRONG_BUY' : profitPercent > 0.5 ? 'BUY' : profitPercent < -2 ? 'STRONG_SELL' : profitPercent < -0.5 ? 'SELL' : 'HOLD'
      
      predictions[tf.label] = {
        price: projectedPrice,
        profit: profitPercent,
        confidence: confidence,
        signal: signal,
        direction: profitPercent > 0 ? 'up' : 'down'
      }
    })
    return predictions
  }

  const runBacktest = (historicalData, timeframe) => {
    if (historicalData.length < 10) return null
    
    const maShort = timeframe === '1H' ? 5 : timeframe === '24H' ? 6 : 7
    const maLong = timeframe === '1H' ? 10 : timeframe === '24H' ? 12 : 14
    
    let trades = 0
    let wins = 0
    let totalProfit = 0
    let maxDrawdown = 0
    let peak = 100
    let position = null
    let entryPrice = 0
    let equity = 100
    
    for (let i = 5; i < historicalData.length - 1; i++) {
      const current = historicalData[i]
      const shortMA = historicalData.slice(i - maShort, i).reduce((a, b) => a + b.close, 0) / maShort
      const longMA = historicalData.slice(i - maLong, i).reduce((a, b) => a + b.close, 0) / maLong
      
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

  const generateFutureCandles = (lastClose, timeframe) => {
    const future = []
    let currentPrice = lastClose
    const candleCount = 12 // Always 12 future candles (up to 1 hour)
    
    for (let i = 1; i <= candleCount; i++) {
      const time = `+${i * 5}m`
      const candle = generateCandle(currentPrice, time, true)
      future.push(candle)
      currentPrice = candle.close
    }
    return future
  }

  const formatTime = (date, format) => {
    if (format === 'time') return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (format === 'date') return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
  
  const generateInitialData = () => {
    const basePrice = symbol === 'BTC' ? 45000 : symbol === 'ETH' ? 2800 : 100
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
    
    const future = generateFutureCandles(currentPrice, timeRange)
    setFutureData(future)
    
    const backtest = runBacktest([...dataPoints])
    setBacktestResults(backtest)
    
    return dataPoints
  }

  useEffect(() => {
    const initialData = generateInitialData()
    setData(initialData)
    
    intervalRef.current = setInterval(() => {
      setData(prevData => {
        const lastPrice = prevData[prevData.length - 1]?.close || 45000
        const newCandle = generateCandle(lastPrice, formatTime(new Date(), timeRangeConfig[timeRange].format))
        const newData = [...prevData.slice(1), newCandle]
        
        setPrice(newCandle.close)
        const firstPrice = prevData[0]?.open || lastPrice
        setChange(((newCandle.close - firstPrice) / firstPrice) * 100)
        
        const newPredictions = generatePredictions(newCandle.close)
        setPredictions(newPredictions)
        
        const future = generateFutureCandles(newCandle.close, timeRange)
        setFutureData(future)
        
        const backtest = runBacktest(newData, timeRange)
        setBacktestResults(backtest)
        
        return newData
      })
    }, 5000)

    return () => clearInterval(intervalRef.current)
  }, [symbol, timeRange])

  const timeRangeConfig = {
    '1m': { interval: 60000, points: 60, label: '1m', format: 'time' },
    '5m': { interval: 300000, points: 60, label: '5m', format: 'time' },
    '15m': { interval: 900000, points: 60, label: '15m', format: 'time' },
    '30m': { interval: 1800000, points: 60, label: '30m', format: 'time' },
    '1H': { interval: 3600000, points: 24, label: '1H', format: 'time' },
    '4H': { interval: 14400000, points: 30, label: '4H', format: 'datetime' },
    '1D': { interval: 86400000, points: 30, label: '1D', format: 'date' },
    '7D': { interval: 604800000, points: 12, label: '1W', format: 'date' },
    '30D': { interval: 2592000000, points: 30, label: '1M', format: 'date' }
  }
  
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

      {/* Backtesting */}
      <div style={{ background: 'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border: '1px solid rgba(71,85,105,0.35)', borderRadius: 18, padding: 22 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>📊</span>
            <h3 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14, margin: 0, fontFamily: "'Space Mono',monospace" }}>
              Backtesting Results
            </h3>
          </div>
          <button onClick={() => setShowBacktest(!showBacktest)}
            style={{ padding: '6px 14px', borderRadius: 8, background: showBacktest ? 'rgba(139,92,246,0.2)' : 'transparent', border: `1px solid ${showBacktest ? 'rgba(139,92,246,0.5)' : 'rgba(71,85,105,0.3)'}`, color: showBacktest ? '#a78bfa' : '#64748b', cursor: 'pointer', fontSize: 11, fontWeight: 700 }}>
            {showBacktest ? 'Hide Details' : 'Show Details'}
          </button>
        </div>

        {backtestResults && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
              {[['Trades', backtestResults.trades], ['Win Rate', `${backtestResults.winRate}%`], 
                ['Total Profit', `${backtestResults.totalProfit}%`], ['Max Drawdown', `${backtestResults.maxDrawdown}%`],
                ['Avg Profit', `${backtestResults.avgProfit}%`], ['Sharpe', backtestResults.sharpe]
              ].map(([label, val]) => (
                <div key={label} style={{ textAlign: 'center', padding: '10px', background: 'rgba(15,23,42,0.4)', borderRadius: 10 }}>
                  <div style={{ color: '#64748b', fontSize: 10, marginBottom: 4, textTransform: 'uppercase' }}>{label}</div>
                  <div style={{ color: (label === 'Total Profit' || label === 'Win Rate') && parseFloat(val) > 0 ? '#10b981' : (label === 'Total Profit' || label === 'Max Drawdown') && parseFloat(val) < 0 ? '#ef4444' : '#f1f5f9', fontSize: 16, fontWeight: 800, fontFamily: "'Space Mono',monospace" }}>
                    {val}
                  </div>
                </div>
              ))}
            </div>

            {showBacktest && (
              <div style={{ marginTop: 16, padding: 14, background: 'rgba(15,23,42,0.5)', borderRadius: 12 }}>
                <h4 style={{ color: '#a78bfa', fontSize: 12, margin: '0 0 10px' }}>Strategy Details</h4>
                <p style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.6, margin: 0 }}>
                  <strong style={{ color: '#f1f5f9' }}>Strategy:</strong> Moving Average Crossover (5-period vs 10-period)<br/><br/>
                  <strong style={{ color: '#f1f5f9' }}>Entry:</strong> When short MA crosses above long MA with price above both MAs<br/><br/>
                  <strong style={{ color: '#f1f5f9' }}>Exit:</strong> When short MA crosses below long MA OR stop-loss at 2%<br/><br/>
                  <strong style={{ color: '#f1f5f9' }}>Period:</strong> Last {timeRange} of historical data<br/><br/>
                  <strong style={{ color: '#f1f5f9' }}>Risk Management:</strong> Fixed position size, no leverage applied
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
