import { useState, useEffect, useRef, useCallback } from 'react'

export function useChartData(symbol, timeRange) {
  const [data, setData] = useState([])
  const [futureData, setFutureData] = useState([])
  const [price, setPrice] = useState(0)
  const [change, setChange] = useState(0)
  const [predictions, setPredictions] = useState({})
  const [backtestResults, setBacktestResults] = useState(null)
  const intervalRef = useRef(null)

  const TIMEFRAMES = [
    { label: '5m', minutes: 5 },
    { label: '15m', minutes: 15 },
    { label: '30m', minutes: 30 },
    { label: '1h', minutes: 60 }
  ]

  const generateCandle = useCallback((prevClose, time, isFuture = false) => {
    const volatility = prevClose * 0.015
    const trendBias = isFuture ? (Math.random() - 0.3) * 0.02 : 0
    const open = prevClose
    const close = open + (Math.random() - 0.5 + trendBias) * volatility * 2
    const high = Math.max(open, close) + Math.random() * volatility * 0.8
    const low = Math.min(open, close) - Math.random() * volatility * 0.8
    const volume = Math.random() * 1000 + 500
    return { time, open, high, low, close, volume, isFuture }
  }, [])

  const generatePredictions = useCallback((currentPrice) => {
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
  }, [])

  const generateFutureCandles = useCallback((lastClose) => {
    const future = []
    let currentPrice = lastClose
    for (let i = 1; i <= 12; i++) {
      const time = `+${i * 5}m`
      const candle = generateCandle(currentPrice, time, true)
      future.push(candle)
      currentPrice = candle.close
    }
    return future
  }, [generateCandle])

  const runBacktest = useCallback((historicalData) => {
    if (historicalData.length < 10) return null
    let trades = 0, wins = 0, totalProfit = 0, maxDrawdown = 0, peak = 100, position = null, entryPrice = 0, equity = 100
    
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
    
    return { trades, winRate: trades > 0 ? ((wins / trades) * 100).toFixed(1) : 0, totalProfit: totalProfit.toFixed(2), maxDrawdown: maxDrawdown.toFixed(2), avgProfit: trades > 0 ? (totalProfit / trades).toFixed(2) : 0, sharpe: trades > 0 ? (totalProfit / Math.max(1, maxDrawdown)).toFixed(2) : 0 }
  }, [])

  const generateInitialData = useCallback(() => {
    const basePrice = symbol === 'BTC' ? 45000 : symbol === 'ETH' ? 2800 : 100
    const points = 20
    const dataPoints = []
    let currentPrice = basePrice
    
    for (let i = 0; i < points; i++) {
      const time = new Date(Date.now() - (points - i) * 300000)
      const candle = generateCandle(currentPrice, time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
      dataPoints.push(candle)
      currentPrice = candle.close
    }
    
    setPrice(currentPrice)
    setChange(((currentPrice - basePrice) / basePrice) * 100)
    setPredictions(generatePredictions(currentPrice))
    const future = generateFutureCandles(currentPrice)
    setFutureData(future)
    setBacktestResults(runBacktest(dataPoints))
    
    return dataPoints
  }, [symbol, generateCandle, generatePredictions, generateFutureCandles, runBacktest])

  useEffect(() => {
    const initialData = generateInitialData()
    setData(initialData)
    
    intervalRef.current = setInterval(() => {
      setData(prevData => {
        const lastPrice = prevData[prevData.length - 1]?.close || 45000
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        const newCandle = generateCandle(lastPrice, time)
        const newData = [...prevData.slice(1), newCandle]
        setPrice(newCandle.close)
        setChange(((newCandle.close - (prevData[0]?.open || lastPrice)) / (prevData[0]?.open || lastPrice)) * 100)
        setPredictions(generatePredictions(newCandle.close))
        setFutureData(generateFutureCandles(newCandle.close))
        setBacktestResults(runBacktest(newData))
        return newData
      })
    }, 5000)

    return () => clearInterval(intervalRef.current)
  }, [symbol, timeRange, generateCandle, generateInitialData, generatePredictions, generateFutureCandles, runBacktest])

  return { data, futureData, price, change, predictions, backtestResults, TIMEFRAMES }
}

export function useSignalColor() {
  return {
    STRONG_BUY: '#10b981',
    BUY: '#34d399',
    HOLD: '#fbbf24',
    SELL: '#ef4444',
    STRONG_SELL: '#dc2626'
  }
}

export function formatPrice(price, symbol) {
  return `$${price.toFixed(symbol === 'BTC' ? 2 : 4)}`
}

export function formatPercent(value) {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}
