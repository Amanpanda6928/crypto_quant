import requests
import time

BASE = "https://api.binance.com/api/v3"

def get_klines(symbol, interval="1m", limit=60):
    return requests.get(f"{BASE}/klines", params={
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }).json()


def get_all_prices(coins=None):
    """
    Fetch current prices for all coins from Binance
    Returns: dict with coin symbol as key and price data as value
    """
    try:
        # If no coins specified, use default 17 coins
        if coins is None:
            coins = [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
                "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT",
                "MATICUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
                "XLMUSDT", "ICPUSDT"
            ]
        
        # Fetch 24hr ticker data for all symbols
        response = requests.get(f"{BASE}/ticker/24hr", timeout=10)
        
        if response.status_code != 200:
            print(f"[WARN] Failed to fetch prices: {response.status_code}")
            return {}
        
        all_data = response.json()
        
        # Filter for our coins only
        result = {}
        for item in all_data:
            symbol = item.get('symbol', '')
            if symbol in coins:
                result[symbol] = {
                    'price': float(item.get('lastPrice', 0)),
                    'volume': float(item.get('volume', 0)),
                    'change_24h': float(item.get('priceChangePercent', 0)),
                    'high_24h': float(item.get('highPrice', 0)),
                    'low_24h': float(item.get('lowPrice', 0)),
                    'timestamp': int(item.get('closeTime', 0))
                }
        
        # Also fetch current prices as backup
        price_response = requests.get(f"{BASE}/ticker/price", timeout=10)
        if price_response.status_code == 200:
            price_data = price_response.json()
            for item in price_data:
                symbol = item.get('symbol', '')
                if symbol in coins and symbol not in result:
                    result[symbol] = {
                        'price': float(item.get('price', 0)),
                        'volume': 0,
                        'change_24h': 0,
                        'timestamp': int(time.time() * 1000)
                    }
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error fetching all prices: {e}")
        return {}


# For direct import compatibility
if __name__ == "__main__":
    # Test the function
    prices = get_all_prices()
    print(f"OK: Fetched prices for {len(prices)} coins")
    for coin, data in list(prices.items())[:5]:
        print(f"  {coin}: ${data['price']:,.2f}")
