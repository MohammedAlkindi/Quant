"""Unit tests for the cost-study strategy rules.

Fixture values are deliberately irregular (no round numbers, no tidy
arithmetic relations) so a formula error cannot cancel out by coincidence.
"""

import numpy as np
import pandas as pd
import pytest

from quant.study_strategies import (
    _state_machine,
    bollinger_mr,
    donchian,
    faber_tma,
    halloween,
    macd,
    rsi2,
    tsmom,
    wilder_rsi,
)


def _walk(n: int, seed: int = 20260814, start: float = 83.47) -> pd.Series:
    rng = np.random.default_rng(seed)
    steps = rng.normal(0.0003, 0.011, n)
    prices = start * np.exp(np.cumsum(steps))
    return pd.Series(prices, index=pd.bdate_range('2001-03-07', periods=n))


def test_state_machine_holds_between_signals():
    idx = pd.bdate_range('2010-05-11', periods=6)
    entry = pd.Series([False, True, False, False, False, False], index=idx)
    exit_ = pd.Series([False, False, False, True, False, False], index=idx)
    out = _state_machine(entry, exit_)
    assert out.tolist() == [0.0, 1.0, 1.0, 0.0, 0.0, 0.0]


def test_state_machine_entry_wins_when_flat_even_if_exit_fires():
    idx = pd.bdate_range('2010-05-11', periods=3)
    entry = pd.Series([True, False, False], index=idx)
    exit_ = pd.Series([True, True, False], index=idx)
    out = _state_machine(entry, exit_)
    # Flat + both signals: the exit applies only to an open position, so the
    # entry takes effect; the persisting exit then closes it next bar.
    assert out.tolist() == [1.0, 0.0, 0.0]


def test_wilder_rsi_extremes_and_warmup():
    up = pd.Series([31.7, 32.9, 34.6, 35.2, 36.9, 38.1])
    down = pd.Series([38.1, 36.9, 35.2, 34.6, 32.9, 31.7])
    rsi_up = wilder_rsi(up, 2)
    rsi_down = wilder_rsi(down, 2)
    assert rsi_up.iloc[:2].isna().all()  # diff + min_periods warm-up
    assert (rsi_up.dropna() == 100.0).all()
    assert (rsi_down.dropna() == 0.0).all()
    mixed = wilder_rsi(_walk(300), 2).dropna()
    assert ((mixed >= 0.0) & (mixed <= 100.0)).all()


def test_faber_holds_month_end_decision_through_next_month():
    close = _walk(190)  # ~9 calendar months of business days
    weights = faber_tma(close, 3)
    month_ends = close.index.to_series().groupby(close.index.to_period('M')).max()
    # Weight may only change on the bar after a month-end decision bar or on
    # the month-end bar itself; verify: within a month, all bars after the
    # first carry the value decided at the previous month-end.
    changes = weights[weights.diff().fillna(0.0) != 0.0].index
    allowed = set(month_ends)
    for ts in changes:
        assert ts in allowed, f'weight changed off month-end at {ts}'
    # Spot-check the sign rule at the 5th month-end (3-month SMA warm-up over).
    me_close = close[close.index.isin(month_ends)]
    sma3 = me_close.rolling(3).mean()
    t = me_close.index[4]
    assert weights.loc[t] == float(me_close.loc[t] > sma3.loc[t])


def test_tsmom_sign_rule_at_month_end():
    close = _walk(400)
    weights = tsmom(close, 6)
    month_ends = close.index.to_series().groupby(close.index.to_period('M')).max()
    me_close = close[close.index.isin(month_ends)]
    trailing = me_close / me_close.shift(6) - 1.0
    for t in me_close.index[8:12]:
        assert weights.loc[t] == float(trailing.loc[t] > 0)


def test_donchian_reads_only_prior_bars():
    n = 25
    rng = np.random.default_rng(7)
    base = 50.0 + rng.normal(0.0, 0.23, n).cumsum()
    high = base + 0.31
    low = base - 0.29
    close = base.copy()
    # Bar 22: close pops above the prior 20-bar high, but the bar's own high
    # is higher still. Including today's high in the channel (a look-ahead
    # bug) would suppress the entry.
    prior_high = high[2:22].max()
    close[22] = prior_high + 0.57
    high[22] = close[22] + 0.83
    low[22] = close[22] - 0.11
    prices = pd.DataFrame(
        {'open': close, 'high': high, 'low': low, 'close': close},
        index=pd.bdate_range('2015-09-02', periods=n),
    )
    weights = donchian(prices, entry_window=20, exit_window=10)
    assert weights.iloc[22] == 1.0, 'entry must compare against the PRIOR 20-bar high'
    assert (weights.iloc[:22] == 0.0).all()


def test_bollinger_enters_below_lower_band_exits_at_mid():
    close = _walk(260)
    weights = bollinger_mr(close, 20, 2.0)
    mid = close.rolling(20).mean()
    std = close.rolling(20).std(ddof=0)
    lower = mid - 2.0 * std
    entered = weights[(weights.diff() == 1.0)].index
    for t in entered:
        assert close.loc[t] < lower.loc[t]
    exited = weights[(weights.diff() == -1.0)].index
    for t in exited:
        assert close.loc[t] >= mid.loc[t]


def test_macd_warmup_is_flat_and_matches_line_cross():
    close = _walk(120)
    weights = macd(close)
    assert (weights.iloc[:26] == 0.0).all()
    macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    expected = (macd_line > signal_line).iloc[40:60].astype(float)
    assert weights.iloc[40:60].tolist() == expected.tolist()


def test_halloween_by_calendar_month():
    idx = pd.bdate_range('2018-01-03', '2019-12-30')
    weights = halloween(pd.Series(61.83, index=idx))
    assert (weights[idx.month.isin([11, 12, 1, 2, 3, 4])] == 1.0).all()
    assert (weights[idx.month.isin([5, 6, 7, 8, 9, 10])] == 0.0).all()


@pytest.mark.parametrize(
    'builder',
    [
        lambda p: faber_tma(p['close'], 10),
        lambda p: tsmom(p['close'], 12),
        lambda p: rsi2(p['close'], 10.0),
        lambda p: macd(p['close']),
        lambda p: bollinger_mr(p['close']),
        lambda p: donchian(p, 20, 10),
        lambda p: halloween(p['close']),
    ],
)
def test_weights_are_binary_nan_free_and_aligned(builder):
    close = _walk(700)
    prices = pd.DataFrame(
        {'open': close.shift(1).fillna(close.iloc[0]), 'high': close * 1.004, 'low': close * 0.9961, 'close': close},
        index=close.index,
    )
    weights = builder(prices)
    assert weights.index.equals(prices.index)
    assert not weights.isna().any()
    assert set(weights.unique()) <= {0.0, 1.0}
