import numpy as np

def optimize(pnl_list):
    if len(pnl_list) < 5:
        return {}

    arr = np.array(pnl_list)

    return {
        "best_trade": float(arr.max()),
        "worst_trade": float(arr.min()),
        "avg_trade": float(arr.mean()),
        "volatility": float(arr.std())
    }
