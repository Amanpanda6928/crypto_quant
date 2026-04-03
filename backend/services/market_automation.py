"""
24/7 Multi-Timeframe Market Data Automation Service
Fetches candle data for 15m, 30m, 1h, 4h, 1d timeframes
Generates predictions every 15 minutes
Auto-deletes data older than 1 day
"""
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import and init database
from db.database import init_db

class MultiTimeframeAutomation:
    """
    Automated service for multi-timeframe predictions:
    - Fetches candle data for 15m, 30m, 1h, 4h, 1d
    - Generates predictions every 15 minutes
    - Auto-deletes data older than 1 day
    """
    
    TIMEFRAMES = ["15m", "30m", "1h", "4h", "1d"]
    
    def __init__(self, coins: List[str]):
        self.coins = coins
        self.running = False
        self.last_prediction_time = None
        self.last_cleanup_time = None
        
        # Store candle data for each timeframe
        self.candle_data: Dict[str, Dict[str, List]] = {}
        # Store predictions for each timeframe
        self.predictions: Dict[str, Dict[str, Dict]] = {}
        # Store signals
        self.signals: List[Dict] = []
        
        # Initialize storage
        for tf in self.TIMEFRAMES:
            self.candle_data[tf] = {}
            self.predictions[tf] = {}
            for coin in coins:
                self.candle_data[tf][coin] = []
    
    def start(self):
        """Start the 24/7 automation"""
        self.running = True
        logger.info("🚀 Starting 24/7 Multi-Timeframe Automation...")
        logger.info("⏰ Predictions every 15 minutes for: 15m, 30m, 1h, 4h, 1d")
        
        self.main_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.main_thread.start()
        logger.info("✅ Multi-timeframe automation started")
    
    def stop(self):
        """Stop the automation"""
        self.running = False
        logger.info("⏹️ Stopping automation...")
    
    def _automation_loop(self):
        """Main automation loop - runs continuously"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Generate predictions every 15 minutes (900 seconds)
                if self.last_prediction_time is None or (current_time - self.last_prediction_time).seconds >= 900:
                    logger.info("🔄 Starting 15-minute prediction cycle...")
                    self._fetch_all_timeframes()
                    self._generate_all_predictions()
                    self._generate_signals()
                    self._cleanup_old_data()
                    self.last_prediction_time = current_time
                    logger.info("✅ 15-minute cycle complete")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in automation loop: {e}")
                time.sleep(30)
    
    def _fetch_all_timeframes(self):
        """Fetch candle data for all timeframes (15m, 30m, 1h, 4h, 1d)"""
        try:
            from services.binance_service import get_klines
            
            for tf in self.TIMEFRAMES:
                logger.info(f"📊 Fetching {tf} candles for {len(self.coins)} coins...")
                
                for coin in self.coins:
                    try:
                        symbol = coin if coin.endswith("USDT") else f"{coin}USDT"
                        klines = get_klines(symbol, interval=tf, limit=100)
                        
                        if klines and isinstance(klines, list):
                            candles = []
                            for k in klines:
                                if isinstance(k, list) and len(k) >= 6:
                                    candles.append({
                                        'timestamp': datetime.fromtimestamp(k[0] / 1000),
                                        'open': float(k[1]),
                                        'high': float(k[2]),
                                        'low': float(k[3]),
                                        'close': float(k[4]),
                                        'volume': float(k[5])
                                    })
                            
                            self.candle_data[tf][coin] = candles
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to fetch {tf} for {coin}: {e}")
                
                logger.info(f"✅ Fetched {tf} data")
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"❌ Error fetching timeframe data: {e}")
    
    def _generate_all_predictions(self):
        """Generate predictions for all 5 timeframes"""
        try:
            from multi_coin_lstm import multi_lstm
            
            for tf in self.TIMEFRAMES:
                logger.info(f"🤖 Generating {tf} predictions...")
                predictions = {}
                
                for coin in self.coins:
                    candles = self.candle_data.get(tf, {}).get(coin, [])
                    
                    if len(candles) >= 20:
                        try:
                            latest_price = candles[-1]['close']
                            closes = [c['close'] for c in candles[-50:]]
                            volumes = [c['volume'] for c in candles[-20:]]
                            
                            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else latest_price
                            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else latest_price
                            
                            price_change = ((latest_price - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0
                            avg_volume = sum(volumes) / len(volumes) if volumes else 0
                            latest_volume = volumes[-1] if volumes else 0
                            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
                            
                            # Timeframe-specific weights
                            if tf == "15m":
                                momentum_weight, volume_weight, threshold = 0.6, 0.4, 0.3
                                target_multiplier = 1.002
                            elif tf == "30m":
                                momentum_weight, volume_weight, threshold = 0.55, 0.45, 0.4
                                target_multiplier = 1.004
                            elif tf == "1h":
                                momentum_weight, volume_weight, threshold = 0.5, 0.5, 0.5
                                target_multiplier = 1.008
                            elif tf == "4h":
                                momentum_weight, volume_weight, threshold = 0.45, 0.55, 0.6
                                target_multiplier = 1.02
                            else:  # 1d
                                momentum_weight, volume_weight, threshold = 0.4, 0.6, 0.8
                                target_multiplier = 1.05
                            
                            score = (price_change * momentum_weight) + ((volume_ratio - 1) * 10 * volume_weight)
                            
                            if score > threshold:
                                direction = "BUY"
                                confidence = min(95, 60 + abs(score) * 5)
                            elif score < -threshold:
                                direction = "SELL"
                                confidence = min(95, 60 + abs(score) * 5)
                            else:
                                direction = "HOLD"
                                confidence = 50 + abs(score) * 2
                            
                            target_price = latest_price * target_multiplier if direction == "BUY" else latest_price * (2 - target_multiplier)
                            
                            predictions[coin] = {
                                'timestamp': datetime.now(),
                                'current_price': latest_price,
                                'predicted_direction': direction,
                                'confidence': confidence / 100,
                                'target_price': target_price,
                                'timeframe': tf,
                                'score': round(score, 2),
                                'sma_20': round(sma_20, 2),
                                'sma_50': round(sma_50, 2),
                                'volume_ratio': round(volume_ratio, 2),
                                'price_change_24h': round(price_change, 2)
                            }
                        except Exception as e:
                            logger.warning(f"⚠️ Prediction error for {coin} {tf}: {e}")
                
                self.predictions[tf] = predictions
                logger.info(f"✅ Generated {len(predictions)} {tf} predictions")
                self._store_timeframe_predictions(predictions, tf)
                
        except Exception as e:
            logger.error(f"❌ Error generating predictions: {e}")
    
    def _store_timeframe_predictions(self, predictions: Dict, timeframe: str):
        """Store timeframe-specific predictions in database"""
        try:
            from app.db.database import SessionLocal
            from app.db.models import Prediction
            
            db = SessionLocal()
            try:
                for coin, pred in predictions.items():
                    prediction = Prediction(
                        coin=coin,
                        timestamp=pred['timestamp'],
                        current_price=pred['current_price'],
                        predicted_direction=pred['predicted_direction'],
                        confidence=pred['confidence'],
                        target_price=pred['target_price'],
                        timeframe=timeframe
                    )
                    db.add(prediction)
                
                db.commit()
                logger.info(f"✅ Stored {len(predictions)} {timeframe} predictions")
                
            except Exception as e:
                logger.error(f"❌ DB error storing {timeframe} predictions: {e}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error in store_predictions: {e}")
    
    def _cleanup_old_data(self):
        """Delete data older than 1 day from database"""
        try:
            from app.db.database import SessionLocal
            from app.db.models import MarketData, Prediction
            from sqlalchemy import func
            
            db = SessionLocal()
            try:
                one_day_ago = datetime.now() - timedelta(days=1)
                
                # Delete old market data
                market_deleted = db.query(MarketData).filter(
                    MarketData.timestamp < one_day_ago
                ).delete(synchronize_session=False)
                
                # Delete old predictions
                pred_deleted = db.query(Prediction).filter(
                    Prediction.timestamp < one_day_ago
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.info(f"🗑️ Cleaned up: {market_deleted} market records, {pred_deleted} predictions")
                
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")
    
    def _generate_signals(self):
        """Generate trading signals from all timeframe predictions"""
        try:
            signals = []
            
            for coin in self.coins:
                coin_signals = []
                
                for tf in self.TIMEFRAMES:
                    pred = self.predictions.get(tf, {}).get(coin)
                    if pred and pred['confidence'] >= 0.7:
                        coin_signals.append({
                            'coin': coin,
                            'timeframe': tf,
                            'signal': pred['predicted_direction'],
                            'confidence': pred['confidence'],
                            'current_price': pred['current_price'],
                            'target_price': pred['target_price'],
                            'timestamp': pred['timestamp']
                        })
                
                # Multi-timeframe consensus
                if len(coin_signals) >= 2:
                    buy_count = sum(1 for s in coin_signals if s['signal'] == 'BUY')
                    sell_count = sum(1 for s in coin_signals if s['signal'] == 'SELL')
                    
                    if buy_count >= 2:
                        best = max(coin_signals, key=lambda x: x['confidence'])
                        signals.append({**best, 'strength': 'STRONG', 'timeframes_agree': buy_count, 'reason': f"{buy_count} timeframes show BUY"})
                    elif sell_count >= 2:
                        best = max(coin_signals, key=lambda x: x['confidence'])
                        signals.append({**best, 'strength': 'STRONG', 'timeframes_agree': sell_count, 'reason': f"{sell_count} timeframes show SELL"})
            
            signals.sort(key=lambda x: x['confidence'], reverse=True)
            self.signals = signals[:20]
            
            logger.info(f"✅ Generated {len(signals)} multi-timeframe signals")
            
        except Exception as e:
            logger.error(f"❌ Error generating signals: {e}")
    
    def _store_signals(self, signals: List[Dict]):
        """Store signals in database"""
        try:
            from app.db.database import SessionLocal
            from app.db.models import Signal
            
            db = SessionLocal()
            try:
                for sig in signals:
                    signal = Signal(
                        coin=sig['coin'],
                        timestamp=sig['timestamp'],
                        signal=sig['signal'],
                        confidence=sig['confidence'],
                        current_price=sig['current_price'],
                        target_price=sig['target_price'],
                        reason=sig['reason']
                    )
                    db.add(signal)
                
                db.commit()
                
            except Exception as e:
                logger.error(f"❌ Error storing signals: {e}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Database error in store_signals: {e}")
    
    def get_latest_data(self) -> Dict:
        """Get latest multi-timeframe data"""
        return {
            'timestamp': datetime.now(),
            'coins_tracked': len(self.coins),
            'timeframes': self.TIMEFRAMES,
            'candle_data': self.candle_data,
            'predictions': self.predictions,
            'signals': self.signals,
            'last_prediction': self.last_prediction_time
        }


# Global automation instance
_automation: Optional[MultiTimeframeAutomation] = None

def start_automation(coins: List[str] = None):
    """Start the 24/7 multi-timeframe automation service"""
    global _automation
    
    if coins is None:
        coins = [
            "BTC", "ETH", "BNB", "SOL", "XRP",
            "ADA", "AVAX", "DOGE", "DOT", "LINK",
            "MATIC", "LTC", "BCH", "UNI", "ATOM",
            "XLM", "ICP"
        ]
    
    if _automation is None:
        _automation = MultiTimeframeAutomation(coins)
        _automation.start()
    
    return _automation

def stop_automation():
    """Stop the automation service"""
    global _automation
    if _automation:
        _automation.stop()
        _automation = None

def get_automation_status():
    """Get current automation status"""
    if _automation:
        return _automation.get_latest_data()
    return None


if __name__ == "__main__":
    # Test the automation
    auto = start_automation()
    
    try:
        while True:
            time.sleep(10)
            status = get_automation_status()
            if status:
                print(f"✅ Running - {status['coins_tracked']} coins tracked")
    except KeyboardInterrupt:
        stop_automation()
        print("\n⏹️ Automation stopped")
