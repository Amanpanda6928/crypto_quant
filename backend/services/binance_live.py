# Enhanced Binance Live Trading Service with OCO Support
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
import time

client = Client(
    os.getenv("BINANCE_API_KEY"),
    os.getenv("BINANCE_SECRET")
)

def get_price(symbol):
    """Get current price for a symbol"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return None

def market_buy(symbol, qty):
    """Execute market buy order"""
    try:
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

def get_order_status(order_id):
    """Get order status"""
    try:
        order = client.get_order(orderId=order_id)
        return order
    except Exception as e:
        print(f"Error getting order status: {e}")
        return None

def cancel_order(order_id, symbol=None):
    """Cancel an order"""
    try:
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
        account = client.get_account()
        return account
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None

def get_symbol_info(symbol):
    """Get symbol trading information"""
    try:
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
        orders = client.get_all_orders(limit=limit)
        return orders
    except Exception as e:
        print(f"Error getting order history: {e}")
        return []

def get_server_time():
    """Get Binance server time"""
    try:
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
