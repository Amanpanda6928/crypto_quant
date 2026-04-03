# Portfolio Optimization Engine
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.strategies import get_strategy_signals, calculate_strategy_performance

def run_portfolio(prices, weights=None, strategies=None):
    """Run portfolio backtest with multiple strategies"""
    if strategies is None:
        strategies = ['sma', 'ema', 'rsi', 'bollinger', 'macd', 'stochastic']
    
    if weights is None:
        weights = {strategy: 1.0/len(strategies) for strategy in strategies}
    
    # Get signals from all strategies
    all_signals = get_strategy_signals(prices)
    
    # Initialize portfolio
    balance = 10000
    equity = []
    trades = []
    
    for i in range(len(prices[strategies[0]])):  # Use length of first strategy
        portfolio_score = 0
        position = None
        current_price = prices[i]
        
        # Calculate portfolio score from all strategies
        for strategy in strategies:
            if strategy in all_signals and i < len(all_signals[strategy]):
                signal = all_signals[strategy][i]
                weight = weights.get(strategy, 0)
                
                if signal == "BUY":
                    portfolio_score += weight * 1
                elif signal == "SELL":
                    portfolio_score += weight * -1
                # HOLD contributes 0
        
        # Trading logic based on portfolio score
        if portfolio_score > 0.5 and position is None:
            position = {
                "entry": current_price,
                "quantity": 0.01,
                "time": i,
                "type": "LONG"
            }
        elif portfolio_score < -0.5 and position is not None:
            pnl = (current_price - position["entry"]) * position["quantity"]
            balance += pnl
            trades.append({
                "entry": position["entry"],
                "exit": current_price,
                "pnl": pnl,
                "time": position["time"],
                "exit_time": i,
                "type": position["type"]
            })
            position = None
        
        equity.append(balance)
    
    return {
        "equity": equity,
        "final_balance": balance,
        "trades": trades,
        "weights": weights,
        "strategies": strategies
    }

def optimize_weights(prices, strategies=None):
    """Optimize portfolio weights using grid search"""
    if strategies is None:
        strategies = ['sma', 'ema', 'rsi', 'bollinger', 'macd']
    
    best_balance = 0
    best_weights = None
    optimization_results = []
    
    # Grid search for optimal weights
    step_size = 0.2
    weight_range = np.arange(0, 1.1, step_size)
    
    for w1 in weight_range:
        for w2 in weight_range:
            for w3 in weight_range:
                for w4 in weight_range:
                    for w5 in weight_range:
                        # Normalize weights
                        total_weight = w1 + w2 + w3 + w4 + w5
                        if total_weight == 0:
                            continue
                        
                        weights = {
                            'sma': w1 / total_weight,
                            'ema': w2 / total_weight,
                            'rsi': w3 / total_weight,
                            'bollinger': w4 / total_weight,
                            'macd': w5 / total_weight
                        }
                        
                        # Run portfolio with these weights
                        result = run_portfolio(prices, weights, strategies)
                        
                        optimization_results.append({
                            'weights': weights,
                            'final_balance': result['final_balance'],
                            'total_return': (result['final_balance'] - 10000) / 10000 * 100
                        })
                        
                        if result['final_balance'] > best_balance:
                            best_balance = result['final_balance']
                            best_weights = weights
    
    # Sort results by performance
    optimization_results.sort(key=lambda x: x['final_balance'], reverse=True)
    
    return {
        "best_balance": best_balance,
        "best_weights": best_weights,
        "top_combinations": optimization_results[:10],  # Top 10 combinations
        "total_combinations_tested": len(optimization_results)
    }

def monte_carlo_optimization(prices, strategies=None, iterations=1000):
    """Monte Carlo optimization for portfolio weights"""
    if strategies is None:
        strategies = ['sma', 'ema', 'rsi', 'bollinger', 'macd']
    
    best_balance = 0
    best_weights = None
    results = []
    
    for iteration in range(iterations):
        # Generate random weights
        random_weights = np.random.random(len(strategies))
        random_weights = random_weights / np.sum(random_weights)
        
        weights = {strategy: weight for strategy, weight in zip(strategies, random_weights)}
        
        # Run portfolio
        result = run_portfolio(prices, weights, strategies)
        
        results.append({
            'iteration': iteration + 1,
            'weights': weights,
            'final_balance': result['final_balance'],
            'total_return': (result['final_balance'] - 10000) / 10000 * 100
        })
        
        if result['final_balance'] > best_balance:
            best_balance = result['final_balance']
            best_weights = weights
    
    return {
        "best_balance": best_balance,
        "best_weights": best_weights,
        "monte_carlo_results": results,
        "iterations": iterations
    }

def calculate_portfolio_metrics(equity_curve, initial_balance=10000):
    """Calculate comprehensive portfolio metrics"""
    if not equity_curve:
        return {}
    
    final_balance = equity_curve[-1]
    total_return = (final_balance - initial_balance) / initial_balance * 100
    
    # Calculate daily returns
    returns = np.diff(equity_curve) / equity_curve[:-1]
    returns = returns[~np.isnan(returns)]
    
    # Sharpe ratio (annualized)
    if len(returns) > 1 and np.std(returns) > 0:
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
    else:
        sharpe_ratio = 0
    
    # Maximum drawdown
    peak = equity_curve[0]
    drawdowns = []
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        drawdowns.append(drawdown)
    
    max_drawdown = min(drawdowns) if drawdowns else 0
    
    # Volatility (annualized)
    volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 1 else 0
    
    # Sortino ratio (downside deviation)
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 1:
        downside_deviation = np.std(downside_returns)
        sortino_ratio = np.mean(returns) / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
    else:
        sortino_ratio = 0
    
    # Calmar ratio (return / max drawdown)
    calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "calmar_ratio": calmar_ratio,
        "max_drawdown": max_drawdown,
        "volatility": volatility,
        "final_balance": final_balance
    }

def analyze_strategy_contributions(prices, weights, strategies=None):
    """Analyze individual strategy contributions"""
    if strategies is None:
        strategies = ['sma', 'ema', 'rsi', 'bollinger', 'macd']
    
    contributions = {}
    all_signals = get_strategy_signals(prices)
    
    for strategy in strategies:
        if strategy in all_signals:
            performance = calculate_strategy_performance(all_signals[strategy], prices)
            weight = weights.get(strategy, 0)
            
            contributions[strategy] = {
                "weight": weight,
                "individual_return": (performance['final_balance'] - 10000) / 10000 * 100,
                "weighted_return": (performance['final_balance'] - 10000) / 10000 * 100 * weight,
                "win_rate": performance['win_rate'],
                "total_trades": performance['total_trades']
            }
    
    return contributions

def get_portfolio_recommendations(weights, performance_metrics):
    """Get portfolio optimization recommendations"""
    recommendations = []
    
    # Analyze weight distribution
    total_weight = sum(weights.values())
    weight_distribution = {k: v/total_weight for k, v in weights.items()}
    
    # Check for over-concentration
    max_weight = max(weight_distribution.values())
    if max_weight > 0.5:
        recommendations.append({
            "type": "risk",
            "message": f"Portfolio is over-concentrated ({max_weight*100:.1f}% in one strategy)",
            "suggestion": "Consider diversifying across more strategies"
        })
    
    # Check for under-performance
    if performance_metrics.get('sharpe_ratio', 0) < 0.5:
        recommendations.append({
            "type": "performance",
            "message": "Low risk-adjusted returns detected",
            "suggestion": "Consider optimizing strategy weights or adding new strategies"
        })
    
    # Check for high volatility
    if performance_metrics.get('volatility', 0) > 30:
        recommendations.append({
            "type": "volatility",
            "message": "High portfolio volatility detected",
            "suggestion": "Consider adding low-volatility strategies or reducing position sizes"
        })
    
    return recommendations

def generate_portfolio_report(prices, weights, strategies=None):
    """Generate comprehensive portfolio analysis report"""
    # Run portfolio
    portfolio_result = run_portfolio(prices, weights, strategies)
    
    # Calculate metrics
    metrics = calculate_portfolio_metrics(portfolio_result['equity'])
    
    # Analyze contributions
    contributions = analyze_strategy_contributions(prices, weights, strategies)
    
    # Get recommendations
    recommendations = get_portfolio_recommendations(weights, metrics)
    
    return {
        "portfolio_summary": {
            "initial_balance": 10000,
            "final_balance": portfolio_result['final_balance'],
            "total_return": metrics['total_return'],
            "sharpe_ratio": metrics['sharpe_ratio'],
            "max_drawdown": metrics['max_drawdown'],
            "volatility": metrics['volatility']
        },
        "strategy_weights": weights,
        "strategy_contributions": contributions,
        "recommendations": recommendations,
        "performance_metrics": metrics
    }
