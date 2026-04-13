// Clean optimized API service
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// JWT interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('nexus_jwt')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

// 401 handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('nexus_jwt')
      localStorage.removeItem('nexus_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ─── Coin metadata (UI only — not from API) ────────────────────────────────────
// 10 coins for portfolio
export const ALL_COINS = [
  { symbol: 'BTC',  name: 'Bitcoin',           color: '#f7931a' },
  { symbol: 'ETH',  name: 'Ethereum',           color: '#627eea' },
  { symbol: 'BNB',  name: 'Binance Coin',       color: '#f3ba2f' },
  { symbol: 'SOL',  name: 'Solana',             color: '#9945ff' },
  { symbol: 'XRP',  name: 'Ripple',             color: '#00aae4' },
  { symbol: 'ADA',  name: 'Cardano',            color: '#0033ad' },
  { symbol: 'AVAX', name: 'Avalanche',          color: '#e84142' },
  { symbol: 'DOGE', name: 'Dogecoin',           color: '#c2a633' },
  { symbol: 'DOT',  name: 'Polkadot',           color: '#e6007a' },
  { symbol: 'LINK', name: 'Chainlink',          color: '#2a5ada' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────
function seededRng(seed) {
  let s = seed
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280 }
}

// Mock fallback generators (only used if backend is down)
function mockSignals() {
  const SIGS = ['BUY', 'SELL', 'HOLD']
  const MOM  = ['Strong bullish divergence on RSI', 'Bearish divergence detected', 'MACD golden cross confirmed', 'Oversold bounce signal', 'Institutional accumulation', 'Overbought — reversal likely']
  const TRD  = ['Breaking 50-day MA resistance', 'Failed support retest', 'Higher highs pattern forming', 'Descending triangle breakdown', 'Accumulation breakout', 'Cup and handle completing']
  const VOL  = ['3.2× average volume spike', 'Decreasing buy pressure', 'Institutional OBV signal', 'Smart money footprint', 'Below-average volume', 'Whale activity detected']
  return ALL_COINS.map((coin, i) => {
    const r = seededRng(i * 137 + 42)
    return {
      id:          i + 1,
      coin:        coin.symbol,
      name:        coin.name,
      color:       coin.color,
      signal:      SIGS[Math.floor(r() * 3)],
      probability: Math.floor(r() * 30) + 60,
      confidence:  Math.floor(r() * 35) + 55,
      momentum:    MOM[Math.floor(r() * MOM.length)],
      trend:       TRD[Math.floor(r() * TRD.length)],
      volume:      VOL[Math.floor(r() * VOL.length)],
      timestamp:   new Date(Date.now() - Math.floor(r() * 3600000)).toISOString(),
    }
  })
}

function mockEquity(days = 60) {
  const data = []
  let equity = 10000, benchmark = 10000
  for (let i = 0; i < days; i++) {
    equity    *= 1 + (Math.sin(i * 0.35) * 0.012 + (Math.random() - 0.46) * 0.025)
    benchmark *= 1 + (Math.random() - 0.47) * 0.015
    data.push({ day: `D${i + 1}`, equity: Math.round(equity * 100) / 100, benchmark: Math.round(benchmark * 100) / 100 })
  }
  return data
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUTH  —  /api/auth/login  |  /api/auth/register
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * POST /api/auth/login
 * Body: { email, password }
 * Returns: { access_token, token_type, user: { id, name, email, role, plan } }
 */
export async function login(email, password) {
  try {
    const { data } = await api.post('/api/auth/login', { email, password })
    // FastAPI OAuth2 returns access_token
    const token = data.access_token || data.token
    localStorage.setItem('nexus_jwt', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    const user = data.user || {
      id:    data.id    || 1,
      name:  data.name  || email.split('@')[0],
      email: data.email || email,
      role:  data.role  || 'user',
      plan:  data.plan  || 'PRO',
    }
    localStorage.setItem('nexus_user', JSON.stringify(user))
    return { token, user }
  } catch (error) {
    const msg = error.response?.data?.detail || error.response?.data?.message || 'Login failed'
    throw new Error(msg)
  }
}

/**
 * POST /api/auth/register
 * Body: { name, email, password }
 * Returns: { access_token, user }
 */
export async function register(name, email, password) {
  try {
    const { data } = await api.post('/api/auth/register', { name, email, password })
    const token = data.access_token || data.token
    localStorage.setItem('nexus_jwt', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    const user = data.user || { id: data.id, name, email, role: 'user', plan: 'FREE' }
    localStorage.setItem('nexus_user', JSON.stringify(user))
    return { token, user }
  } catch (error) {
    const msg = error.response?.data?.detail || error.response?.data?.message || 'Registration failed'
    throw new Error(msg)
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SIGNALS  —  /api/signals  |  /api/suggestions
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/signals
 * Query params: signal_type (BUY|SELL|HOLD|ALL), min_confidence (0-100), coin
 * Returns: [{ id, coin, name, signal, probability, confidence, momentum, trend, volume, timestamp }]
 */
export async function fetchSignals(filters = {}) {
  try {
    const params = {}
    if (filters.signal && filters.signal !== 'ALL') params.signal_type   = filters.signal
    if (filters.minConfidence)                       params.min_confidence = filters.minConfidence
    if (filters.coin)                               params.coin           = filters.coin
    const { data } = await api.get('/api/signals', { params })
    return Array.isArray(data) ? data : data.signals || []
  } catch (error) {
    console.warn('fetchSignals fallback to mock:', error.message)
    let signals = mockSignals()
    if (filters.signal && filters.signal !== 'ALL') signals = signals.filter(s => s.signal === filters.signal)
    if (filters.minConfidence) signals = signals.filter(s => s.confidence >= filters.minConfidence)
    return signals
  }
}

/**
 * GET /api/signals/current/{symbol}
 * Returns: { symbol, timestamp, signal, confidence, probability, live_data, prediction_1h, market_data }
 */
export async function fetchSignalWithLiveData(symbol) {
  try {
    const { data } = await api.get(`/api/signals/current/${symbol}`)
    return {
      symbol: data.symbol || symbol,
      signal: data.signal || 'HOLD',
      confidence: data.confidence ?? 50,
      probability: data.probability ?? 50,
      liveData: data.live_data || {},
      prediction1h: data.prediction_1h || {},
      marketData: data.market_data || {},
      timestamp: data.timestamp || new Date().toISOString()
    }
  } catch (error) {
    console.warn(`fetchSignalWithLiveData(${symbol}) failed:`, error.message)
    return null
  }
}

/**
 * GET /api/signals/batch?symbols=BTC,ETH,...
 * Returns: { signals: [...], count, timestamp }
 */
export async function fetchSignalsBatch(symbols, timeframe = '1h') {
  try {
    const symbolsParam = Array.isArray(symbols) ? symbols.join(',') : symbols
    const { data } = await api.get('/api/signals/batch', {
      params: { symbols: symbolsParam, timeframe }
    })
    return data.signals || []
  } catch (error) {
    console.warn('fetchSignalsBatch failed, using mock:', error.message)
    // Return mock signals that match the expected backend format
    const mockSigs = ALL_COINS.map((coin, i) => {
      const r = seededRng(i * 137 + 42 + timeframe.length)
      const signals = ['BUY', 'SELL', 'HOLD']
      const signal = signals[Math.floor(r() * 3)]
      const confidence = Math.floor(r() * 35) + 55
      const targetMultipliers = { '30m': 1.005, '1h': 1.01, '4h': 1.03, '1d': 1.08 }
      const basePrices = { 'BTC': 67500, 'ETH': 3450, 'BNB': 585, 'SOL': 145, 'XRP': 0.62 }
      const basePrice = basePrices[coin.symbol] || 100
      const targetMult = targetMultipliers[timeframe] || 1.01
      const predictedChange = signal === 'BUY' ? (r() * 2 + 0.5) : signal === 'SELL' ? -(r() * 2 + 0.5) : (r() - 0.5)
      return {
        symbol: coin.symbol + 'USDT',
        signal: signal,
        confidence: confidence,
        probability: confidence,
        timestamp: new Date().toISOString(),
        timeframe: timeframe,
        [`prediction_${timeframe}`]: {
          signal: signal,
          confidence: confidence,
          target_price: Math.round(basePrice * targetMult * (1 + predictedChange / 100)),
          predicted_change: parseFloat(predictedChange.toFixed(2))
        },
        live_data: {
          current_price: basePrice,
          price_change_24h: parseFloat((r() * 10 - 5).toFixed(2)),
          volume_24h: Math.floor(r() * 1000000000),
          trend: signal === 'BUY' ? 'BULLISH' : signal === 'SELL' ? 'BEARISH' : 'NEUTRAL',
          trend_score: confidence,
          rsi: Math.floor(r() * 40) + 30
        },
        market_data: {
          high_24h: Math.round(basePrice * 1.05),
          low_24h: Math.round(basePrice * 0.95),
          volume_24h: Math.floor(r() * 1000000000),
          volatility: parseFloat((r() * 5 + 1).toFixed(2))
        }
      }
    })
    return mockSigs
  }
}

/**
 * GET /api/signals/predictions/{timeframe}/{symbol}
 * Returns: { symbol, timestamp, current_price, prediction, technical_indicators, market_data, analysis }
 * timeframe: 30m, 1h, 4h, 1d
 */
export async function fetchPredictionByTimeframe(symbol, timeframe = '1h') {
  try {
    const { data } = await api.get(`/api/signals/current/${symbol}`, {
      params: { timeframe }
    })
    return {
      symbol: data.symbol || symbol,
      currentPrice: data.live_data?.current_price || 0,
      prediction: data[`prediction_${timeframe}`] || data.prediction_1h || {},
      technicalIndicators: data.live_data || {},
      marketData: data.market_data || {},
      analysis: {
        trend: data.live_data?.trend,
        trendScore: data.live_data?.trend_score,
        rsi: data.live_data?.rsi,
        signal: data.signal,
        confidence: data.confidence
      },
      timestamp: data.timestamp || new Date().toISOString(),
      timeframe: data.timeframe || timeframe
    }
  } catch (error) {
    console.warn(`fetchPredictionByTimeframe(${symbol}, ${timeframe}) failed:`, error.message)
    return null
  }
}

/**
 * GET /api/suggestions
 * Returns: [{ id, coin, name, signal, probability, confidence, ... }]
 * Top 5 high-confidence BUY opportunities
 */
export async function fetchSuggestions() {
  try {
    const { data } = await api.get('/api/suggestions')
    return Array.isArray(data) ? data : data.suggestions || []
  } catch (error) {
    console.warn('fetchSuggestions fallback to mock:', error.message)
    return mockSignals()
      .filter(s => s.signal === 'BUY' && s.confidence > 75)
      .slice(0, 5)
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PORTFOLIO  —  /api/portfolio
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/portfolio
 * Returns: { coins: ['BTC', 'ETH', ...], positions: [...] }
 */
export async function fetchPortfolio() {
  try {
    const { data } = await api.get('/api/portfolio')
    return {
      coins:     data.coins     || data.symbols    || [],
      positions: data.positions || data.holdings   || [],
    }
  } catch (error) {
    console.warn('fetchPortfolio fallback to mock:', error.message)
    return { coins: ['BTC', 'ETH', 'SOL', 'AVAX', 'INJ'], positions: [] }
  }
}

/**
 * POST /api/portfolio
 * Body: { coins: ['BTC', 'ETH', ...] }
 * Returns: { success: true, coins: [...] }
 */
export async function savePortfolio(coins) {
  try {
    const { data } = await api.post('/api/portfolio', { coins })
    return data
  } catch (error) {
    const msg = error.response?.data?.detail || 'Failed to save portfolio'
    throw new Error(msg)
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// LIVE TRADING  —  /api/live/*
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/live/price/{symbol}
 * Returns: { symbol, price, change_24h, change_1h, high_24h, low_24h, volume_24h, timestamp }
 */
export async function fetchLivePrice(symbol) {
  try {
    const { data } = await api.get(`/api/live/price/${symbol}`)
    return {
      symbol:    data.symbol    || symbol,
      price:     data.price     || data.current_price || 0,
      change24h: data.change_24h  ?? data.price_change_percentage_24h ?? 0,
      change1h:  data.change_1h   ?? data.price_change_percentage_1h  ?? 0,
      high24h:   data.high_24h    || data.high  || 0,
      low24h:    data.low_24h     || data.low   || 0,
      volume24h: data.volume_24h  || data.volume || 0,
      timestamp: data.timestamp  || new Date().toISOString(),
    }
  } catch (error) {
    console.warn(`fetchLivePrice(${symbol}) failed:`, error.message)
    return null
  }
}

/**
 * GET /api/predictions
 * Returns: { predictions: [{ symbol, current_price, prediction_1h, change_percent, confidence, signal, indicators }], count, timestamp }
 */
export async function fetchPredictions() {
  try {
    const { data } = await api.get('/api/predictions')
    return data.predictions || []
  } catch (error) {
    console.warn('fetchPredictions failed:', error.message)
    return []
  }
}

/**
 * GET /api/predictions/{symbol}
 * Returns: { symbol, current_price, prediction_1h, change_percent, confidence, signal, indicators }
 */
export async function fetchPrediction(symbol) {
  try {
    const { data } = await api.get(`/api/predictions/${symbol}`)
    return data
  } catch (error) {
    console.warn(`fetchPrediction(${symbol}) failed:`, error.message)
    return null
  }
}

/**
 * GET /api/live/klines/{symbol}
 * Query params: interval (30m, 1h, 4h, 1d), limit
 * Returns: { symbol, interval, candles: [{ time, open, high, low, close, volume }], timestamp }
 */
export async function fetchBinanceKlines(symbol, interval = '1h', limit = 100) {
  try {
    const { data } = await api.get(`/api/live/klines/${symbol}`, {
      params: { interval, limit }
    })
    return {
      symbol: data.symbol || symbol,
      interval: data.interval || interval,
      candles: data.candles || [],
      timestamp: data.timestamp || Date.now(),
    }
  } catch (error) {
    console.warn(`fetchBinanceKlines(${symbol}) failed:`, error.message)
    return { symbol, interval, candles: [], timestamp: Date.now() }
  }
}

/**
 * GET /api/live/klines/{symbol}
 * Query params: interval (30m, 1h, 4h, 1d), limit
 * Returns: { symbol, interval, candles: [...], analysis: {...}, timestamp }
 */
export async function fetchKlines(symbol, interval = '1h', limit = 60) {
  try {
    const { data } = await api.get(`/api/live/klines/${symbol}USDT`, { 
      params: { interval, limit } 
    })
    return {
      symbol:    data.symbol    || symbol,
      interval:  data.interval  || interval,
      candles:   data.candles   || [],
      analysis:  data.analysis  || {
        current_price: 0,
        price_change_24h: 0,
        trend: 'NEUTRAL',
        trend_score: 50,
        sma_7: 0,
        sma_20: 0,
        volatility: 0,
        volume_change: 0,
        high_24h: 0,
        low_24h: 0,
        support: 0,
        resistance: 0,
      },
      timestamp: data.timestamp || Date.now(),
    }
  } catch (error) {
    console.warn(`fetchKlines(${symbol}) failed:`, error.message)
    return null
  }
}

/**
 * GET /api/live/price/{symbol} — batch fetch for multiple symbols
 * Calls the endpoint once per symbol in parallel (use if your backend
 * doesn't have a batch endpoint)
 */
export async function fetchMultiplePrices(symbols) {
  const results = await Promise.allSettled(
    symbols.map(sym => fetchLivePrice(sym))
  )
  return results
    .map((r, i) => r.status === 'fulfilled' && r.value ? r.value : { symbol: symbols[i], price: 0, change24h: 0, change1h: 0 })
}

/**
 * POST /api/live/order
 * Body: { symbol, side (BUY|SELL), quantity, order_type (MARKET|LIMIT|STOP), price? }
 * Returns: { order_id, status, symbol, side, quantity, price, timestamp }
 */
export async function placeLiveOrder({ symbol, side, quantity, orderType = 'MARKET', price = null }) {
  try {
    const body = {
      symbol,
      side:       side.toUpperCase(),
      quantity,
      order_type: orderType.toUpperCase(),
    }
    if (price && orderType !== 'MARKET') body.price = price
    const { data } = await api.post('/api/live/order', body)
    return {
      orderId:   data.order_id   || data.orderId    || `mock_${Date.now()}`,
      status:    data.status     || 'OPEN',
      symbol:    data.symbol     || symbol,
      side:      data.side       || side,
      quantity:  data.quantity   || quantity,
      price:     data.price      || price || 0,
      timestamp: data.timestamp  || new Date().toISOString(),
    }
  } catch (error) {
    const msg = error.response?.data?.detail || error.response?.data?.message || 'Order placement failed'
    throw new Error(msg)
  }
}

/**
 * GET /api/live/account
 * Returns: { account_id, can_trade, balances: [...], positions: [...] }
 */
export async function fetchAccount() {
  try {
    const { data } = await api.get('/api/live/account')
    return {
      accountId:  data.account_id  || data.accountId  || '',
      canTrade:   data.can_trade   ?? data.canTrade   ?? true,
      balances:   data.balances    || [],
      positions:  data.positions   || [],
    }
  } catch (error) {
    console.warn('fetchAccount failed:', error.message)
    return { accountId: 'demo', canTrade: true, balances: [], positions: [] }
  }
}

/**
 * GET /api/live/balance
 * Returns: { total_usd, available_usd, in_positions_usd, pnl_today, pnl_total }
 */
export async function fetchBalance() {
  try {
    const { data } = await api.get('/api/live/balance')
    return {
      totalUsd:       data.total_usd       ?? data.totalUsd       ?? 0,
      availableUsd:   data.available_usd   ?? data.availableUsd   ?? 0,
      inPositionsUsd: data.in_positions_usd ?? data.inPositionsUsd ?? 0,
      pnlToday:       data.pnl_today       ?? data.pnlToday       ?? 0,
      pnlTotal:       data.pnl_total       ?? data.pnlTotal       ?? 0,
    }
  } catch (error) {
    console.warn('fetchBalance failed:', error.message)
    return { totalUsd: 24832, availableUsd: 18200, inPositionsUsd: 6632, pnlToday: 842, pnlTotal: 4832 }
  }
}

/**
 * GET /api/live/status
 * Returns: { connected, exchange, mode (live|paper|demo), active_orders, bot_running }
 */
export async function fetchTradingStatus() {
  try {
    const { data } = await api.get('/api/live/status')
    return {
      connected:    data.connected     ?? false,
      exchange:     data.exchange      || 'Binance',
      mode:         data.mode          || 'demo',
      activeOrders: data.active_orders ?? data.activeOrders ?? 0,
      botRunning:   data.bot_running   ?? data.botRunning   ?? false,
    }
  } catch (error) {
    console.warn('fetchTradingStatus failed:', error.message)
    return { connected: false, exchange: 'Binance', mode: 'demo', activeOrders: 0, botRunning: false }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MARKET  —  /api/market/status
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/market/status
 * Returns: { regime (BULL|BEAR|NEUTRAL), volatility (LOW|MEDIUM|HIGH), fear_greed, btc_dominance }
 */
export async function fetchMarketStatus() {
  try {
    const { data } = await api.get('/api/market/status')
    return {
      regime:      data.regime      || data.market_regime  || 'BULL',
      volatility:  data.volatility  || data.vol_regime     || 'MEDIUM',
      fearGreed:   data.fear_greed  ?? data.fearGreed      ?? 65,
      dominance:   data.btc_dominance ?? data.dominance    ?? 52.4,
    }
  } catch (error) {
    console.warn('fetchMarketStatus fallback to mock:', error.message)
    return { regime: 'BULL', volatility: 'MEDIUM', fearGreed: 65, dominance: 52.4 }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ANALYTICS  —  /api/analytics/equity
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/analytics/equity
 * Query params: days (default 60)
 * Returns: [{ day, equity, benchmark }]
 */
export async function fetchEquityCurve(days = 60) {
  try {
    const { data } = await api.get('/api/analytics/equity', { params: { days } })
    const raw = Array.isArray(data) ? data : data.equity || data.data || []
    return raw.map((item, i) => ({
      day:       item.day       || item.date      || `D${i + 1}`,
      equity:    item.equity    || item.value     || item.portfolio_value || 0,
      benchmark: item.benchmark || item.btc_value || 0,
    }))
  } catch (error) {
    console.warn('fetchEquityCurve fallback to mock:', error.message)
    return mockEquity(days)
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ADMIN  —  /api/admin/users
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/admin/users
 * Returns: [{ id, name, email, plan, role, joined, signals_used }]
 */
export async function fetchAdminUsers() {
  try {
    const { data } = await api.get('/api/admin/users')
    const users = Array.isArray(data) ? data : data.users || []
    return users.map(u => ({
      id:      u.id,
      name:    u.name     || u.username    || u.email.split('@')[0],
      email:   u.email,
      plan:    u.plan     || u.subscription || 'FREE',
      role:    u.role     || 'user',
      joined:  u.joined   || u.created_at  || u.createdAt || 'N/A',
      signals: u.signals  || u.signals_used || 0,
    }))
  } catch (error) {
    console.warn('fetchAdminUsers fallback to mock:', error.message)
    return [
      { id: 1, name: 'Amandeep',       email: 'amandeep@nexus.ai',  plan: 'ELITE', role: 'admin', joined: '2024-01-15', signals: 230 },
      { id: 2, name: 'Karan Sahoo',    email: 'karan@nexus.ai',     plan: 'PRO',   role: 'user',  joined: '2024-03-20', signals: 115 },
      { id: 3, name: 'Biswajit Das',   email: 'biswajit@nexus.ai',  plan: 'PRO',   role: 'user',  joined: '2024-04-02', signals: 22  },
      { id: 4, name: 'Priyabata Pradhan',   email: 'gudu@nexus.ai',      plan: 'PRO',   role: 'user',  joined: '2024-02-10', signals: 88 },
    ]
  }
}

/**
 * PATCH /api/admin/users/{id}
 * Body: { plan }
 * Returns: { success: true, user: {...} }
 */
export async function updateUserPlan(userId, plan) {
  try {
    const { data } = await api.patch(`/api/admin/users/${userId}`, { plan })
    return data
  } catch (error) {
    const msg = error.response?.data?.detail || 'Failed to update plan'
    throw new Error(msg)
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// BOT  —  /api/bot/start
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * POST /api/bot/start
 * Body: { strategy, coins, risk_level (low|medium|high), max_position_size }
 * Returns: { bot_id, status, message, started_at }
 */
export async function startBot({ strategy = 'ai_signals', coins = [], riskLevel = 'medium', maxPositionSize = 100 } = {}) {
  try {
    const { data } = await api.post('/api/bot/start', {
      strategy,
      coins,
      risk_level:        riskLevel,
      max_position_size: maxPositionSize,
    })
    return {
      botId:     data.bot_id    || data.botId    || `bot_${Date.now()}`,
      status:    data.status    || 'running',
      message:   data.message   || 'Bot started successfully',
      startedAt: data.started_at || new Date().toISOString(),
    }
  } catch (error) {
    const msg = error.response?.data?.detail || 'Failed to start bot'
    throw new Error(msg)
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// LIVE EXCEL  —  /api/live-excel/* (Auto-generated every 30 min)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/live-excel/status
 * Returns: { has_data, last_updated, next_update, predictions_count, coins, timeframes }
 */
export async function fetchLiveExcelStatus() {
  try {
    const { data } = await api.get('/api/live-excel/status')
    return data
  } catch (error) {
    console.warn('fetchLiveExcelStatus failed:', error.message)
    return null
  }
}

/**
 * GET /api/live-excel/download
 * Returns: Excel file (auto-generated every 30 min)
 */
export async function downloadLatestExcel() {
  try {
    const response = await api.get('/api/live-excel/download', {
      responseType: 'blob'
    })
    
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `live_predictions_${new Date().toISOString().slice(0,16).replace(/[T:]/g,'-')}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    return true
  } catch (error) {
    console.error('Download failed:', error)
    throw new Error('Failed to download latest Excel')
  }
}

/**
 * GET /api/live-excel/data
 * Query params: coin, timeframe, min_confidence
 * Returns: { count, last_updated, next_update, predictions }
 */
export async function fetchLivePredictionsData(coin = null, timeframe = null, minConfidence = 60) {
  try {
    const params = { min_confidence: minConfidence }
    if (coin) params.coin = coin
    if (timeframe) params.timeframe = timeframe
    
    const { data } = await api.get('/api/live-excel/data', { params })
    return data
  } catch (error) {
    console.warn('fetchLivePredictionsData failed:', error.message)
    return null
  }
}

/**
 * POST /api/live-excel/refresh
 * Force immediate regeneration of predictions
 */
export async function forceRefreshPredictions() {
  try {
    const { data } = await api.post('/api/live-excel/refresh')
    return data
  } catch (error) {
    console.error('Force refresh failed:', error)
    throw new Error('Failed to refresh predictions')
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXPORT  —  /api/export/*
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/export/predictions/excel
 * Query params: coins, timeframes, format
 * Returns: Excel file download
 */
export async function exportPredictionsToExcel(coins = null, timeframes = '30m,1h,4h,1d', format = 'xlsx') {
  try {
    const params = { timeframes, format }
    if (coins) params.coins = coins
    
    const response = await api.get('/api/export/predictions/excel', {
      params,
      responseType: 'blob'  // Important for file downloads
    })
    
    // Create download link
    const blob = new Blob([response.data], { 
      type: format === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `predictions_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    return true
  } catch (error) {
    console.error('Export failed:', error)
    throw new Error('Failed to export predictions')
  }
}

/**
 * GET /api/export/predictions/json
 * Returns predictions as JSON
 */
export async function exportPredictionsToJSON(coins = null, timeframes = '30m,1h,4h,1d') {
  try {
    const params = { timeframes }
    if (coins) params.coins = coins
    
    const { data } = await api.get('/api/export/predictions/json', { params })
    return data
  } catch (error) {
    console.error('Export failed:', error)
    throw new Error('Failed to export predictions')
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Legacy exports for backward compatibility
// ═══════════════════════════════════════════════════════════════════════════════
export { mockSignals as generateMockSignals }
export { mockEquity as generateEquityCurve }
export { fetchEquityCurve as getEquityCurve }

export default api
