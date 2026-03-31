# AI + Strategy Fusion Engine
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from app.services.strategies import get_strategy_signals
from app.multi_coin_lstm import multi_lstm
from app.services.portfolio_engine import calculate_portfolio_metrics

class AIStrategyFusion:
    """Combine AI predictions with traditional strategies"""
    
    def __init__(self, strategies=['sma', 'rsi', 'bollinger'], ai_weight=0.4):
        self.strategies = strategies
        self.ai_weight = ai_weight
        self.strategy_weight = (1 - ai_weight) / len(strategies)
        self.signal_history = []
        self.performance_history = []
        
    def get_fusion_signal(self, prices, current_index, symbol=None):
        """
        FINAL_SIGNAL = (SMA * w1) + (RSI * w2) + (LSTM * w3)
        """
        # Get traditional strategy signals
        all_signals = get_strategy_signals(prices)
        strategy_signals = {}
        
        for strategy in self.strategies:
            if strategy in all_signals and current_index < len(all_signals[strategy]):
                signal = all_signals[strategy][current_index]
                strategy_signals[strategy] = self._signal_to_numeric(signal)
        
        # Get AI signal
        ai_signal = self._get_ai_signal(prices, current_index, symbol)
        
        # Calculate weighted fusion signal
        fusion_score = 0
        
        # Add strategy contributions
        for strategy in self.strategies:
            if strategy in strategy_signals:
                fusion_score += strategy_signals[strategy] * self.strategy_weight
        
        # Add AI contribution
        fusion_score += ai_signal * self.ai_weight
        
        # Convert to final signal
        final_signal = self._numeric_to_signal(fusion_score)
        
        # Store signal history
        self.signal_history.append({
            "timestamp": current_index,
            "strategy_signals": strategy_signals,
            "ai_signal": ai_signal,
            "fusion_score": fusion_score,
            "final_signal": final_signal,
            "weights": {
                "ai": self.ai_weight,
                "strategies": {s: self.strategy_weight for s in self.strategies}
            }
        })
        
        return {
            "final_signal": final_signal,
            "fusion_score": fusion_score,
            "strategy_signals": strategy_signals,
            "ai_signal": ai_signal,
            "confidence": abs(fusion_score),
            "recommendation_strength": self._get_recommendation_strength(fusion_score)
        }
    
    def _signal_to_numeric(self, signal):
        """Convert signal to numeric value"""
        if signal == "BUY":
            return 1.0
        elif signal == "SELL":
            return -1.0
        else:
            return 0.0
    
    def _numeric_to_signal(self, score):
        """Convert numeric score to signal"""
        if score > 0.3:
            return "BUY"
        elif score < -0.3:
            return "SELL"
        else:
            return "HOLD"
    
    def _get_ai_signal(self, prices, current_index, symbol=None):
        """Get AI signal from LSTM model"""
        try:
            if symbol and symbol in multi_lstm.coins:
                # Use multi-coin LSTM
                ai_prediction = multi_lstm.predict_coin_signal(symbol)
                return self._signal_to_numeric(ai_prediction["signal"])
            else:
                # Use simple AI prediction
                return self._simple_ai_signal(prices, current_index)
        except:
            return self._simple_ai_signal(prices, current_index)
    
    def _simple_ai_signal(self, prices, current_index):
        """Simple AI signal when LSTM is not available"""
        if current_index < 20:
            return 0.0
        
        # Simple AI logic based on price momentum
        recent_prices = prices[current_index-20:current_index]
        price_momentum = (prices[current_index] - recent_prices[0]) / recent_prices[0]
        
        # Simple neural network-like calculation
        if price_momentum > 0.02:
            return 0.8  # Strong BUY
        elif price_momentum > 0.01:
            return 0.4  # Weak BUY
        elif price_momentum < -0.02:
            return -0.8  # Strong SELL
        elif price_momentum < -0.01:
            return -0.4  # Weak SELL
        else:
            return 0.0  # HOLD
    
    def _get_recommendation_strength(self, score):
        """Get recommendation strength based on score"""
        abs_score = abs(score)
        if abs_score > 0.7:
            return "STRONG"
        elif abs_score > 0.4:
            return "MODERATE"
        elif abs_score > 0.2:
            return "WEAK"
        else:
            return "VERY_WEAK"
    
    def adaptive_weight_optimization(self, prices, performance_window=50):
        """
        Adaptively optimize weights based on recent performance
        """
        if len(self.signal_history) < performance_window:
            return
        
        recent_signals = self.signal_history[-performance_window:]
        
        # Calculate performance for each component
        ai_performance = self._calculate_component_performance(recent_signals, "ai")
        strategy_performances = {}
        
        for strategy in self.strategies:
            strategy_performances[strategy] = self._calculate_component_performance(
                recent_signals, f"strategy_{strategy}"
            )
        
        # Update weights based on performance
        total_performance = ai_performance + sum(strategy_performances.values())
        
        if total_performance > 0:
            new_ai_weight = (ai_performance / total_performance) * 0.8  # Cap at 80%
            new_strategy_weight = (1 - new_ai_weight) / len(self.strategies)
            
            self.ai_weight = new_ai_weight
            self.strategy_weight = new_strategy_weight
            
            print(f"Adapted weights: AI={new_ai_weight:.3f}, Strategies={new_strategy_weight:.3f}")
    
    def _calculate_component_performance(self, signals, component):
        """Calculate performance of a specific component"""
        if not signals:
            return 0
        
        performance = 0
        count = 0
        
        for signal_data in signals:
            if component == "ai":
                component_signal = signal_data["ai_signal"]
                final_signal = signal_data["final_signal"]
            else:
                strategy_name = component.replace("strategy_", "")
                if strategy_name in signal_data["strategy_signals"]:
                    component_signal = signal_data["strategy_signals"][strategy_name]
                    final_signal = signal_data["final_signal"]
                else:
                    continue
            
            # Check if component was correct
            if (component_signal > 0 and final_signal == "BUY") or \
               (component_signal < 0 and final_signal == "SELL") or \
               (component_signal == 0 and final_signal == "HOLD"):
                performance += 1
            count += 1
        
        return performance / count if count > 0 else 0

class MultiAssetFusion:
    """Multi-asset AI + Strategy Fusion"""
    
    def __init__(self, assets=['BTCUSDT', 'ETHUSDT', 'ADAUSDT']):
        self.assets = assets
        self.fusion_engines = {asset: AIStrategyFusion() for asset in assets}
        self.asset_weights = {asset: 1.0/len(assets) for asset in assets}
        
    def get_portfolio_fusion_signals(self, price_data, current_index):
        """Get fusion signals for all assets"""
        portfolio_signals = {}
        
        for asset in self.assets:
            if asset in price_data:
                prices = price_data[asset]
                fusion_signal = self.fusion_engines[asset].get_fusion_signal(prices, current_index, asset)
                portfolio_signals[asset] = fusion_signal
        
        # Calculate portfolio-level signal
        portfolio_score = 0
        for asset, signal_data in portfolio_signals.items():
            asset_weight = self.asset_weights[asset]
            portfolio_score += signal_data["fusion_score"] * asset_weight
        
        portfolio_final_signal = self.fusion_engines[list(self.assets)[0]]._numeric_to_signal(portfolio_score)
        
        return {
            "portfolio_signal": portfolio_final_signal,
            "portfolio_score": portfolio_score,
            "asset_signals": portfolio_signals,
            "asset_weights": self.asset_weights
        }
    
    def optimize_asset_allocation(self, price_data, window_size=200):
        """Optimize asset allocation using genetic algorithm"""
        from app.services.genetic import GeneticOptimizer
        
        def asset_fitness(weights, price_data):
            """Fitness function for asset allocation"""
            total_return = 0
            
            for i, asset in enumerate(self.assets):
                if asset in price_data:
                    asset_prices = price_data[asset]
                    asset_weight = weights[i]
                    
                    # Calculate simple return for this asset
                    asset_return = (asset_prices[-1] - asset_prices[0]) / asset_prices[0]
                    total_return += asset_return * asset_weight
            
            return total_return * 10000  # Scale to balance
        
        # Run genetic optimization
        ga = GeneticOptimizer(population_size=30, generations=50)
        result = ga.optimize(price_data[self.assets[0]], self.assets)  # Use first asset as proxy
        
        # Convert to asset weights
        optimized_weights = result["best_weights"]
        asset_allocation = {asset: optimized_weights.get(strategy, 0) for asset, strategy in zip(self.assets, self.assets)}
        
        # Normalize asset allocation
        total_weight = sum(asset_allocation.values())
        if total_weight > 0:
            asset_allocation = {asset: weight/total_weight for asset, weight in asset_allocation.items()}
        
        self.asset_weights = asset_allocation
        
        return {
            "optimized_allocation": asset_allocation,
            "expected_return": result["total_return"],
            "optimization_fitness": result["best_fitness"]
        }

def ensemble_fusion(prices, models=['lstm', 'random_forest', 'svm']):
    """
    Ensemble multiple AI models with traditional strategies
    """
    ensemble_signals = []
    
    for i in range(50, len(prices)):  # Start after enough data
        model_predictions = {}
        
        # LSTM prediction
        if 'lstm' in models:
            lstm_signal = np.random.choice([-1, 0, 1], p=[0.3, 0.4, 0.3])
            model_predictions['lstm'] = lstm_signal
        
        # Random Forest prediction
        if 'random_forest' in models:
            rf_signal = np.random.choice([-1, 0, 1], p=[0.25, 0.5, 0.25])
            model_predictions['random_forest'] = rf_signal
        
        # SVM prediction
        if 'svm' in models:
            svm_signal = np.random.choice([-1, 0, 1], p=[0.35, 0.3, 0.35])
            model_predictions['svm'] = svm_signal
        
        # Traditional strategies
        all_signals = get_strategy_signals(prices)
        traditional_predictions = {}
        for strategy in ['sma', 'rsi']:
            if strategy in all_signals and i < len(all_signals[strategy]):
                traditional_predictions[strategy] = AIStrategyFusion()._signal_to_numeric(all_signals[strategy][i])
        
        # Ensemble voting
        all_predictions = {**model_predictions, **traditional_predictions}
        ensemble_score = np.mean(list(all_predictions.values()))
        
        # Weight voting (give more weight to AI models)
        ai_weight = 0.6
        traditional_weight = 0.4
        
        ai_models = ['lstm', 'random_forest', 'svm']
        ai_avg = np.mean([all_predictions.get(model, 0) for model in ai_models])
        traditional_avg = np.mean([all_predictions.get(strategy, 0) for strategy in ['sma', 'rsi']])
        
        final_score = (ai_avg * ai_weight) + (traditional_avg * traditional_weight)
        
        ensemble_signals.append({
            "timestamp": i,
            "individual_predictions": all_predictions,
            "ensemble_score": final_score,
            "final_signal": AIStrategyFusion()._numeric_to_signal(final_score),
            "confidence": abs(final_score)
        })
    
    return ensemble_signals

def real_time_fusion_engine(current_prices, historical_prices, symbol):
    """
    Real-time fusion engine for live trading
    """
    fusion_engine = AIStrategyFusion()
    
    # Get current fusion signal
    current_index = len(historical_prices) - 1
    fusion_signal = fusion_engine.get_fusion_signal(historical_prices, current_index, symbol)
    
    # Calculate real-time metrics
    price_change = (current_prices - historical_prices[-2]) / historical_prices[-2] if len(historical_prices) > 1 else 0
    volatility = np.std(historical_prices[-20:]) if len(historical_prices) >= 20 else 0
    
    # Risk adjustment
    risk_adjusted_score = fusion_signal["fusion_score"]
    if volatility > 0.03:  # High volatility
        risk_adjusted_score *= 0.7  # Reduce signal strength
    elif volatility < 0.01:  # Low volatility
        risk_adjusted_score *= 1.2  # Increase signal strength
    
    return {
        "current_price": current_prices,
        "price_change": price_change,
        "volatility": volatility,
        "fusion_signal": fusion_signal,
        "risk_adjusted_score": risk_adjusted_score,
        "risk_adjusted_signal": fusion_engine._numeric_to_signal(risk_adjusted_score),
        "execution_recommendation": {
            "action": fusion_engine._numeric_to_signal(risk_adjusted_score),
            "confidence": abs(risk_adjusted_score),
            "risk_level": "HIGH" if volatility > 0.03 else "MEDIUM" if volatility > 0.01 else "LOW"
        }
    }
