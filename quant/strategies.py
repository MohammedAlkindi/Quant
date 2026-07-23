"""Baseline strategies expressed as target-weight series in [0, 1].

Weights are decided on each bar's close; the engine applies them with a
one-bar execution delay, so no strategy here can act on information from
the bar it trades on.
"""

import pandas as pd


def buy_and_hold(close: pd.Series) -> pd.Series:
    return pd.Series(1.0, index=close.index)


def ma_crossover(close: pd.Series, fast: int, slow: int) -> pd.Series:
    if fast >= slow:
        raise ValueError(f'fast window ({fast}) must be smaller than slow window ({slow})')
    fast_ma = close.rolling(fast, min_periods=fast).mean()
    slow_ma = close.rolling(slow, min_periods=slow).mean()
    long = (fast_ma > slow_ma) & slow_ma.notna()
    return long.astype(float)
