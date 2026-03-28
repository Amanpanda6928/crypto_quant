import requests

BASE = "https://api.binance.com/api/v3"

def get_klines(symbol, interval="1m", limit=60):
    return requests.get(f"{BASE}/klines", params={
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }).json()
