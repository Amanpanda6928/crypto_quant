"""Quick test for hedge fund backtesting module"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'c:\\Users\\omama\\criptoviews')

from backend.backtesting.hedge_fund_strategy import (
    HedgeFundBacktester, RiskParameters, ExecutionConfig, generate_sample_data
)

print("Testing Hedge Fund Backtesting Module")
print("=" * 50)

# Quick test with smaller dataset
print('\nGenerating sample data...')
df = generate_sample_data(days=100)
print(f'Data shape: {df.shape}')
print(f'Date range: {df.index[0]} to {df.index[-1]}')

backtester = HedgeFundBacktester(initial_capital=100000)
print('\nRunning Multi-Factor Momentum strategy...')
result = backtester.run_backtest(df, backtester.multi_factor_momentum)

print(f'\nBacktest Results:')
print(f'Total Return: {result["total_return_pct"]:.2f}%')
print(f'Sharpe Ratio: {result["sharpe_ratio"]:.3f}')
print(f'Sortino Ratio: {result["sortino_ratio"]:.3f}')
print(f'Max Drawdown: {result["max_drawdown_pct"]:.2f}%')
print(f'Total Trades: {result["total_trades"]}')
print(f'Win Rate: {result["win_rate_pct"]:.1f}%')
print(f'Final Capital: ${result["final_capital"]:,.2f}')

print('\n' + '=' * 50)
print('Test completed successfully!')
