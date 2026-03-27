"""
Backtest Metrics Module - Robust & Safe
"""

import pandas as pd
import numpy as np
from typing import Dict


class MetricsCalculator:

    @staticmethod
    def calculate_all_metrics(results: Dict) -> Dict:

        trades = results.get("trades", [])
        equity_curve = results.get("equity_curve", [])

        # ============================
        # SAFE BASE METRICS
        # ============================

        metrics = {
            "total_return_pct": results.get("total_return_pct", 0),
            "max_drawdown_pct": results.get("max_drawdown_pct", 0),
            "sharpe_ratio": results.get("sharpe_ratio", 0),
            "total_trades": len(trades),
            "win_rate": results.get("win_rate", 0),
        }

        # ============================
        # TRADE METRICS
        # ============================

        if trades:

            wins = [t for t in trades if t.pnl > 0]
            losses = [t for t in trades if t.pnl <= 0]

            metrics["winning_trades"] = len(wins)
            metrics["losing_trades"] = len(losses)

            metrics["avg_trade_pnl"] = np.mean([t.pnl for t in trades])

            gross_profit = sum(t.pnl for t in wins)
            gross_loss = abs(sum(t.pnl for t in losses))

            metrics["profit_factor"] = (
                gross_profit / gross_loss if gross_loss > 0 else float("inf")
            )

            avg_win = np.mean([t.pnl for t in wins]) if wins else 0
            avg_loss = np.mean([t.pnl for t in losses]) if losses else 0

            metrics["avg_win"] = avg_win
            metrics["avg_loss"] = avg_loss

            metrics["win_loss_ratio"] = (
                abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")
            )

        # ============================
        # EQUITY METRICS
        # ============================

        if equity_curve:

            equity = pd.Series(equity_curve)
            returns = equity.pct_change().dropna()

            if len(returns) > 0:

                metrics["volatility"] = returns.std() * np.sqrt(252 * 24 * 60)

                if metrics["max_drawdown_pct"] != 0:
                    metrics["calmar_ratio"] = (
                        metrics["total_return_pct"] /
                        abs(metrics["max_drawdown_pct"])
                    )
                else:
                    metrics["calmar_ratio"] = float("inf")

                downside = returns[returns < 0]

                if len(downside) > 0 and downside.std() != 0:
                    metrics["sortino_ratio"] = (
                        returns.mean() / downside.std()
                    ) * np.sqrt(252 * 24 * 60)

        return metrics

    # =========================================
    # PRINT REPORT
    # =========================================

    @staticmethod
    def print_report(results: Dict):

        metrics = MetricsCalculator.calculate_all_metrics(results)

        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE REPORT")
        print("=" * 60)

        print("\nCapital:")
        print(f"Initial: ${results.get('initial_capital', 0):,.2f}")
        print(f"Final:   ${results.get('final_capital', 0):,.2f}")
        print(f"Return:  {metrics['total_return_pct']:.2f}%")

        print("\nRisk:")
        print(f"Max DD:  {metrics['max_drawdown_pct']:.2f}%")
        print(f"Sharpe:  {metrics['sharpe_ratio']:.4f}")

        if "sortino_ratio" in metrics:
            print(f"Sortino: {metrics['sortino_ratio']:.4f}")

        print("\nTrades:")
        print(f"Total:   {metrics['total_trades']}")
        print(f"WinRate: {metrics['win_rate']:.2f}%")

        if "profit_factor" in metrics:
            print(f"PF:      {metrics['profit_factor']:.2f}")

        print("=" * 60)

        return metrics


# =========================================
# HELPERS
# =========================================

def calculate_metrics(results: Dict) -> Dict:
    return MetricsCalculator.calculate_all_metrics(results)


def print_metrics(results: Dict):
    return MetricsCalculator.print_report(results)