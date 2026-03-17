import numpy as np


def backtest_actions(prices: np.ndarray, actions: list[str]) -> dict:
    equity = [1.0]
    position = 0
    for i in range(1, min(len(prices), len(actions) + 1)):
        if actions[i - 1] == 'buy':
            position = 1
        elif actions[i - 1] == 'sell':
            position = -1
        ret = ((prices[i] - prices[i - 1]) / max(prices[i - 1], 1e-6)) * position
        equity.append(equity[-1] * (1 + ret))
    arr = np.array(equity)
    return {'ending_equity': float(arr[-1]), 'max_drawdown': float((arr / np.maximum.accumulate(arr) - 1).min())}
