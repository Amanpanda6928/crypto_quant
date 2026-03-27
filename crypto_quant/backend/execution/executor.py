"""
Execution Engine (Paper Trading + Real Binance)
"""

import os
from typing import Dict, Optional
from ..utils.config import get_config


class TradeExecutor:

    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self.config = get_config()
        
        if not paper_trading:
            try:
                from binance.client import Client
                self.client = Client(
                    self.config.get('api_key'),
                    self.config.get('api_secret')
                )
                print("✅ Real Binance trading enabled")
            except Exception as e:
                print(f"❌ Binance client error: {e}")
                print("Falling back to paper trading")
                self.paper_trading = True
        else:
            print("📝 Paper trading mode")

    def submit_order(self, symbol, side, quantity, price):

        if self.paper_trading:
            return self._paper_order(symbol, side, quantity, price)
        else:
            return self._real_order(symbol, side, quantity, price)

    def _paper_order(self, symbol, side, quantity, price):
        print(f"[PAPER] {side.upper()} {symbol} | qty={quantity:.4f} @ {price:.2f}")

        return {
            "symbol": symbol,
            "side": side,
            "qty": quantity,
            "price": price,
            "status": "filled",
            "paper": True
        }

    def _real_order(self, symbol, side, quantity, price):
        try:
            # Convert to Binance format
            symbol = symbol.upper()
            side = side.upper()
            
            # For simplicity, use market order
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            print(f"[REAL] {side} {symbol} | qty={quantity:.4f} | status={order['status']}")
            
            return {
                "symbol": symbol,
                "side": side,
                "qty": quantity,
                "price": price,
                "status": order['status'],
                "order_id": order['orderId'],
                "paper": False
            }
            
        except Exception as e:
            print(f"[ERROR] Real order failed: {e}")
            # Fallback to paper
            return self._paper_order(symbol, side, quantity, price)

