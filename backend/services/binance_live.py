# Enhanced Binance Live Trading Service with OCO Support
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
import time

# Lazy initialization - client created on first use
_client = None

def get_client():
    """Get or create Binance client (lazy initialization)"""
    global _client
    if _client is None:
        try:
            _client = Client(
                os.getenv("BINANCE_API_KEY"),
                os.getenv("BINANCE_SECRET"),
                {"verify": True, "timeout": 20},
                testnet=os.getenv("BINANCE_TESTNET", "false").lower() == "true",
            )
        except Exception as e:
            print(f"⚠️  Binance client init failed: {e}")
            print("   Running in offline/demo mode - no live trading available")
            _client = None
    return _client

def get_price(symbol):
    """Get current price for a symbol"""
    try:
        client = get_client()
        if client is None:
            print(f"Offline mode: Cannot get price for {symbol}")
            return None
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return None

def market_buy(symbol, qty):
    """Execute market buy order"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot execute market buy")
            return None
        order = client.create_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quantity=qty
        )
        print(f"Market BUY order placed: {order}")
        return order
    except BinanceAPIException as e:
        print(f"Market BUY failed: {e}")
        return None

def market_sell(symbol, qty):
    """Execute market sell order"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot execute market sell")
            return None
        order = client.create_order(
            symbol=symbol,
            side="SELL",
            type="MARKET",
            quantity=qty
        )
        print(f"Market SELL order placed: {order}")
        return order
    except BinanceAPIException as e:
        print(f"Market SELL failed: {e}")
        return None

def place_oco_sell(symbol, qty, take_profit, stop_loss):
    """
    Place OCO (One-Cancels-Other) order for LONG position
    SELL order with TP (limit) and SL (stop-market)
    """
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot place OCO sell")
            return None
        order = client.create_oco_order(
            symbol=symbol,
            side="SELL",
            quantity=qty,
            price=str(round(take_profit, 6)),  # Take profit (limit order)
            stopPrice=str(round(stop_loss, 6)),  # Stop loss trigger
            stopLimitPrice=str(round(stop_loss * 0.999, 6)),  # Stop limit price
            stopLimitTimeInForce="GTC"
        )
        print(f"OCO SELL order placed: {order}")
        return order
    except BinanceAPIException as e:
        print(f"OCO SELL failed: {e}")
        return None

def place_oco_buy(symbol, qty, take_profit, stop_loss):
    """
    Place OCO order for SHORT position
    BUY order with TP (limit) and SL (stop-market)
    """
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot place OCO buy")
            return None
        order = client.create_oco_order(
            symbol=symbol,
            side="BUY",
            quantity=qty,
            price=str(round(take_profit, 6)),  # Take profit (limit order)
            stopPrice=str(round(stop_loss, 6)),  # Stop loss trigger
            stopLimitPrice=str(round(stop_loss * 1.001, 6)),  # Stop limit price
            stopLimitTimeInForce="GTC"
        )
        print(f"OCO BUY order placed: {order}")
        return order
    except BinanceAPIException as e:
        print(f"OCO BUY failed: {e}")
        return None

def get_order_status(order_id, symbol=None):
    """Get order status"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot get order status")
            return None
        if symbol:
            order = client.get_order(symbol=symbol, orderId=order_id)
        else:
            order = client.get_order(orderId=order_id)
        return order
    except Exception as e:
        print(f"Error getting order status: {e}")
        return None

def cancel_order(order_id, symbol=None):
    """Cancel an order"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot cancel order")
            return None
        if symbol:
            result = client.cancel_order(symbol=symbol, orderId=order_id)
        else:
            result = client.cancel_order(orderId=order_id)
        print(f"Order cancelled: {result}")
        return result
    except Exception as e:
        print(f"Error cancelling order: {e}")
        return None

def get_account_info():
    """Get account information"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot get account info")
            return None
        account = client.get_account()
        return account
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None

def get_symbol_info(symbol):
    """Get symbol trading information"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot get symbol info")
            return None
        info = client.get_symbol_info(symbol=symbol)
        return info
    except Exception as e:
        print(f"Error getting symbol info: {e}")
        return None

def get_all_prices():
    """Get prices for all 30 coins"""
    symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT",
        "MATICUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
        "XLMUSDT", "ICPUSDT", "APTUSDT", "ARBUSDT", "OPUSDT",
        "PEPEUSDT", "SHIBUSDT", "RNDRUSDT", "INJUSDT", "SUIUSDT",
        "SEIUSDT", "KASUSDT", "FTMUSDT", "GRTUSDT", "RUNEUSDT"
    ]
    
    prices = {}
    for symbol in symbols:
        try:
            price = get_price(symbol)
            coin = symbol.replace("USDT", "")
            prices[coin] = price
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            coin = symbol.replace("USDT", "")
            prices[coin] = None
    
    return prices

def get_balance(asset="USDT"):
    """Get balance for specific asset"""
    try:
        account = get_account_info()
        if account:
            for balance_info in account["balances"]:
                if balance_info["asset"] == asset:
                    return float(balance_info["free"])
        return 0.0
    except Exception as e:
        print(f"Error getting balance: {e}")
        return 0.0

def get_open_orders(symbol=None):
    """Get all open orders"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot get open orders")
            return []
        if symbol:
            orders = client.get_open_orders(symbol=symbol)
        else:
            orders = client.get_open_orders()
        return orders
    except Exception as e:
        print(f"Error getting open orders: {e}")
        return []

def get_order_history(limit=100):
    """Get order history"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot get order history")
            return []
        orders = client.get_all_orders(limit=limit)
        return orders
    except Exception as e:
        print(f"Error getting order history: {e}")
        return []

def get_server_time():
    """Get Binance server time"""
    try:
        client = get_client()
        if client is None:
            return None
        server_time = client.get_server_time()
        return server_time
    except Exception as e:
        print(f"Error getting server time: {e}")
        return None

def test_connection():
    """Test Binance connection"""
    try:
        server_time = get_server_time()
        if server_time:
            print("✅ Binance connection successful")
            return True
        else:
            print("❌ Binance connection failed")
            return False
    except Exception as e:
        print(f"❌ Binance connection error: {e}")
        return False

# Advanced order management
def place_trailing_stop(symbol, side, quantity, activation_price, callback_rate):
    """Place trailing stop order"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot place trailing stop")
            return None
        order = client.create_order(
            symbol=symbol,
            side=side,
            type="TRAILING_STOP_MARKET",
            quantity=quantity,
            activationPrice=str(activation_price),
            callbackRate=callback_rate
        )
        print(f"Trailing stop order placed: {order}")
        return order
    except Exception as e:
        print(f"Trailing stop failed: {e}")
        return None

def place_take_profit_order(symbol, side, quantity, stop_price, profit_price):
    """Place take profit order"""
    try:
        client = get_client()
        if client is None:
            print("Offline mode: Cannot place take profit order")
            return None
        order = client.create_order(
            symbol=symbol,
            side=side,
            type="LIMIT_MAKER",
            quantity=quantity,
            price=str(profit_price),
            stopPrice=str(stop_price),
            timeInForce="GTC"
        )
        print(f"Take profit order placed: {order}")
        return order
    except Exception as e:
        print(f"Take profit order failed: {e}")
        return None
