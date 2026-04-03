from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import httpx
import asyncio
import time
import jwt
import hashlib
import os
import json
import numpy as np
from datetime import datetime, timedelta

app = FastAPI(title="NEXUS AI Trading API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "nexus_secret_key_change_in_production")
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
COINGECKO_BASE     = "https://api.coingecko.com/api/v3"
BINANCE_BASE       = "https://api.binance.com/api/v3"

security = HTTPBearer(auto_error=False)

# ── In-memory store (replace with DB in production) ──────────────────────────
USERS_DB = {
    "amandeep@nexus.ai": {
        "id": 1, "name": "Amandeep", "email": "amandeep@nexus.ai",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin", "plan": "ELITE",
    },
    "karan@nexus.ai": {
        "id": 2, "name": "Karan Sahoo", "email": "karan@nexus.ai",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user", "plan": "PRO",
    },
    "biswajit@nexus.ai": {
        "id": 3, "name": "Biswajit Das", "email": "biswajit@nexus.ai",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user", "plan": "PRO",
    },
    "gudu@nexus.ai": {
        "id": 4, "name": "Gudu Pradhan", "email": "gudu@nexus.ai",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user", "plan": "PRO",
    },
}

COIN_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana",  "XRP": "ripple",   "ADA": "cardano",
    "AVAX":"avalanche-2", "DOGE":"dogecoin", "DOT":"polkadot",
    "LINK":"chainlink", "MATIC":"matic-network", "LTC":"litecoin",
    "BCH": "bitcoin-cash", "UNI":"uniswap",  "ATOM":"cosmos",
    "XLM": "stellar", "ICP":"internet-computer", "APT":"aptos",
    "ARB": "arbitrum", "OP":"optimism",   "PEPE":"pepe",
    "SHIB":"shiba-inu","RNDR":"render-token","INJ":"injective-protocol",
    "SUI": "sui",      "SEI":"sei-network", "KAS":"kaspa",
    "FTM": "fantom",   "GRT":"the-graph",   "RUNE":"thorchain",
}

# ── Auth helpers ──────────────────────────────────────────────────────────────
def create_token(user: dict) -> str:
    payload = {
        "sub":   user["email"],
        "id":    user["id"],
        "role":  user["role"],
        "exp":   datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        email   = payload.get("sub")
        user    = USERS_DB.get(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ── Models ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class PortfolioRequest(BaseModel):
    coins: List[str]

# ════════════════════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = USERS_DB.get(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    ph = hashlib.sha256(req.password.encode()).hexdigest()
    if ph != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "id":    user["id"],
            "name":  user["name"],
            "email": user["email"],
            "role":  user["role"],
            "plan":  user["plan"],
        },
    }

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    if req.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = {
        "id":            len(USERS_DB) + 1,
        "name":          req.name,
        "email":         req.email,
        "password_hash": hashlib.sha256(req.password.encode()).hexdigest(),
        "role":          "user",
        "plan":          "FREE",
    }
    USERS_DB[req.email] = new_user
    token = create_token(new_user)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {k: new_user[k] for k in ["id","name","email","role","plan"]},
    }

# ════════════════════════════════════════════════════════════════════════════════
# LIVE PRICE — fetches from CoinGecko
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/live/price/{symbol}")
async def get_live_price(symbol: str, user=Depends(get_current_user)):
    symbol = symbol.upper()
    coin_id = COIN_IDS.get(symbol)
    if not coin_id:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not supported")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids":         coin_id,
                    "sparkline":   "false",
                    "price_change_percentage": "1h,24h",
                }
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                raise HTTPException(status_code=404, detail="Coin data not found")
            c = data[0]
            return {
                "symbol":    symbol,
                "price":     c["current_price"],
                "change_24h":c.get("price_change_percentage_24h", 0),
                "change_1h": c.get("price_change_percentage_1h_in_currency", 0),
                "high_24h":  c.get("high_24h", 0),
                "low_24h":   c.get("low_24h", 0),
                "volume_24h":c.get("total_volume", 0),
                "market_cap":c.get("market_cap", 0),
                "rank":      c.get("market_cap_rank", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="CoinGecko timeout")

@app.get("/api/live/prices")
async def get_multiple_prices(symbols: str, user=Depends(get_current_user)):
    """Batch price fetch. symbols=BTC,ETH,SOL"""
    syms   = [s.strip().upper() for s in symbols.split(",")]
    ids    = [COIN_IDS[s] for s in syms if s in COIN_IDS]
    if not ids:
        raise HTTPException(status_code=400, detail="No valid symbols")
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids":         ",".join(ids),
                    "sparkline":   "true",
                    "price_change_percentage": "1h,24h,7d",
                }
            )
            r.raise_for_status()
            data = r.json()
            id_to_sym = {v: k for k, v in COIN_IDS.items()}
            result = []
            for c in data:
                sym = id_to_sym.get(c["id"], c["symbol"].upper())
                result.append({
                    "symbol":    sym,
                    "name":      c["name"],
                    "price":     c["current_price"],
                    "change_24h":c.get("price_change_percentage_24h", 0),
                    "change_1h": c.get("price_change_percentage_1h_in_currency", 0),
                    "change_7d": c.get("price_change_percentage_7d_in_currency", 0),
                    "high_24h":  c.get("high_24h", 0),
                    "low_24h":   c.get("low_24h", 0),
                    "volume_24h":c.get("total_volume", 0),
                    "market_cap":c.get("market_cap", 0),
                    "rank":      c.get("market_cap_rank", 0),
                    "sparkline": c.get("sparkline_in_7d", {}).get("price", []),
                    "timestamp": datetime.utcnow().isoformat(),
                })
            return result
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="CoinGecko timeout")

# ════════════════════════════════════════════════════════════════════════════════
# SIGNALS
# ════════════════════════════════════════════════════════════════════════════════

def compute_signal(change_24h: float, change_1h: float) -> dict:
    """Simple rule-based signal from price data."""
    if change_24h > 3 and change_1h > 0:
        return {"signal":"BUY",  "probability":min(95,70+int(abs(change_24h)*2)), "confidence":min(92,68+int(abs(change_1h)*5))}
    if change_24h > 1:
        return {"signal":"BUY",  "probability":min(85,62+int(abs(change_24h)*3)), "confidence":min(82,60+int(abs(change_24h)*4))}
    if change_24h < -3 and change_1h < 0:
        return {"signal":"SELL", "probability":min(93,68+int(abs(change_24h)*2)), "confidence":min(90,66+int(abs(change_1h)*4))}
    if change_24h < -1:
        return {"signal":"SELL", "probability":min(83,60+int(abs(change_24h)*3)), "confidence":min(80,58+int(abs(change_24h)*3))}
    return {"signal":"HOLD", "probability":55, "confidence":58}

MOMENTUM_MAP = {
    "BUY":  ["Strong bullish divergence on RSI","MACD golden cross confirmed","Oversold bounce signal","Institutional accumulation","Bullish engulfing candle"],
    "SELL": ["Bearish divergence on RSI","Death cross forming","Overbought — reversal likely","Failed support retest","Selling pressure increasing"],
    "HOLD": ["Consolidating near resistance","Mixed signals on lower TF","Range-bound trading","Awaiting breakout confirmation","Low volume sideways"],
}
TREND_MAP = {
    "BUY":  ["Breaking 50-day MA resistance","Higher highs pattern forming","Accumulation breakout","Cup and handle completing","Support level holding"],
    "SELL": ["Descending triangle breakdown","Lower lows forming","Double top near ATH","Resistance rejection","Below key moving averages"],
    "HOLD": ["Sideways channel","Coiling near key level","No clear direction","Watching for breakout","Neutral trend"],
}

@app.get("/api/signals")
async def get_signals(
    signal_type: Optional[str] = None,
    min_confidence: Optional[int] = None,
    user=Depends(get_current_user)
):
    syms = list(COIN_IDS.keys())
    ids  = list(COIN_IDS.values())
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids":         ",".join(ids),
                    "price_change_percentage": "1h,24h",
                    "per_page":    50,
                }
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            data = []

    id_to_sym = {v: k for k, v in COIN_IDS.items()}
    signals   = []
    import random, hashlib as hs

    for i, c in enumerate(data):
        sym  = id_to_sym.get(c["id"], c["symbol"].upper())
        ch24 = c.get("price_change_percentage_24h", 0) or 0
        ch1  = c.get("price_change_percentage_1h_in_currency", 0) or 0
        sig  = compute_signal(ch24, ch1)

        # Deterministic pick for momentum/trend based on symbol
        seed = int(hs.md5(sym.encode()).hexdigest(), 16)
        mom_pool = MOMENTUM_MAP[sig["signal"]]
        trd_pool = TREND_MAP[sig["signal"]]
        momentum = mom_pool[seed % len(mom_pool)]
        trend    = trd_pool[(seed // 7) % len(trd_pool)]

        entry = {
            "id":          i + 1,
            "coin":        sym,
            "name":        c["name"],
            "signal":      sig["signal"],
            "probability": sig["probability"],
            "confidence":  sig["confidence"],
            "momentum":    momentum,
            "trend":       trend,
            "volume":      f"{(c.get('total_volume',0)/1e9):.2f}B avg volume",
            "price":       c["current_price"],
            "change_24h":  ch24,
            "timestamp":   datetime.utcnow().isoformat(),
        }
        if signal_type and signal_type != "ALL" and entry["signal"] != signal_type:
            continue
        if min_confidence and entry["confidence"] < min_confidence:
            continue
        signals.append(entry)

    return signals

@app.get("/api/suggestions")
async def get_suggestions(user=Depends(get_current_user)):
    all_sigs = await get_signals(user=user)
    buy_sigs = [s for s in all_sigs if s["signal"] == "BUY"]
    buy_sigs.sort(key=lambda x: x["confidence"], reverse=True)
    return buy_sigs[:5]

# ════════════════════════════════════════════════════════════════════════════════
# PORTFOLIO
# ════════════════════════════════════════════════════════════════════════════════

USER_PORTFOLIOS = {}

@app.get("/api/portfolio")
async def get_portfolio(user=Depends(get_current_user)):
    coins = USER_PORTFOLIOS.get(user["email"], ["BTC","ETH","SOL","AVAX","INJ"])
    return {"coins": coins, "positions": []}

@app.post("/api/portfolio")
async def save_portfolio(req: PortfolioRequest, user=Depends(get_current_user)):
    USER_PORTFOLIOS[user["email"]] = req.coins
    return {"success": True, "coins": req.coins}

# ════════════════════════════════════════════════════════════════════════════════
# LIVE BALANCE & STATUS (mock Binance — replace with real SDK)
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/live/balance")
async def get_balance(user=Depends(get_current_user)):
    # Replace with real Binance SDK call:
    # from binance.client import Client
    # client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
    # account = client.get_account()
    return {
        "total_usd":        24832.0,
        "available_usd":    18200.0,
        "in_positions_usd": 6632.0,
        "pnl_today":        842.0,
        "pnl_total":        4832.0,
    }

@app.get("/api/live/account")
async def get_account(user=Depends(get_current_user)):
    return {
        "account_id": "demo_account",
        "can_trade":  True,
        "balances":   [{"asset":"USDT","free":"18200.00","locked":"0.00"}],
        "positions":  [
            {"symbol":"BTC","qty":0.15,"entry":64200,"current":0},
            {"symbol":"ETH","qty":2.4, "entry":3380, "current":0},
            {"symbol":"SOL","qty":12,  "entry":176,  "current":0},
        ],
    }

@app.get("/api/live/status")
async def get_trading_status(user=Depends(get_current_user)):
    return {
        "connected":     bool(BINANCE_API_KEY),
        "exchange":      "Binance",
        "mode":          "paper" if not BINANCE_API_KEY else "live",
        "active_orders": 0,
        "bot_running":   False,
    }

# ════════════════════════════════════════════════════════════════════════════════
# MARKET STATUS
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/market/status")
async def get_market_status(user=Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{COINGECKO_BASE}/global")
            r.raise_for_status()
            g = r.json()["data"]
            mcap_change = g.get("market_cap_change_percentage_24h_usd", 0) or 0
            regime      = "BULL" if mcap_change > 0 else "BEAR"
            volatility  = "HIGH" if abs(mcap_change) > 5 else "MEDIUM" if abs(mcap_change) > 2 else "LOW"
            return {
                "regime":       regime,
                "volatility":   volatility,
                "fear_greed":   65,
                "btc_dominance":round(g.get("market_cap_percentage", {}).get("btc", 52.4), 1),
                "total_market_cap": g.get("total_market_cap", {}).get("usd", 0),
                "total_volume_24h": g.get("total_volume", {}).get("usd", 0),
                "active_cryptos":   g.get("active_cryptocurrencies", 0),
                "mcap_change_24h":  mcap_change,
            }
        except Exception:
            return {"regime":"BULL","volatility":"MEDIUM","fear_greed":65,"btc_dominance":52.4}

# ════════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/analytics/equity")
async def get_equity_curve(days: int = 60, user=Depends(get_current_user)):
    import math, random
    data  = []
    eq    = 10000.0
    bench = 10000.0
    for i in range(days):
        eq    *= 1 + (math.sin(i * 0.35) * 0.012 + (random.random() - 0.46) * 0.025)
        bench *= 1 + (random.random() - 0.47) * 0.015
        data.append({
            "day":       f"D{i+1}",
            "equity":    round(eq, 2),
            "benchmark": round(bench, 2),
        })
    return data

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/admin/users")
async def get_admin_users(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return [
        {"id":u["id"],"name":u["name"],"email":u["email"],"plan":u["plan"],"role":u["role"],"joined":"2024-01-15","signals":230}
        for u in USERS_DB.values()
    ]

@app.patch("/api/admin/users/{user_id}")
async def update_user_plan(user_id: int, body: dict, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    for u in USERS_DB.values():
        if u["id"] == user_id:
            u["plan"] = body.get("plan", u["plan"])
            return {"success": True}
    raise HTTPException(status_code=404, detail="User not found")

# ════════════════════════════════════════════════════════════════════════════════
# BOT
# ════════════════════════════════════════════════════════════════════════════════

@app.post("/api/bot/start")
async def start_bot(body: dict, user=Depends(get_current_user)):
    return {
        "bot_id":     f"bot_{int(time.time())}",
        "status":     "running",
        "message":    "Bot started with AI signals strategy",
        "started_at": datetime.utcnow().isoformat(),
    }

# ════════════════════════════════════════════════════════════════════════════════
# BINANCE LIVE DATA & PREDICTIONS
# ════════════════════════════════════════════════════════════════════════════════

async def fetch_binance_klines(symbol: str, interval: str = "1h", limit: int = 100):
    """Fetch candlestick data from Binance"""
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(
                f"{BINANCE_BASE}/klines",
                params={
                    "symbol": symbol.upper() + "USDT",
                    "interval": interval,
                    "limit": limit
                }
            )
            r.raise_for_status()
            data = r.json()
            # Binance format: [open_time, open, high, low, close, volume, ...]
            candles = []
            for d in data:
                candles.append({
                    "time": d[0],
                    "open": float(d[1]),
                    "high": float(d[2]),
                    "low": float(d[3]),
                    "close": float(d[4]),
                    "volume": float(d[5]),
                })
            return candles
        except Exception as e:
            print(f"Binance klines error for {symbol}: {e}")
            return []

def generate_prediction(candles: list, symbol: str) -> dict:
    """Generate 1-hour price prediction using technical analysis"""
    if len(candles) < 20:
        return {
            "symbol": symbol,
            "current_price": 0,
            "prediction_1h": 0,
            "change_percent": 0,
            "confidence": 50,
            "signal": "HOLD",
            "indicators": {}
        }
    
    closes = np.array([c["close"] for c in candles])
    highs = np.array([c["high"] for c in candles])
    lows = np.array([c["low"] for c in candles])
    volumes = np.array([c["volume"] for c in candles])
    
    current_price = closes[-1]
    
    # Simple Moving Averages
    sma_7 = np.mean(closes[-7:])
    sma_20 = np.mean(closes[-20:])
    
    # RSI calculation (14-period)
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
    avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = np.mean(closes[-12:])
    ema_26 = np.mean(closes[-26:]) if len(closes) >= 26 else np.mean(closes[-12:])
    macd = ema_12 - ema_26
    
    # Bollinger Bands
    sma_20 = np.mean(closes[-20:])
    std_20 = np.std(closes[-20:])
    upper_band = sma_20 + (std_20 * 2)
    lower_band = sma_20 - (std_20 * 2)
    
    # Volume analysis
    avg_volume = np.mean(volumes[-20:])
    recent_volume = np.mean(volumes[-5:])
    volume_trend = recent_volume / (avg_volume + 1e-10)
    
    # Price momentum (last 5 candles)
    momentum = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    
    # Support and Resistance
    support = np.min(lows[-20:])
    resistance = np.max(highs[-20:])
    
    # Generate prediction using weighted ensemble
    # ML Prediction: Trend following
    ml_change = momentum * 0.6 + (volume_trend - 1) * 2
    
    # SMA Crossover prediction
    sma_signal = 1 if sma_7 > sma_20 else -1
    sma_change = abs(sma_7 - sma_20) / sma_20 * 100 * sma_signal
    
    # RSI Mean reversion
    if rsi > 70:
        rsi_signal = -1  # Overbought, expect down
    elif rsi < 30:
        rsi_signal = 1   # Oversold, expect up
    else:
        rsi_signal = 0
    rsi_change = (50 - rsi) / 10
    
    # MACD signal
    macd_signal = 1 if macd > 0 else -1
    macd_change = abs(macd) / current_price * 100 * macd_signal
    
    # Bollinger Bands signal
    bb_position = (current_price - lower_band) / (upper_band - lower_band + 1e-10)
    if bb_position > 0.9:
        bb_signal = -1  # Near upper band
    elif bb_position < 0.1:
        bb_signal = 1   # Near lower band
    else:
        bb_signal = 0
    bb_change = (0.5 - bb_position) * 5
    
    # Ensemble prediction (weighted average)
    ensemble_change = (
        ml_change * 0.30 +
        sma_change * 0.25 +
        rsi_change * 0.20 +
        macd_change * 0.15 +
        bb_change * 0.10
    )
    
    # Limit prediction to realistic bounds
    ensemble_change = max(-5, min(5, ensemble_change))
    
    prediction_price = current_price * (1 + ensemble_change / 100)
    
    # Determine signal
    if ensemble_change > 1.5:
        signal = "BUY"
        confidence = min(95, 60 + abs(ensemble_change) * 10)
    elif ensemble_change < -1.5:
        signal = "SELL"
        confidence = min(95, 60 + abs(ensemble_change) * 10)
    else:
        signal = "HOLD"
        confidence = 50 + abs(ensemble_change) * 5
    
    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "prediction_1h": round(prediction_price, 2),
        "change_percent": round(ensemble_change, 2),
        "confidence": round(confidence, 1),
        "signal": signal,
        "indicators": {
            "rsi": round(rsi, 1),
            "macd": round(macd, 4),
            "sma_7": round(sma_7, 2),
            "sma_20": round(sma_20, 2),
            "upper_band": round(upper_band, 2),
            "lower_band": round(lower_band, 2),
            "volume_trend": round(volume_trend, 2),
            "momentum": round(momentum, 2),
            "support": round(support, 2),
            "resistance": round(resistance, 2),
        }
    }

@app.get("/api/live/klines/{symbol}")
async def get_klines(symbol: str, interval: str = "1h", limit: int = 100, user=Depends(get_current_user)):
    """Get Binance candlestick data for live charts"""
    candles = await fetch_binance_klines(symbol, interval, limit)
    if not candles:
        raise HTTPException(status_code=500, detail="Failed to fetch klines from Binance")
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "candles": candles,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/predictions/{symbol}")
async def get_prediction(symbol: str, user=Depends(get_current_user)):
    """Get 1-hour AI prediction for a specific coin"""
    candles = await fetch_binance_klines(symbol, "1h", 50)
    if not candles:
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
    
    prediction = generate_prediction(candles, symbol.upper())
    return prediction

@app.get("/api/predictions")
async def get_all_predictions(user=Depends(get_current_user)):
    """Get 1-hour AI predictions for all supported coins"""
    symbols = list(COIN_IDS.keys())
    
    # Fetch data for all coins concurrently
    async def fetch_and_predict(symbol):
        try:
            candles = await fetch_binance_klines(symbol, "1h", 50)
            if candles:
                return generate_prediction(candles, symbol)
            return None
        except Exception as e:
            print(f"Error predicting {symbol}: {e}")
            return None
    
    # Run all predictions concurrently
    tasks = [fetch_and_predict(sym) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    predictions = []
    for sym, result in zip(symbols, results):
        if isinstance(result, dict) and result:
            predictions.append(result)
    
    # Sort by confidence (highest first)
    predictions.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "predictions": predictions,
        "count": len(predictions),
        "timestamp": datetime.utcnow().isoformat()
    }


# ════════════════════════════════════════════════════════════════════════════════
# 24/7 AUTOMATION API
# ════════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize database and start the 24/7 automation service"""
    try:
        # Initialize database tables
        from db.database import init_db
        init_db()
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")
    
    try:
        from services.market_automation import start_automation
        # Start with the 17 coins that have loaded models
        coins = [
            "BTC", "ETH", "BNB", "SOL", "XRP",
            "ADA", "AVAX", "DOGE", "DOT", "LINK",
            "MATIC", "LTC", "BCH", "UNI", "ATOM",
            "XLM", "ICP"
        ]
        start_automation(coins)
        print("✅ 24/7 Market Data Automation started")
    except Exception as e:
        print(f"⚠️ Failed to start automation: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the automation service when the app shuts down"""
    try:
        from services.market_automation import stop_automation
        stop_automation()
        print("⏹️ Automation stopped")
    except Exception as e:
        print(f"⚠️ Error stopping automation: {e}")

@app.get("/api/automation/status")
async def get_automation_status(user=Depends(get_current_user)):
    """Get 24/7 automation status and latest data"""
    try:
        from services.market_automation import get_automation_status as get_status
        status = get_status()
        if status:
            return {
                "running": True,
                "coins_tracked": status["coins_tracked"],
                "last_fetch": status["last_fetch"].isoformat() if status["last_fetch"] else None,
                "last_prediction": status["last_prediction"].isoformat() if status["last_prediction"] else None,
                "predictions_count": len(status["predictions"]),
                "signals_count": len(status["signals"]),
                "timestamp": datetime.utcnow().isoformat()
            }
        return {"running": False, "message": "Automation not running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation/live-data")
async def get_live_automation_data(user=Depends(get_current_user)):
    """Get live market data, predictions, and signals from automation"""
    try:
        from services.market_automation import get_automation_status as get_status
        status = get_status()
        if status:
            return {
                "price_data": status["price_data"],
                "predictions": status["predictions"],
                "signals": status["signals"],
                "timestamp": datetime.utcnow().isoformat()
            }
        raise HTTPException(status_code=503, detail="Automation not running")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation/signals")
async def get_automation_signals(user=Depends(get_current_user)):
    """Get latest high-confidence trading signals"""
    try:
        from services.market_automation import get_automation_status as get_status
        status = get_status()
        if status and status["signals"]:
            return {
                "signals": status["signals"],
                "count": len(status["signals"]),
                "timestamp": datetime.utcnow().isoformat()
            }
        return {"signals": [], "count": 0, "message": "No signals available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════════
# DATABASE API - Live Data Storage
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/market-data/latest")
async def get_latest_market_data(coin: str = None, limit: int = 100, user=Depends(get_current_user)):
    """Get latest market data from database"""
    try:
        from db.database import SessionLocal
        from db.models import MarketData
        
        db = SessionLocal()
        try:
            query = db.query(MarketData)
            if coin:
                query = query.filter(MarketData.coin == coin.upper())
            data = query.order_by(MarketData.timestamp.desc()).limit(limit).all()
            
            return {
                "data": [
                    {
                        "coin": d.coin,
                        "timestamp": d.timestamp.isoformat(),
                        "price": d.price,
                        "volume": d.volume,
                        "change_24h": d.change_24h
                    }
                    for d in data
                ],
                "count": len(data)
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/history")
async def get_predictions_history(coin: str = None, limit: int = 50, user=Depends(get_current_user)):
    """Get prediction history from database"""
    try:
        from db.database import SessionLocal
        from db.models import Prediction
        
        db = SessionLocal()
        try:
            query = db.query(Prediction)
            if coin:
                query = query.filter(Prediction.coin == coin.upper())
            data = query.order_by(Prediction.timestamp.desc()).limit(limit).all()
            
            return {
                "predictions": [
                    {
                        "coin": p.coin,
                        "timestamp": p.timestamp.isoformat(),
                        "current_price": p.current_price,
                        "predicted_direction": p.predicted_direction,
                        "confidence": p.confidence,
                        "target_price": p.target_price,
                        "timeframe": p.timeframe
                    }
                    for p in data
                ],
                "count": len(data)
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
