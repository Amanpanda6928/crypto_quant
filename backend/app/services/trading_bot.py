# =========================
# services/trading_bot.py
# =========================
import time
import asyncio
from typing import Dict, List
from app.services.ai_model import ai_model
from app.services.trading_engine import trading_engine
from app.services.binance_client import binance_client
from app.core.config import BOT_INTERVAL, MAX_DAILY_TRADES, LIVE_TRADING

class TradingBot:
    def __init__(self):
        self.is_running = False
        self.daily_trades = 0
        self.last_reset = time.strftime("%Y-%m-%d")
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        self.performance = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0
        }
    
    def reset_daily_counter(self):
        """Reset daily trade counter"""
        today = time.strftime("%Y-%m-%d")
        if today != self.last_reset:
            self.daily_trades = 0
            self.last_reset = today
    
    async def run_bot(self):
        """Main bot loop"""
        self.is_running = True
        print("🤖 Trading bot started")
        
        while self.is_running:
            try:
                self.reset_daily_counter()
                
                # Check daily trade limit
                if self.daily_trades >= MAX_DAILY_TRADES:
                    print(f"Daily trade limit reached ({MAX_DAILY_TRADES})")
                    await asyncio.sleep(60)  # Wait 1 minute before checking again
                    continue
                
                # Process each symbol
                for symbol in self.symbols:
                    if not self.is_running:
                        break
                    
                    await self.process_symbol(symbol)
                
                # Wait for next iteration
                await asyncio.sleep(BOT_INTERVAL)
                
            except Exception as e:
                print(f"Bot error: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def process_symbol(self, symbol: str):
        """Process a single symbol for trading signals"""
        try:
            # Get current price
            current_price = binance_client.get_price(symbol)
            if not current_price:
                return
            
            # Generate AI signal
            signal = ai_model.predict(symbol, [current_price])
            
            print(f"📊 {symbol}: {signal['signal']} (confidence: {signal['confidence']:.2f})")
            
            # Execute trade based on signal
            if signal['confidence'] > 0.7 and signal['signal'] in ['BUY', 'SELL']:
                await self.execute_signal(symbol, signal, current_price)
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
    
    async def execute_signal(self, symbol: str, signal: Dict, price: float):
        """Execute a trading signal"""
        try:
            # Calculate position size (0.01 BTC for demo)
            quantity = 0.01
            
            # Execute trade
            if LIVE_TRADING:
                result = binance_client.market_order(symbol, signal['signal'], quantity)
                if result:
                    print(f"✅ Live trade executed: {symbol} {signal['signal']} {quantity}")
                    self.daily_trades += 1
                    self.performance["total_trades"] += 1
            else:
                # Paper trading
                result = trading_engine.execute_trade(symbol, price, quantity, signal['signal'])
                if result.get("success"):
                    print(f"📝 Paper trade executed: {symbol} {signal['signal']} {quantity}")
                    self.daily_trades += 1
                    self.performance["total_trades"] += 1
            
        except Exception as e:
            print(f"Error executing signal: {e}")
    
    def stop_bot(self):
        """Stop the bot"""
        self.is_running = False
        print("🛑 Trading bot stopped")
    
    def get_status(self) -> Dict:
        """Get bot status and performance"""
        return {
            "is_running": self.is_running,
            "daily_trades": self.daily_trades,
            "max_daily_trades": MAX_DAILY_TRADES,
            "performance": self.performance,
            "symbols": self.symbols,
            "live_trading": LIVE_TRADING
        }
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        total = self.performance["total_trades"]
        if total == 0:
            return {"win_rate": 0, "total_pnl": 0.0}
        
        win_rate = (self.performance["winning_trades"] / total) * 100
        return {
            "win_rate": round(win_rate, 2),
            "total_trades": total,
            "total_pnl": self.performance["total_pnl"],
            "daily_trades": self.daily_trades
        }

# Global bot instance
trading_bot = TradingBot()

async def run_bot():
    await trading_bot.run_bot()
