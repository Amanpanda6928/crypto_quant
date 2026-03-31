# Professional Execution Engine
import asyncio
import websockets
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import queue

class ExecutionEngine:
    """Professional Real-time Execution Engine"""
    
    def __init__(self):
        self.is_running = False
        self.execution_queue = queue.Queue()
        self.market_data = {}
        self.feature_engine = None
        self.strategies = {}
        self.ai_models = {}
        self.optimizer = None
        self.risk_manager = None
        self.position_manager = None
        self.logger = None
        
        # Performance tracking
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "last_execution": None
        }
        
        # WebSocket connections
        self.binance_ws = None
        self.redis_client = None
        
    async def start(self, config: Dict):
        """Start the execution engine"""
        print("🚀 Starting Execution Engine...")
        
        # Initialize components
        await self._initialize_components(config)
        
        # Start WebSocket connections
        await self._start_websocket_connections()
        
        # Start async workers
        self.is_running = True
        
        # Start main execution loop
        await self._main_execution_loop()
    
    async def _initialize_components(self, config: Dict):
        """Initialize all engine components"""
        # Feature Engine
        self.feature_engine = FeatureEngine()
        
        # Load strategies
        from app.services.strategies import get_strategy_signals
        self.strategies = {
            'sma': SMAStrategy(),
            'rsi': RSIStrategy(),
            'bollinger': BollingerStrategy(),
            'macd': MACDStrategy()
        }
        
        # Load AI models
        from app.multi_coin_lstm import multi_lstm
        self.ai_models = {
            'lstm': multi_lstm
        }
        
        # Initialize optimizer
        from app.services.genetic import GeneticOptimizer
        self.optimizer = GeneticOptimizer()
        
        # Initialize risk manager
        from app.services.risk_manager import risk_manager
        self.risk_manager = risk_manager
        
        # Initialize position manager
        self.position_manager = PositionManager()
        
        # Initialize logger
        self.logger = ExecutionLogger()
        
        print("✅ All components initialized")
    
    async def _start_websocket_connections(self):
        """Start WebSocket connections to exchanges"""
        try:
            # Binance WebSocket for real-time data
            self.binance_ws = await websockets.connect(
                "wss://stream.binance.com:9443/ws/btcusdt@ticker"
            )
            print("✅ Connected to Binance WebSocket")
            
            # Start WebSocket listener
            asyncio.create_task(self._websocket_listener())
            
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            # Fallback to HTTP polling
            asyncio.create_task(self._http_polling_fallback())
    
    async def _websocket_listener(self):
        """Listen to WebSocket messages"""
        try:
            async for message in self.binance_ws:
                data = json.loads(message)
                await self._process_market_data(data)
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def _http_polling_fallback(self):
        """HTTP polling fallback for market data"""
        import aiohttp
        
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT') as response:
                        data = await response.json()
                        await self._process_market_data(data)
                        
            except Exception as e:
                print(f"❌ HTTP polling error: {e}")
            
            await asyncio.sleep(1)  # Poll every second
    
    async def _process_market_data(self, data: Dict):
        """Process incoming market data"""
        try:
            # Extract price and timestamp
            price = float(data.get('c', data.get('price', 0)))
            timestamp = data.get('E', data.get('time', time.time()))
            
            # Update market data
            symbol = data.get('s', 'BTCUSDT')
            self.market_data[symbol] = {
                'price': price,
                'timestamp': timestamp,
                'volume': float(data.get('v', 0)),
                'high': float(data.get('h', price)),
                'low': float(data.get('l', price)),
                'open': float(data.get('o', price))
            }
            
            # Trigger execution pipeline
            await self._trigger_execution_pipeline(symbol)
            
        except Exception as e:
            print(f"❌ Market data processing error: {e}")
    
    async def _trigger_execution_pipeline(self, symbol: str):
        """Trigger the complete execution pipeline"""
        try:
            # 1. Feature Engine → Extract features
            features = await self.feature_engine.extract_features(self.market_data, symbol)
            
            # 2. Strategies → Generate signals
            strategy_signals = {}
            for strategy_name, strategy in self.strategies.items():
                signal = await strategy.generate_signal(features, symbol)
                strategy_signals[strategy_name] = signal
            
            # 3. AI Model → Get AI predictions
            ai_predictions = {}
            for model_name, model in self.ai_models.items():
                prediction = await model.predict(features, symbol)
                ai_predictions[model_name] = prediction
            
            # 4. Optimizer → Optimize weights
            optimized_weights = await self.optimizer.optimize_weights(
                strategy_signals, ai_predictions, symbol
            )
            
            # 5. Risk Manager → Risk assessment
            risk_assessment = await self.risk_manager.assess_trade_risk(
                symbol, optimized_weights, self.market_data[symbol]
            )
            
            # 6. Execution → Execute trades
            if risk_assessment['approved']:
                execution_result = await self._execute_trade(
                    symbol, optimized_weights, risk_assessment
                )
                
                # 7. Logging → Log everything
                await self.logger.log_execution({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'features': features,
                    'strategy_signals': strategy_signals,
                    'ai_predictions': ai_predictions,
                    'optimized_weights': optimized_weights,
                    'risk_assessment': risk_assessment,
                    'execution_result': execution_result
                })
            
        except Exception as e:
            print(f"❌ Execution pipeline error: {e}")
    
    async def _execute_trade(self, symbol: str, weights: Dict, risk_assessment: Dict):
        """Execute trade with risk management"""
        start_time = time.time()
        
        try:
            # Calculate final signal
            final_signal = self._calculate_final_signal(weights)
            
            if final_signal == 'HOLD':
                return {
                    'action': 'HOLD',
                    'reason': 'No clear signal',
                    'execution_time': time.time() - start_time
                }
            
            # Check position limits
            if not self.risk_manager.check_position_limit(symbol):
                return {
                    'action': 'REJECTED',
                    'reason': 'Position limit exceeded',
                    'execution_time': time.time() - start_time
                }
            
            # Calculate position size
            current_price = self.market_data[symbol]['price']
            position_size = self._calculate_position_size(
                current_price, risk_assessment
            )
            
            # Execute trade
            if final_signal == 'BUY':
                order_result = await self._execute_buy_order(symbol, position_size)
            else:  # SELL
                order_result = await self._execute_sell_order(symbol, position_size)
            
            # Update position manager
            if order_result['success']:
                self.position_manager.add_position(symbol, {
                    'side': final_signal,
                    'size': position_size,
                    'entry_price': current_price,
                    'timestamp': datetime.now(),
                    'order_id': order_result['order_id']
                })
            
            execution_time = time.time() - start_time
            self._update_execution_stats(True, execution_time)
            
            return {
                'action': final_signal,
                'symbol': symbol,
                'size': position_size,
                'price': current_price,
                'order_result': order_result,
                'execution_time': execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_execution_stats(False, execution_time)
            
            return {
                'action': 'ERROR',
                'error': str(e),
                'execution_time': execution_time
            }
    
    def _calculate_final_signal(self, weights: Dict) -> str:
        """Calculate final trading signal from weights"""
        total_score = 0
        
        # Sum weighted scores
        for component, weight in weights.items():
            signal_score = weights.get(component, {}).get('score', 0)
            total_score += signal_score * weight.get('weight', 0)
        
        # Convert to signal
        if total_score > 0.3:
            return 'BUY'
        elif total_score < -0.3:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_position_size(self, current_price: float, risk_assessment: Dict) -> float:
        """Calculate optimal position size"""
        # Base position size
        base_size = 100.0  # USDT
        
        # Adjust for risk
        risk_multiplier = risk_assessment.get('risk_multiplier', 1.0)
        adjusted_size = base_size * risk_multiplier
        
        # Ensure minimum position size
        min_size = 10.0  # USDT
        return max(adjusted_size, min_size)
    
    async def _execute_buy_order(self, symbol: str, size: float) -> Dict:
        """Execute buy order"""
        try:
            # Mock execution - replace with real broker API
            order_id = f"BUY_{symbol}_{int(time.time())}"
            
            print(f"🟢 BUY Order: {symbol} - Size: {size} USDT")
            
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'side': 'BUY',
                'size': size,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_sell_order(self, symbol: str, size: float) -> Dict:
        """Execute sell order"""
        try:
            # Mock execution - replace with real broker API
            order_id = f"SELL_{symbol}_{int(time.time())}"
            
            print(f"🔴 SELL Order: {symbol} - Size: {size}")
            
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'side': 'SELL',
                'size': size,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_execution_stats(self, success: bool, execution_time: float):
        """Update execution statistics"""
        self.execution_stats['total_executions'] += 1
        
        if success:
            self.execution_stats['successful_executions'] += 1
        else:
            self.execution_stats['failed_executions'] += 1
        
        # Update average execution time
        total_time = (self.execution_stats['average_execution_time'] * 
                      (self.execution_stats['total_executions'] - 1) + execution_time)
        self.execution_stats['average_execution_time'] = total_time / self.execution_stats['total_executions']
        self.execution_stats['last_execution'] = datetime.now()
    
    async def _main_execution_loop(self):
        """Main execution loop"""
        print("🔄 Execution engine started")
        
        while self.is_running:
            try:
                # Process any queued executions
                while not self.execution_queue.empty():
                    execution_task = self.execution_queue.get()
                    await self._execute_trade(**execution_task)
                
                # Periodic tasks
                await self._periodic_tasks()
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                await asyncio.sleep(1)
    
    async def _periodic_tasks(self):
        """Periodic maintenance tasks"""
        current_time = datetime.now()
        
        # Update position PnL
        await self.position_manager.update_pnl(self.market_data)
        
        # Risk management checks
        await self.risk_manager.comprehensive_risk_check(
            self.position_manager.get_total_equity(),
            self.position_manager.get_account_balance(),
            self.position_manager.get_returns()
        )
        
        # Log performance metrics
        if current_time.second % 30 == 0:  # Every 30 seconds
            await self.logger.log_performance(self.execution_stats)
    
    async def stop(self):
        """Stop the execution engine"""
        print("🛑 Stopping Execution Engine...")
        
        self.is_running = False
        
        # Close WebSocket connections
        if self.binance_ws:
            await self.binance_ws.close()
        
        # Close all positions
        await self.position_manager.close_all_positions()
        
        print("✅ Execution Engine stopped")
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            'is_running': self.is_running,
            'market_data_connected': len(self.market_data) > 0,
            'active_strategies': list(self.strategies.keys()),
            'active_ai_models': list(self.ai_models.keys()),
            'execution_stats': self.execution_stats,
            'position_status': self.position_manager.get_status(),
            'risk_level': self.risk_manager.get_risk_summary() if self.risk_manager else None
        }

# Supporting classes
class FeatureEngine:
    """Feature extraction engine"""
    
    async def extract_features(self, market_data: Dict, symbol: str) -> Dict:
        """Extract technical features from market data"""
        if symbol not in market_data:
            return {}
        
        data = market_data[symbol]
        
        # Calculate technical indicators
        features = {
            'price': data['price'],
            'volume': data['volume'],
            'high': data['high'],
            'low': data['low'],
            'open': data['open'],
            'price_change': (data['price'] - data['open']) / data['open'],
            'volatility': (data['high'] - data['low']) / data['open'],
            'range_ratio': (data['high'] - data['low']) / data['price']
        }
        
        return features

class SMAStrategy:
    """SMA Strategy implementation"""
    
    async def generate_signal(self, features: Dict, symbol: str) -> Dict:
        """Generate SMA signal"""
        # Mock SMA calculation
        score = 0.1 if features.get('price_change', 0) > 0 else -0.1
        
        return {
            'signal': 'BUY' if score > 0 else 'SELL',
            'score': score,
            'confidence': abs(score)
        }

class RSIStrategy:
    """RSI Strategy implementation"""
    
    async def generate_signal(self, features: Dict, symbol: str) -> Dict:
        """Generate RSI signal"""
        # Mock RSI calculation
        score = 0.2 if features.get('volatility', 0) > 0.02 else -0.2
        
        return {
            'signal': 'BUY' if score > 0 else 'SELL',
            'score': score,
            'confidence': abs(score)
        }

class BollingerStrategy:
    """Bollinger Bands Strategy implementation"""
    
    async def generate_signal(self, features: Dict, symbol: str) -> Dict:
        """Generate Bollinger signal"""
        # Mock Bollinger calculation
        range_ratio = features.get('range_ratio', 0)
        score = 0.3 if range_ratio > 0.05 else -0.3
        
        return {
            'signal': 'BUY' if score > 0 else 'SELL',
            'score': score,
            'confidence': abs(score)
        }

class MACDStrategy:
    """MACD Strategy implementation"""
    
    async def generate_signal(self, features: Dict, symbol: str) -> Dict:
        """Generate MACD signal"""
        # Mock MACD calculation
        momentum = features.get('price_change', 0)
        score = 0.25 if momentum > 0.01 else -0.25
        
        return {
            'signal': 'BUY' if score > 0 else 'SELL',
            'score': score,
            'confidence': abs(score)
        }

class PositionManager:
    """Position management system"""
    
    def __init__(self):
        self.positions = {}
        self.account_balance = 10000.0
    
    def add_position(self, symbol: str, position_data: Dict):
        """Add new position"""
        self.positions[symbol] = position_data
    
    def update_pnl(self, market_data: Dict):
        """Update PnL for all positions"""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol]['price']
                entry_price = position['entry_price']
                size = position['size']
                
                pnl = (current_price - entry_price) * size
                position['unrealized_pnl'] = pnl
                position['current_price'] = current_price
    
    def get_total_equity(self) -> float:
        """Get total portfolio equity"""
        total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in self.positions.values())
        return self.account_balance + total_pnl
    
    def get_account_balance(self) -> float:
        """Get account balance"""
        return self.account_balance
    
    def get_returns(self) -> List[float]:
        """Get historical returns"""
        # Mock returns
        return [0.01, -0.005, 0.02, 0.015, -0.01]
    
    def get_status(self) -> Dict:
        """Get position manager status"""
        return {
            'total_positions': len(self.positions),
            'total_equity': self.get_total_equity(),
            'account_balance': self.account_balance,
            'positions': self.positions
        }
    
    async def close_all_positions(self):
        """Close all positions"""
        for symbol in list(self.positions.keys()):
            print(f"Closing position: {symbol}")
            del self.positions[symbol]

class ExecutionLogger:
    """Execution logging system"""
    
    async def log_execution(self, execution_data: Dict):
        """Log execution data"""
        log_entry = {
            'timestamp': execution_data['timestamp'],
            'symbol': execution_data['symbol'],
            'action': execution_data.get('execution_result', {}).get('action'),
            'size': execution_data.get('execution_result', {}).get('size'),
            'price': execution_data.get('execution_result', {}).get('price'),
            'execution_time': execution_data.get('execution_result', {}).get('execution_time')
        }
        
        print(f"📝 Execution Log: {log_entry}")
    
    async def log_performance(self, stats: Dict):
        """Log performance statistics"""
        print(f"📊 Performance Stats: {stats}")

# Global execution engine instance
execution_engine = ExecutionEngine()
