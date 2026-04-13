#!/usr/bin/env python3
import sys
from datetime import datetime
sys.path.insert(0, 'backend')

from app.services.live_prediction_service import get_live_service, COINS, TIMEFRAMES

service = get_live_service()

# Run backtests for each coin (this populates the cache)
print('Running hedge fund backtests for all coins...')
for coin in COINS:
    for tf in ['1h', '4h', '1d']:  # Run full backtests on key timeframes
        service.run_backtest_for_coin(coin['symbol'], tf, days=14)
print('Backtests complete.')

# Generate predictions
predictions = service.generate_all_predictions()

# Timing info
generated_at = service.last_update
next_update = service.next_update
generated_str = generated_at.strftime('%Y-%m-%d %H:%M:%S') if generated_at else 'N/A'
next_update_str = next_update.strftime('%H:%M:%S') if next_update else 'N/A'

print('='*80)
print('LIVE PREDICTIONS WITH HEDGE FUND BACKTESTING METRICS')
print('10 Coins x 5 Timeframes = 50 Predictions with Strategy Backtests')
print(f'Generated: {generated_str} | Next Update: {next_update_str} (15 min interval)')
print('='*80)

for tf in TIMEFRAMES:
    print(f'\n{tf}:')
    print('-'*80)
    print(f"  {'COIN':5} {'SIGNAL':6} {'CONF':5} {'CURRENT':>12} {'PREDICTED':>12} {'STRATEGY':18} {'SHARPE':>6} {'WIN%':>5} {'RETURN':>7}")
    print('-'*80)
    for coin in COINS:
        preds = service.get_predictions_for_coin(coin['symbol'])
        if tf in preds:
            p = preds[tf]
            emoji = 'BUY' if p['signal'] == 'BUY' else 'SELL' if p['signal'] == 'SELL' else 'HOLD'
            # Get backtest metrics from cache
            metrics = service.run_backtest_for_coin(coin['symbol'], tf, days=14)
            strategy = metrics.get('strategy', 'N/A')[:16]
            sharpe = metrics.get('sharpe_ratio', 0)
            win_rate = metrics.get('win_rate_pct', 0)
            ret = metrics.get('total_return_pct', 0)
            print(f"  {coin['symbol']:5} {emoji:6} {int(p['confidence']):4}% ${p['current_price']:>10,.2f} ${p['predicted_price']:>10,.2f} {strategy:18} {sharpe:>6.2f} {win_rate:>5.1f} {ret:>7.1f}%")

flat_preds = [p for coin in COINS for tf in TIMEFRAMES 
              for p in [service.get_predictions_for_coin(coin['symbol']).get(tf)] if p]
buy = sum(1 for p in flat_preds if p['signal'] == 'BUY')
sell = sum(1 for p in flat_preds if p['signal'] == 'SELL')
hold = sum(1 for p in flat_preds if p['signal'] == 'HOLD')

# Calculate time since generation
if generated_at:
    age_minutes = int((datetime.now() - generated_at).total_seconds() / 60)
    age_str = f'{age_minutes} min ago'
else:
    age_str = 'N/A'

print('\n' + '='*80)
print(f'SUMMARY: BUY={buy} SELL={sell} HOLD={hold} | Total={len(flat_preds)} predictions')
print(f'Timing: Generated {age_str} | Next Update: {next_update_str} | Interval: 15 min')
print('\nBACKTEST METRICS LEGEND:')
print('  STRATEGY = Best performing hedge fund strategy for this coin/timeframe')
print('  SHARPE   = Risk-adjusted return ratio (higher is better)')
print('  WIN%     = Historical win rate from backtested trades')
print('  RETURN   = Backtested total return percentage')
print('='*80)
