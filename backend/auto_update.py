#!/usr/bin/env python3
"""Auto-update service - Fetches live prices every 5 minutes"""
import sys
sys.path.insert(0, '.')

import time
import threading
from datetime import datetime
from app.services.coingecko_service import get_coingecko_service
from app.services.live_prediction_service import get_live_service, COINS, TIMEFRAMES

class AutoUpdateService:
    """Background service that updates prices every 5 minutes"""
    
    def __init__(self, interval_minutes=5):
        self.interval = interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread = None
        self.update_count = 0
    
    def start(self):
        """Start the auto-update service"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print(f"🚀 Auto-update started - Every {self.interval//60} minutes")
    
    def stop(self):
        """Stop the auto-update service"""
        self.running = False
        print("🛑 Auto-update stopped")
    
    def _run_loop(self):
        """Main update loop"""
        # Initial update
        self._do_update()
        
        while self.running:
            time.sleep(self.interval)
            if self.running:
                self._do_update()
    
    def _do_update(self):
        """Perform one update cycle"""
        self.update_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"🔄 UPDATE #{self.update_count} - {timestamp}")
        print('='*60)
        
        # 1. Fetch real prices
        print("📊 Fetching live prices from CoinGecko...")
        coingecko = get_coingecko_service()
        prices = coingecko.get_all_prices()
        
        if prices:
            print(f"✅ Fetched {len(prices)} coins")
            for coin, price in sorted(prices.items())[:5]:
                print(f"   {coin}: ${price:,.2f}")
        else:
            print("⚠️  Failed to fetch prices, using cached")
        
        # 2. Generate new predictions
        print("\n🔮 Generating AI predictions...")
        service = get_live_service()
        predictions = service.generate_all_predictions()
        
        # 3. Summary
        buy = sum(1 for p in predictions if p['signal'] == 'BUY')
        sell = sum(1 for p in predictions if p['signal'] == 'SELL')
        hold = sum(1 for p in predictions if p['signal'] == 'HOLD')
        
        print(f"\n📈 Predictions: 🟢{buy} 🔴{sell} ⚪{hold}")
        print(f"✅ Update #{self.update_count} complete!")
        print('='*60)

# Global instance
_auto_service = None

def start_auto_update(interval_minutes=5):
    """Start auto-update service"""
    global _auto_service
    if _auto_service is None:
        _auto_service = AutoUpdateService(interval_minutes)
    _auto_service.start()
    return _auto_service

def stop_auto_update():
    """Stop auto-update service"""
    global _auto_service
    if _auto_service:
        _auto_service.stop()

if __name__ == "__main__":
    print("🚀 Starting Auto-Update Service")
    print("📊 Updates every 5 minutes")
    print("⏹️  Press Ctrl+C to stop\n")
    
    service = start_auto_update(5)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        stop_auto_update()
        print("✅ Stopped")
