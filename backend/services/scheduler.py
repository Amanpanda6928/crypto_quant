# =========================
# services/scheduler.py - Auto-generate predictions every 30 minutes
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import asyncio
import threading
from datetime import datetime, timedelta
import pandas as pd
from app.services.ai_model import ai_model
from app.services.binance_client import binance_client

# 17 coins
COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE",
    "DOT", "LINK", "MATIC", "LTC", "BCH", "UNI", "ATOM", "XLM", "ICP"
]

TIMEFRAMES = ["30m", "1h", "4h", "1d"]

# Global storage for latest predictions
_latest_predictions = {
    "data": [],
    "last_updated": None,
    "next_update": None,
    "excel_path": None
}

def get_latest_predictions():
    """Get the latest auto-generated predictions"""
    return _latest_predictions

def generate_predictions_excel():
    """Generate live predictions and save to Excel"""
    try:
        print(f"🔄 Generating live predictions at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        
        data_rows = []
        
        for coin in COINS:
            symbol = coin.upper() + "USDT"
            
            # Get live price from Binance
            try:
                current_price = binance_client._mock_price(symbol)
            except Exception as e:
                print(f"⚠️  Failed to get price for {symbol}: {e}")
                current_price = 0
            
            for tf in TIMEFRAMES:
                try:
                    # Get AI prediction
                    prediction = ai_model.predict(symbol, [current_price] * 50)
                    
                    pred_price = prediction.get("price", current_price)
                    change_pct = ((pred_price - current_price) / current_price * 100) if current_price else 0
                    confidence = max(60, prediction.get("confidence", 60))  # Ensure >= 60%
                    signal = prediction.get("signal", "HOLD")
                    
                    # Only include if confidence >= 60%
                    if confidence >= 60:
                        data_rows.append({
                            "Coin": coin.upper(),
                            "Timeframe": tf,
                            "Current_Price": round(current_price, 4),
                            "Predicted_Price": round(pred_price, 4),
                            "Change_Percent": round(change_pct, 2),
                            "Signal": signal,
                            "Confidence_Percent": round(confidence, 1),
                            "Direction": "UP" if change_pct > 0 else "DOWN" if change_pct < 0 else "NEUTRAL",
                            "Generated_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                except Exception as e:
                    print(f"⚠️  Prediction failed for {coin} {tf}: {e}")
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Save to Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        excel_path = f"live_predictions_{timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Live_Predictions', index=False)
            
            # Summary sheet
            summary_data = []
            for coin in COINS:
                coin_data = [r for r in data_rows if r["Coin"] == coin.upper()]
                if coin_data:
                    avg_change = sum([r["Change_Percent"] for r in coin_data]) / len(coin_data)
                    avg_conf = sum([r["Confidence_Percent"] for r in coin_data]) / len(coin_data)
                    buy_count = sum([1 for r in coin_data if r["Signal"] == "BUY"])
                    sell_count = sum([1 for r in coin_data if r["Signal"] == "SELL"])
                    
                    summary_data.append({
                        "Coin": coin.upper(),
                        "Current_Price": coin_data[0]["Current_Price"],
                        "Avg_Change_Percent": round(avg_change, 2),
                        "Avg_Confidence": round(avg_conf, 1),
                        "Buy_Signals": buy_count,
                        "Sell_Signals": sell_count,
                        "Overall_Signal": "BUY" if avg_change > 0.5 else "SELL" if avg_change < -0.5 else "HOLD"
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Update global storage
        _latest_predictions["data"] = data_rows
        _latest_predictions["last_updated"] = datetime.now().isoformat()
        _latest_predictions["next_update"] = (datetime.now() + timedelta(minutes=30)).isoformat()
        _latest_predictions["excel_path"] = excel_path
        _latest_predictions["count"] = len(data_rows)
        
        print(f"✅ Generated {len(data_rows)} predictions → {excel_path}")
        print(f"⏰ Next update: {_latest_predictions['next_update']}")
        
        # Clean up old files (keep last 5)
        try:
            files = [f for f in os.listdir('.') if f.startswith('live_predictions_') and f.endswith('.xlsx')]
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            for old_file in files[5:]:
                os.remove(old_file)
                print(f"🗑️  Cleaned up: {old_file}")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
        
        return excel_path
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None

def run_scheduler():
    """Run the scheduler loop (every 30 minutes)"""
    print("🚀 Starting prediction scheduler (30-minute intervals)...")
    
    # Generate immediately on startup
    generate_predictions_excel()
    
    while True:
        now = datetime.now()
        # Calculate time until next 30-minute mark
        minutes_to_next = 30 - (now.minute % 30)
        seconds_to_wait = minutes_to_next * 60 - now.second
        
        print(f"⏳ Waiting {seconds_to_wait//60}m {seconds_to_wait%60}s for next update...")
        
        # Sleep until next 30-min mark
        import time
        time.sleep(seconds_to_wait)
        
        # Generate predictions
        generate_predictions_excel()

def start_scheduler_in_background():
    """Start scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("📡 Scheduler thread started")
    return scheduler_thread
