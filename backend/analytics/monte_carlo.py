import numpy as np

def monte_carlo(pnl_list, sims=200):
    results = []

    for _ in range(sims):
        equity = 10000
        curve = []

        for _ in range(50):
            equity += np.random.choice(pnl_list)
            curve.append(equity)

        results.append(curve)

    return results
