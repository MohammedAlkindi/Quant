"""Retail-rule strategies for the cost study, as daily target weights in {0, 1}.

Specifications, grids, and sources are pre-registered in
docs/cost-study/protocol.md; this module implements them verbatim. Every
weight is decided on bar t's close from data through bar t only - the engine
adds the one-bar execution delay. Warm-up bars emit 0.0.

Stateful rules (rsi2, bollinger_mr, donchian) run an explicit position state
machine: an entry condition applies only when flat, an exit condition only
when long. A plain loop over the bars keeps that logic auditable; at ~8k
daily bars speed is irrelevant.
"""

import numpy as np
import pandas as pd

WINTER_MONTHS = frozenset({11, 12, 1, 2, 3, 4})


def _state_machine(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    """Long after an entry signal, flat after an exit signal, hold otherwise."""
    entries = entry.to_numpy(dtype=bool)
    exits = exit_.to_numpy(dtype=bool)
    weights = np.zeros(len(entries))
    long = False
    for i in range(len(entries)):
        if not long and entries[i]:
            long = True
        elif long and exits[i]:
            long = False
        weights[i] = 1.0 if long else 0.0
    return pd.Series(weights, index=entry.index)


def _month_end_mask(index: pd.DatetimeIndex) -> pd.Series:
    """True on the last trading day of each calendar month in the index."""
    dates = index.to_series()
    return dates.groupby(index.to_period('M')).transform('max') == dates


def _hold_monthly(index: pd.DatetimeIndex, month_end_signal: pd.Series) -> pd.Series:
    """Spread month-end decisions across daily bars: the weight changes on the
    month-end bar itself (the engine fills it at the next open) and holds
    until the next month-end decision."""
    daily = pd.Series(np.nan, index=index)
    daily.loc[month_end_signal.index] = month_end_signal.astype(float)
    return daily.ffill().fillna(0.0)


def wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + rs)
    # All-gain windows have avg_loss == 0: RSI is 100 by convention.
    return rsi.where(avg_loss > 0, 100.0).where(avg_gain.notna() & avg_loss.notna())


def faber_tma(close: pd.Series, months: int) -> pd.Series:
    month_end = close[_month_end_mask(close.index)]
    sma = month_end.rolling(months, min_periods=months).mean()
    signal = (month_end > sma) & sma.notna()
    return _hold_monthly(close.index, signal)


def tsmom(close: pd.Series, months: int) -> pd.Series:
    month_end = close[_month_end_mask(close.index)]
    trailing = month_end / month_end.shift(months) - 1.0
    signal = (trailing > 0) & trailing.notna()
    return _hold_monthly(close.index, signal)


def rsi2(close: pd.Series, threshold: float) -> pd.Series:
    rsi = wilder_rsi(close, 2)
    sma200 = close.rolling(200, min_periods=200).mean()
    sma5 = close.rolling(5, min_periods=5).mean()
    entry = (rsi < threshold) & (close > sma200) & rsi.notna() & sma200.notna()
    exit_ = (close > sma5) & sma5.notna()
    return _state_machine(entry, exit_)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    macd_line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    # EMAs are defined from the first bar, but early values reflect a partial
    # window; suppress the first `slow` bars as warm-up.
    long = (macd_line > signal_line).to_numpy()
    long[:slow] = False
    return pd.Series(long.astype(float), index=close.index)


def bollinger_mr(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    mid = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=0)
    lower = mid - num_std * std
    entry = (close < lower) & lower.notna()
    exit_ = (close >= mid) & mid.notna()
    return _state_machine(entry, exit_)


def donchian(prices: pd.DataFrame, entry_window: int, exit_window: int) -> pd.Series:
    """Close above the prior entry_window-bar high enters; close below the
    prior exit_window-bar low exits. shift(1) keeps today's bar out of both
    channels."""
    upper = prices['high'].rolling(entry_window, min_periods=entry_window).max().shift(1)
    lower = prices['low'].rolling(exit_window, min_periods=exit_window).min().shift(1)
    close = prices['close']
    entry = (close > upper) & upper.notna()
    exit_ = (close < lower) & lower.notna()
    return _state_machine(entry, exit_)


def halloween(close: pd.Series) -> pd.Series:
    winter = close.index.month.isin(sorted(WINTER_MONTHS))
    return pd.Series(winter.astype(float), index=close.index)
