from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio, json, websockets
import numpy as np

from config.settings import COINS, TIMEFRAMES
from services.binance_service import get_klines
from ml.model_loader import load_all, predict
from trading.paper_portfolio import get_portfolio, update_equity
from analytics.monte_carlo import monte_carlo
from analytics.optimizer import optimize
from db.database import SessionLocal
from db.models import Trade

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

LIVE = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str = None
    user_id: int = None

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Simple authentication - accept any login for demo purposes
    return LoginResponse(
        success=True,
        token="demo_token_12345",
        user_id=1
    )

def save_trade(user_id, symbol, action, price, pnl=0):
    db = SessionLocal()

    t = Trade(
        user_id=user_id,
        symbol=symbol,
        action=action,
        price=price,
        pnl=pnl
    )

    db.add(t)
    db.commit()

@app.on_event("startup")
async def startup():
    load_all()
    asyncio.create_task(stream())

async def stream():
    streams = "/".join([f"{c.lower()}@trade" for c in COINS])
    url = f"wss://stream.binance.com:9443/ws/{streams}"

    async with websockets.connect(url) as ws:
        while True:
            msg = json.loads(await ws.recv())
            symbol = msg["s"]
            price = float(msg["p"])

            if symbol not in LIVE:
                LIVE[symbol] = []

            LIVE[symbol].append(price)
            LIVE[symbol] = LIVE[symbol][-60:]

def compute(symbol):
    weights = {"1m":0.1,"5m":0.2,"15m":0.3,"1h":0.4}
    preds = {}
    current = None

    for tf in TIMEFRAMES:
        klines = get_klines(symbol, tf, 60)
        prices = [float(k[4]) for k in klines]

        if len(prices) < 60:
            continue

        p = predict(symbol, prices, tf)
        preds[tf] = p

        if tf == "1m":
            current = prices[-1]

    if not preds:
        return None

    final = sum(preds[tf]*weights[tf] for tf in preds) / sum(weights[tf] for tf in preds)
    conf = 100 - np.std(list(preds.values()))

    signal = "BUY" if final > current*1.005 else "SELL" if final < current*0.995 else "HOLD"

    # Save trade to database
    save_trade(1, symbol, signal, current)

    return {
        "price": current,
        "prediction": final,
        "signal": signal,
        "confidence": round(conf,2)
    }

@app.websocket("/ws/live")
async def ws(ws: WebSocket):
    await ws.accept()

    while True:
        out = {}

        prices = {}
        for coin in LIVE:
            if LIVE[coin]:
                prices[coin] = LIVE[coin][-1]

        update_equity(prices)

        for coin in LIVE:
            d = compute(coin)
            if d:
                out[coin] = d

        if out:
            await ws.send_json(out)

        await asyncio.sleep(0.5)

@app.get("/analytics")
def analytics():
    pf = get_portfolio()
    pnl = [t.get("pnl",0) for t in pf["history"]]

    if not pnl:
        return {}

    arr = np.array(pnl)

    return {
        "sharpe": float(arr.mean()/(arr.std()+1e-9)),
        "profit": float(arr.sum()),
        "monte": monte_carlo(pnl)[:10],
        "opt": optimize(pnl),
        "equity": pf["equity"][-100:]
    }

@app.get("/history/{user_id}")
def history(user_id: int):
    db = SessionLocal()

    trades = db.query(Trade).filter(Trade.user_id == user_id).all()

    return [
        {
            "symbol": t.symbol,
            "action": t.action,
            "price": t.price,
            "pnl": t.pnl
        }
        for t in trades
    ]
