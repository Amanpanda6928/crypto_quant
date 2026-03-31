# =========================
# services/binance_client.py
# =========================
import time
import requests
from typing import Dict, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
from app.core.config import BINANCE_API_KEY, BINANCE_SECRET_KEY, LIVE_TRADING

class BinanceClient:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self._live_prices = {}  # Cache for live prices
        self._last_price_update = 0
        
        if LIVE_TRADING and BINANCE_API_KEY and BINANCE_SECRET_KEY:
            try:
                self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
                self.is_connected = True
            except Exception as e:
                print(f"Failed to connect to Binance: {e}")
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        if not self.is_connected:
            return self._mock_account()
        
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            print(f"Error getting account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol trading information"""
        if not self.is_connected:
            return self._mock_symbol_info(symbol)
        
        try:
            return self.client.get_symbol_info(symbol)
        except BinanceAPIException as e:
            print(f"Error getting symbol info: {e}")
            return None
    
    def market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """Place a market order"""
        if not self.is_connected:
            return self._mock_order(symbol, side, quantity)
        
        try:
            return self.client.create_order(
                symbol=symbol, 
                side=side, 
                type="MARKET", 
                quantity=quantity
            )
        except BinanceAPIException as e:
            print(f"Error creating market order: {e}")
            return None
    
    def limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Optional[Dict]:
        """Place a limit order"""
        if not self.is_connected:
            return self._mock_order(symbol, side, quantity, price)
        
        try:
            return self.client.create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=str(price)
            )
        except BinanceAPIException as e:
            print(f"Error creating limit order: {e}")
            return None
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if not self.is_connected:
            return self._mock_price(symbol)
        
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Error getting price: {e}")
            return None
    
    def cancel_order(self, symbol: str, orderId: int) -> Optional[Dict]:
        """Cancel an order"""
        if not self.is_connected:
            return {"orderId": orderId, "status": "CANCELED"}
        
        try:
            return self.client.cancel_order(symbol=symbol, orderId=orderId)
        except BinanceAPIException as e:
            print(f"Error canceling order: {e}")
            return None
    
    # Mock methods for paper trading
    def _mock_account(self) -> Dict:
        return {
            "balances": [
                {"asset": "USDT", "free": "10000.0", "locked": "0.0"},
                {"asset": "BTC", "free": "0.0", "locked": "0.0"}
            ]
        }
    
    def _mock_symbol_info(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "status": "TRADING",
            "filters": [
                {"filterType": "PRICE_FILTER", "minPrice": "0.01"},
                {"filterType": "LOT_SIZE", "minQty": "0.001"}
            ]
        }
    
    def _mock_order(self, symbol: str, side: str, quantity: float, price: float = None) -> Dict:
        import uuid
        return {
            "symbol": symbol,
            "orderId": int(uuid.uuid4().hex[:8], 16),
            "orderListId": -1,
            "clientOrderId": str(uuid.uuid4()),
            "transactTime": 1234567890123,
            "price": str(price) if price else "0",
            "origQty": str(quantity),
            "executedQty": str(quantity),
            "cummulativeQuoteQty": str(quantity * (price if price else 50000)),
            "status": "FILLED",
            "type": "MARKET" if price is None else "LIMIT",
            "side": side,
            "fills": []
        }
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 60) -> Optional[list]:
        """Get candlestick/kline data for a symbol"""
        if not self.is_connected:
            return self._mock_klines(symbol, interval, limit)
        
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            return [
                {
                    "time": k[0],           # Open time
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": k[6]
                }
                for k in klines
            ]
        except BinanceAPIException as e:
            print(f"Error getting klines: {e}")
            return self._mock_klines(symbol, interval, limit)
    
    def _mock_klines(self, symbol: str, interval: str, limit: int) -> list:
        """Generate mock klines for testing"""
        import random
        base_price = self._mock_price(symbol)
        klines = []
        current_time = int(time.time() * 1000)
        
        # Interval in milliseconds
        interval_ms = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000
        }.get(interval, 60 * 60 * 1000)
        
        price = base_price
        for i in range(limit):
            open_time = current_time - (limit - i) * interval_ms
            
            # Random price movement
            volatility = price * 0.002  # 0.2% volatility
            open_price = price
            close_price = open_price + random.uniform(-volatility, volatility)
            high_price = max(open_price, close_price) + random.uniform(0, volatility * 0.5)
            low_price = min(open_price, close_price) - random.uniform(0, volatility * 0.5)
            volume = random.uniform(100, 1000)
            
            klines.append({
                "time": open_time,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(volume, 4),
                "close_time": open_time + interval_ms - 1
            })
            price = close_price
        
        return klines
    
    def _mock_price(self, symbol: str) -> float:
        """Fetch live price from Binance public API (free, no API key needed)"""
        # Try to fetch live price first
        try:
            # Check cache (refresh every 5 seconds)
            current_time = time.time()
            if symbol in self._live_prices and (current_time - self._last_price_update) < 5:
                return self._live_prices[symbol]
            
            # Fetch from Binance public API
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                price = float(response.json()['price'])
                self._live_prices[symbol] = price
                self._last_price_update = current_time
                return price
        except Exception as e:
            print(f"Failed to fetch live price for {symbol}: {e}")
        
        # Fallback to cached or static price
        if symbol in self._live_prices:
            return self._live_prices[symbol]
        
        # Final fallback - static mock prices (current market values)
        fallback_prices = {
            "BTCUSDT": 67500.0,
            "ETHUSDT": 3450.0,
            "BNBUSDT": 605.0,
            "SOLUSDT": 142.0,
            "XRPUSDT": 0.58,
            "ADAUSDT": 0.45,
            "AVAXUSDT": 28.5,
            "DOGEUSDT": 0.12,
            "DOTUSDT": 7.2,
            "LINKUSDT": 13.8,
            "MATICUSDT": 0.42,
            "LTCUSDT": 82.0,
            "BCHUSDT": 385.0,
            "UNIUSDT": 7.5,
            "ATOMUSDT": 6.8,
            "XLMUSDT": 0.09,
            "ICPUSDT": 10.5,
            "APTUSDT": 6.2,
            "ARBUSDT": 0.58,
            "OPUSDT": 1.45,
        }
        return fallback_prices.get(symbol, 100.0)
    
    def refresh_all_prices(self) -> Dict[str, float]:
        """Refresh prices for all 20 coins"""
        symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
            "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT",
            "MATICUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
            "XLMUSDT", "ICPUSDT", "APTUSDT", "ARBUSDT", "OPUSDT"
        ]
        
        prices = {}
        for symbol in symbols:
            try:
                price = self._mock_price(symbol)  # This now fetches live price
                prices[symbol] = price
            except Exception as e:
                print(f"Failed to get price for {symbol}: {e}")
                prices[symbol] = 0.0
        
        return prices

# Global client instance
binance_client = BinanceClient()

def market(symbol: str, side: str, qty: float):
    return binance_client.market_order(symbol, side, qty)
