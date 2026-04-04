# Enhanced Live Trading Bot with OCO Orders and Risk Management
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.binance_live import (
    get_price, market_buy, market_sell, place_oco_sell, get_balance, 
    get_open_orders, cancel_order, get_order_status
)
from services.risk_control import calc_qty, sl_tp_prices, calculate_risk_metrics
from multi_coin_lstm import multi_lstm

# Safety guards
MAX_TRADES_PER_DAY = 50
MAX_POSITION_SIZE = 1000  # USDT
MIN_CONFIDENCE = 0.7
RISK_PCT = 1.0  # 1% risk per trade
SL_PCT = 0.02   # 2% stop loss
TP_PCT = 0.04   # 4% take profit

# Bot state
running = False
positions = {}  # Track open positions: {coin: {qty, entry, sl, tp, oco_order_id}}
trade_count = 0
last_reset = time.strftime("%Y-%m-%d")

def reset_daily_counter():
    """Reset daily trade counter"""
    global trade_count, last_reset
    today = time.strftime("%Y-%m-%d")
    if today != last_reset:
        trade_count = 0
        last_reset = today

def can_trade():
    """Check if bot can trade"""
    reset_daily_counter()
    
    # Check daily trade limit
    if trade_count >= MAX_TRADES_PER_DAY:
        print(f"Daily trade limit reached: {trade_count}/{MAX_TRADES_PER_DAY}")
        return False
    
    return True

def execute_long_position(coin, signal, current_price):
    """Execute LONG position with OCO protection"""
    global positions, trade_count
    
    # Calculate position size
    balance = get_balance("USDT")
    sl, tp = sl_tp_prices(current_price, "BUY", SL_PCT, TP_PCT)
    qty = calc_qty(balance, RISK_PCT, current_price, sl)
    
    # Validate trade
    if qty <= 0:
        print(f"Invalid quantity calculated: {qty}")
        return False
    
    live_trading = os.getenv("LIVE_TRADING", "false").lower() == "true"
    
    try:
        if live_trading:
            # 1) Enter market position
            entry_order = market_buy(f"{coin}USDT", qty)
            if not entry_order:
                print(f"Failed to enter LONG position for {coin}")
                return False
            
            # 2) Immediately place OCO sell order for TP/SL
            oco_order = place_oco_sell(f"{coin}USDT", qty, tp, sl)
            if not oco_order:
                print(f"Failed to place OCO protection for {coin}")
                # Cancel entry order
                cancel_order(entry_order["orderId"], f"{coin}USDT")
                return False
            
            # Store position
            positions[coin] = {
                "side": "LONG",
                "entry_price": current_price,
                "quantity": qty,
                "usdt_size": qty * current_price,
                "stop_loss": sl,
                "take_profit": tp,
                "entry_order_id": entry_order["orderId"],
                "oco_order_id": oco_order["orderId"],
                "entry_time": time.time()
            }
            
            print(f"🟢 LIVE LONG: {coin} @ ${current_price}")
            print(f"   Size: {qty} | SL: ${sl} | TP: ${tp}")
            print(f"   Entry Order: {entry_order['orderId']}")
            print(f"   OCO Order: {oco_order['orderId']}")
            
        else:
            # Paper trading
            positions[coin] = {
                "side": "LONG",
                "entry_price": current_price,
                "quantity": qty,
                "usdt_size": qty * current_price,
                "stop_loss": sl,
                "take_profit": tp,
                "entry_time": time.time()
            }
            
            print(f"📝 PAPER LONG: {coin} @ ${current_price}")
            print(f"   Size: {qty} | SL: ${sl} | TP: ${tp}")
        
        trade_count += 1
        return True
        
    except Exception as e:
        print(f"❌ LONG position execution failed: {e}")
        return False

def check_exit_conditions(coin, current_price):
    """Check if position should be closed"""
    global positions
    
    if coin not in positions:
        return None
    
    position = positions[coin]
    
    # Check stop loss
    if current_price <= position["stop_loss"]:
        return {
            "reason": "STOP_LOSS",
            "exit_price": current_price,
            "pnl": (current_price - position["entry_price"]) * position["quantity"]
        }
    
    # Check take profit
    if current_price >= position["take_profit"]:
        return {
            "reason": "TAKE_PROFIT",
            "exit_price": current_price,
            "pnl": (current_price - position["entry_price"]) * position["quantity"]
        }
    
    return None

def close_position(coin, exit_reason, exit_price, pnl):
    """Close position and calculate PnL"""
    global positions
    
    if coin not in positions:
        return False
    
    position = positions[coin]
    live_trading = os.getenv("LIVE_TRADING", "false").lower() == "true"
    
    try:
        pnl_pct = (exit_price - position["entry_price"]) / position["entry_price"] * 100
        
        if live_trading:
            # Cancel OCO order if still active
            if "oco_order_id" in position:
                cancel_order(position["oco_order_id"], f"{coin}USDT")
            
            # Market sell to close position
            close_order = market_sell(f"{coin}USDT", position["quantity"])
            print(f"🔴 LIVE CLOSE: {coin} @ ${exit_price}")
            print(f"   Reason: {exit_reason}")
            print(f"   PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
            print(f"   Close Order: {close_order}")
        
        else:
            print(f"📝 PAPER CLOSE: {coin} @ ${exit_price}")
            print(f"   Reason: {exit_reason}")
            print(f"   PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
        
        del positions[coin]
        return True
        
    except Exception as e:
        print(f"❌ Position close failed: {e}")
        return False

def run_live_bot():
    """Main bot loop with OCO protection"""
    global running, positions
    
    running = True
    
    print("🚀 Starting Enhanced Live Trading Bot")
    print(f"📊 Live Trading: {os.getenv('LIVE_TRADING', 'false')}")
    print(f"🛡️ Risk per Trade: {RISK_PCT}%")
    print(f"🎯 Stop Loss: {SL_PCT*100}%")
    print(f"📈 Take Profit: {TP_PCT*100}%")
    print("=" * 60)
    
    while running:
        try:
            # Get current prices for all coins
            prices = {}
            for coin in multi_lstm.coins[:10]:  # Monitor top 10 coins
                price = get_price(f"{coin}USDT")
                if price:
                    prices[coin] = price
                    multi_lstm.update_coin_price(coin, price)
            
            # Get top signals
            top_signals = multi_lstm.get_top_signals(5)
            
            print(f"\n🎯 Top {len(top_signals)} Trading Opportunities:")
            print("-" * 60)
            
            for i, signal in enumerate(top_signals, 1):
                coin = signal["coin"]
                current_price = prices.get(coin)
                
                if current_price and signal["confidence"] >= MIN_CONFIDENCE:
                    status_emoji = "🟢" if "BUY" in signal["signal"] else "🔴"
                    print(f"{i}. {status_emoji} {coin:6} | {signal['signal']:12} | {signal['confidence']:.3f} | ${current_price:>10.2f}")
                    
                    # Check if we should enter new position
                    if coin not in positions and "BUY" in signal["signal"]:
                        execute_long_position(coin, signal, current_price)
            
            # Check exit conditions for existing positions
            print(f"\n💼 Checking Exit Conditions:")
            print("-" * 60)
            
            for coin in list(positions.keys()):
                current_price = prices.get(coin)
                if current_price:
                    exit_signal = check_exit_conditions(coin, current_price)
                    if exit_signal:
                        close_position(coin, exit_signal["reason"], exit_signal["exit_price"], exit_signal["pnl"])
            
            # Display current positions
            if positions:
                print(f"\n💼 Open Positions ({len(positions)}):")
                print("-" * 60)
                
                for coin, pos in positions.items():
                    current_price = prices.get(coin, pos["entry_price"])
                    pnl = (current_price - pos["entry_price"]) * pos["quantity"]
                    pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"] * 100
                    pnl_emoji = "🟢" if pnl > 0 else "🔴"
                    
                    print(f"  {coin:6} | ${pos['entry_price']:>10.2f} | ${current_price:>10.2f} | {pnl_emoji} ${pnl:+8.2f} ({pnl_pct:+.2f}%)")
                    print(f"    SL: ${pos['stop_loss']:>10.2f} | TP: ${pos['take_profit']:>10.2f}")
            
            # Display bot stats
            risk_metrics = calculate_risk_metrics(positions, prices)
            print(f"\n📊 Bot Stats:")
            print(f"  Trades Today: {trade_count}/{MAX_TRADES_PER_DAY}")
            print(f"  Open Positions: {len(positions)}")
            print(f"  Portfolio Value: ${risk_metrics.get('total_portfolio_value', 0):.2f}")
            print(f"  Total Risk: ${risk_metrics.get('total_risk', 0):.2f}")
            print(f"  Risk Level: {risk_metrics.get('risk_percentage', 0):.1f}%")
            
            # Wait for next iteration
            print(f"\n⏳ Waiting 10 seconds...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            running = False
        except Exception as e:
            print(f"\n❌ Bot error: {e}")
            time.sleep(10)  # Wait before retrying

def stop_bot():
    """Stop trading bot"""
    global running
    running = False
    print("🛑 Stopping enhanced trading bot...")

def get_bot_status():
    """Get current bot status"""
    global positions, trade_count
    return {
        "running": running,
        "positions": positions,
        "trades_today": trade_count,
        "max_trades_per_day": MAX_TRADES_PER_DAY,
        "live_trading": os.getenv("LIVE_TRADING", "false").lower() == "true",
        "coins_tracked": len(multi_lstm.coins),
        "models_loaded": len(multi_lstm.models)
    }

def emergency_close_all():
    """Emergency close all positions"""
    global positions
    print("🚨 EMERGENCY CLOSE ALL POSITIONS")
    
    live_trading = os.getenv("LIVE_TRADING", "false").lower() == "true"
    
    for coin, position in list(positions.items()):
        try:
            # Cancel OCO order first
            if "oco_order_id" in position:
                cancel_order(position["oco_order_id"], f"{coin}USDT")
            
            # Market close position
            current_price = get_price(f"{coin}USDT")
            if current_price:
                if live_trading:
                    close_order = market_sell(f"{coin}USDT", position["quantity"])
                    print(f"Emergency sell order: {close_order}")
                else:
                    print(f"Emergency paper close: {coin}")
            
            pnl = (current_price - position["entry_price"]) * position["quantity"]
            print(f"Closed {coin}: PnL ${pnl:.2f}")
            
        except Exception as e:
            print(f"Failed to close {coin}: {e}")
    
    positions.clear()
    print("✅ All positions closed")

if __name__ == "__main__":
    # Test the bot
    print("🧪 Testing Enhanced Live Trading Bot")
    status = get_bot_status()
    print(f"Status: {status}")
    
    # Uncomment to run live bot
    # run_live_bot()
