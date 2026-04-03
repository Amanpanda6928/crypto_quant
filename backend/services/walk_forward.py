# Walk-Forward Validation Engine
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from services.strategies import get_strategy_signals, calculate_strategy_performance
from multi_coin_lstm import multi_lstm

def walk_forward_validation(prices, window_size=200, step_size=50, strategies=None):
    """
    Walk-Forward Validation: Train → Test → Slide window → Repeat
    
    This prevents look-ahead bias by training on past data only
    and testing on future unseen data.
    """
    if strategies is None:
        strategies = ['sma', 'rsi', 'bollinger']
    
    results = []
    windows = []
    
    for i in range(window_size, len(prices) - step_size, step_size):
        # Define training and test windows
        train_start = i - window_size
        train_end = i
        test_start = i
        test_end = i + step_size
        
        if test_end > len(prices):
            break
        
        train_data = prices[train_start:train_end]
        test_data = prices[test_start:test_end]
        
        print(f"Window {len(windows)+1}: Train {train_start}-{train_end}, Test {test_start}-{test_end}")
        
        # Optimize strategy weights on training data
        optimized_weights = optimize_on_train_data(train_data, strategies)
        
        # Test on unseen data
        test_results = test_strategy_weights(test_data, optimized_weights, strategies)
        
        window_result = {
            "window_number": len(windows) + 1,
            "train_period": f"{train_start}-{train_end}",
            "test_period": f"{test_start}-{test_end}",
            "optimized_weights": optimized_weights,
            "train_balance": 10000,  # Starting balance for this window
            "test_equity": test_results["equity"],
            "test_return": test_results["total_return"],
            "test_sharpe": test_results["sharpe_ratio"],
            "max_drawdown": test_results["max_drawdown"],
            "win_rate": test_results["win_rate"],
            "total_trades": test_results["total_trades"]
        }
        
        results.append(window_result)
        windows.append(window_result)
    
    # Calculate overall walk-forward performance
    overall_performance = calculate_walk_forward_metrics(results)
    
    return {
        "walk_forward_results": results,
        "overall_performance": overall_performance,
        "window_size": window_size,
        "step_size": step_size,
        "total_windows": len(results),
        "strategies_tested": strategies
    }

def optimize_on_train_data(train_data, strategies):
    """Optimize strategy weights using training data only"""
    from app.services.portfolio_engine import run_portfolio
    
    best_balance = 0
    best_weights = {}
    
    # Grid search for optimal weights on training data
    weight_steps = np.arange(0, 1.1, 0.2)
    
    for w1 in weight_steps:
        for w2 in weight_steps:
            for w3 in weight_steps:
                # Normalize weights
                total_weight = w1 + w2 + w3
                if total_weight == 0:
                    continue
                
                weights = {
                    strategies[0]: w1 / total_weight,
                    strategies[1]: w2 / total_weight,
                    strategies[2]: w3 / total_weight
                }
                
                # Test on training data
                train_result = run_portfolio(train_data, weights, strategies)
                
                if train_result['final_balance'] > best_balance:
                    best_balance = train_result['final_balance']
                    best_weights = weights
    
    return best_weights

def test_strategy_weights(test_data, weights, strategies):
    """Test optimized weights on unseen test data"""
    from app.services.portfolio_engine import run_portfolio, calculate_portfolio_metrics
    
    # Run portfolio on test data
    test_result = run_portfolio(test_data, weights, strategies)
    
    # Calculate performance metrics
    metrics = calculate_portfolio_metrics(test_result["equity"])
    
    return {
        "equity": test_result["equity"],
        "final_balance": test_result["final_balance"],
        "total_return": metrics["total_return"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "max_drawdown": metrics["max_drawdown"],
        "win_rate": test_result.get("win_rate", 0),
        "total_trades": len(test_result.get("trades", []))
    }

def calculate_walk_forward_metrics(windows):
    """Calculate overall walk-forward performance metrics"""
    if not windows:
        return {}
    
    # Aggregate returns from all windows
    all_returns = []
    all_balances = []
    
    for window in windows:
        if window["test_equity"]:
            all_returns.extend(window["test_equity"])
            all_balances.append(window["test_equity"][-1] if window["test_equity"] else 10000)
    
    if not all_returns:
        return {}
    
    # Calculate overall metrics
    overall_return = np.mean([w["test_return"] for w in windows])
    overall_sharpe = np.mean([w["test_sharpe"] for w in windows])
    overall_drawdown = np.min([w["max_drawdown"] for w in windows])
    overall_win_rate = np.mean([w["win_rate"] for w in windows])
    
    # Calculate stability metrics
    return_stability = np.std([w["test_return"] for w in windows])
    sharpe_stability = np.std([w["test_sharpe"] for w in windows])
    
    # Success rate (positive returns)
    success_rate = len([w for w in windows if w["test_return"] > 0]) / len(windows) * 100
    
    return {
        "average_return": overall_return,
        "average_sharpe": overall_sharpe,
        "average_max_drawdown": overall_drawdown,
        "average_win_rate": overall_win_rate,
        "return_stability": return_stability,
        "sharpe_stability": sharpe_stability,
        "success_rate": success_rate,
        "total_windows": len(windows),
        "best_window": max(windows, key=lambda x: x["test_return"]) if windows else None,
        "worst_window": min(windows, key=lambda x: x["test_return"]) if windows else None
    }

def multi_asset_walk_forward(price_data, window_size=200, step_size=50):
    """
    Walk-forward validation for multi-asset portfolio
    price_data: {symbol: prices}
    """
    symbols = list(price_data.keys())
    results = []
    
    for i in range(window_size, len(list(price_data.values())[0]) - step_size, step_size):
        window_results = {}
        
        for symbol in symbols:
            symbol_prices = price_data[symbol]
            
            if i + step_size > len(symbol_prices):
                continue
            
            train_data = symbol_prices[i-window_size:i]
            test_data = symbol_prices[i:i+step_size]
            
            # Optimize single asset strategy
            optimized_weights = optimize_on_train_data(train_data, ['sma', 'rsi'])
            test_results = test_strategy_weights(test_data, optimized_weights, ['sma', 'rsi'])
            
            window_results[symbol] = {
                "test_return": test_results["total_return"],
                "test_sharpe": test_results["sharpe_ratio"],
                "max_drawdown": test_results["max_drawdown"]
            }
        
        # Calculate portfolio performance for this window
        portfolio_return = np.mean([r["test_return"] for r in window_results.values()])
        portfolio_sharpe = np.mean([r["test_sharpe"] for r in window_results.values()])
        portfolio_drawdown = np.mean([r["max_drawdown"] for r in window_results.values()])
        
        results.append({
            "window_number": len(results) + 1,
            "period": f"{i}-{i+step_size}",
            "individual_results": window_results,
            "portfolio_return": portfolio_return,
            "portfolio_sharpe": portfolio_sharpe,
            "portfolio_drawdown": portfolio_drawdown
        })
    
    return {
        "multi_asset_results": results,
        "symbols": symbols,
        "overall_performance": calculate_multi_asset_metrics(results)
    }

def calculate_multi_asset_metrics(results):
    """Calculate metrics for multi-asset walk-forward"""
    if not results:
        return {}
    
    portfolio_returns = [r["portfolio_return"] for r in results]
    portfolio_sharpes = [r["portfolio_sharpe"] for r in results]
    portfolio_drawdowns = [r["portfolio_drawdown"] for r in results]
    
    return {
        "average_portfolio_return": np.mean(portfolio_returns),
        "average_portfolio_sharpe": np.mean(portfolio_sharpes),
        "average_portfolio_drawdown": np.mean(portfolio_drawdowns),
        "return_stability": np.std(portfolio_returns),
        "sharpe_stability": np.std(portfolio_sharpes),
        "best_window": max(results, key=lambda x: x["portfolio_return"]) if results else None,
        "worst_window": min(results, key=lambda x: x["portfolio_return"]) if results else None
    }

def ai_walk_forward(prices, window_size=200, step_size=50):
    """
    Walk-forward validation with AI model retraining
    """
    results = []
    
    for i in range(window_size, len(prices) - step_size, step_size):
        train_data = prices[i-window_size:i]
        test_data = prices[i:i+step_size]
        
        # Retrain AI model on training data
        ai_model = train_ai_model(train_data)
        
        # Test on unseen data
        test_results = test_ai_model(ai_model, test_data)
        
        results.append({
            "window": len(results) + 1,
            "train_size": len(train_data),
            "test_size": len(test_data),
            "ai_performance": test_results,
            "model_accuracy": test_results.get("accuracy", 0)
        })
    
    return {
        "ai_walk_forward": results,
        "overall_ai_performance": calculate_ai_metrics(results)
    }

def train_ai_model(train_data):
    """Train AI model on training data"""
    # Mock AI training - in real implementation, 
    # this would train the LSTM model
    return {
        "model_type": "LSTM",
        "training_data_size": len(train_data),
        "features": ["price", "volume", "indicators"],
        "accuracy": 0.75  # Mock accuracy
    }

def test_ai_model(model, test_data):
    """Test AI model on unseen data"""
    # Mock AI testing
    predictions = np.random.choice(["BUY", "SELL", "HOLD"], len(test_data))
    actual_signals = np.random.choice(["BUY", "SELL", "HOLD"], len(test_data))
    
    accuracy = np.mean(predictions == actual_signals)
    
    return {
        "predictions": predictions.tolist(),
        "actual": actual_signals.tolist(),
        "accuracy": accuracy,
        "test_size": len(test_data)
    }

def calculate_ai_metrics(results):
    """Calculate AI model performance metrics"""
    if not results:
        return {}
    
    accuracies = [r["ai_performance"]["accuracy"] for r in results]
    
    return {
        "average_accuracy": np.mean(accuracies),
        "accuracy_stability": np.std(accuracies),
        "best_accuracy": np.max(accuracies),
        "worst_accuracy": np.min(accuracies),
        "total_windows": len(results)
    }

def rolling_window_analysis(prices, window_sizes=[100, 200, 300]):
    """
    Test different window sizes to find optimal parameters
    """
    results = {}
    
    for window_size in window_sizes:
        wf_result = walk_forward_validation(prices, window_size, 50)
        results[f"window_{window_size}"] = {
            "window_size": window_size,
            "average_return": wf_result["overall_performance"]["average_return"],
            "average_sharpe": wf_result["overall_performance"]["average_sharpe"],
            "success_rate": wf_result["overall_performance"]["success_rate"]
        }
    
    # Find best window size
    best_window = max(results.values(), key=lambda x: x["average_return"])
    
    return {
        "rolling_analysis": results,
        "best_window_size": best_window["window_size"],
        "best_performance": best_window,
        "all_window_sizes": window_sizes
    }
