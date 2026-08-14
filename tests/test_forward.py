import inspect

import numpy as np
import pandas as pd
import pytest

import quant.forward
from quant.backtest import CostModel
from quant.forward import FROZEN_FAST, FROZEN_SLOW, evaluate_forward, splice

FREE = CostModel(commission_bps=0, half_spread_bps=0, slippage_bps=0)


def rising_prices(periods=300, start='2024-01-01'):
    idx = pd.bdate_range(start, periods=periods)
    close = np.linspace(100.0, 200.0, periods)
    return pd.DataFrame(
        {'open': close - 0.05, 'high': close + 0.5, 'low': close - 0.5, 'close': close, 'volume': 1e6},
        index=idx,
    )


def overlapping_tail(base, n_overlap, n_new, close_shift=0.0):
    idx = pd.bdate_range(base.index[-n_overlap], periods=n_overlap + n_new)
    close = np.concatenate([base['close'].iloc[-n_overlap:].to_numpy() + close_shift, np.linspace(300.0, 310.0, n_new)])
    return pd.DataFrame(
        {'open': close - 0.05, 'high': close + 0.5, 'low': close - 0.5, 'close': close, 'volume': 1e6},
        index=idx,
    )


def test_splice_appends_only_new_bars_and_keeps_base_rows_in_overlap():
    base = rising_prices(30)
    tail = overlapping_tail(base, n_overlap=15, n_new=5, close_shift=0.004)  # within tolerance
    spliced = splice(base, tail)
    assert len(spliced) == 35
    assert spliced.index[:30].equals(base.index)
    overlap_date = base.index[-1]
    assert spliced.loc[overlap_date, 'close'] == base.loc[overlap_date, 'close']  # base wins in overlap
    assert spliced['close'].iloc[30:].tolist() == tail['close'].iloc[15:].tolist()


def test_splice_rejects_thin_overlap():
    base = rising_prices(30)
    tail = overlapping_tail(base, n_overlap=5, n_new=5)
    with pytest.raises(ValueError, match='overlapping bars'):
        splice(base, tail)


def test_splice_rejects_overlap_that_disagrees_beyond_tolerance():
    base = rising_prices(30)
    tail = overlapping_tail(base, n_overlap=15, n_new=5, close_shift=0.01)
    with pytest.raises(ValueError, match='seam'):
        splice(base, tail)


def test_splice_rejects_tail_without_new_bars():
    base = rising_prices(30)
    tail = overlapping_tail(base, n_overlap=15, n_new=5).iloc[:15]
    with pytest.raises(ValueError, match='adds no bars'):
        splice(base, tail)


def test_forward_parameters_are_frozen_and_never_reselected():
    # The frozen pair is the one the committed backtest picked in-sample on
    # 1993-2019; changing it, or reintroducing grid selection over data that
    # includes the forward window, must be a loud and deliberate act.
    assert (FROZEN_FAST, FROZEN_SLOW) == (10, 200)
    assert 'select_ma_params' not in inspect.getsource(quant.forward)
    prices = rising_prices()
    report = evaluate_forward(prices, costs=FREE, forward_start=prices.index[280])
    assert (report['meta']['fast'], report['meta']['slow']) == (FROZEN_FAST, FROZEN_SLOW)


def test_evaluate_forward_warms_up_from_pre_window_history():
    # Monotone rise: MA state is long across the boundary, so both strategies
    # hold from the first forward decision and enter at the second forward
    # bar's open -- the same treatment the committed backtest gives its own
    # out-of-sample boundary.
    prices = rising_prices()
    forward_start = prices.index[280]
    report = evaluate_forward(prices, costs=FREE, forward_start=forward_start)
    forward_index = prices.index[prices.index >= forward_start]
    for name in ('buy_and_hold', 'ma_cross'):
        trades = report[name]['trades']
        assert len(trades) == 1
        assert trades['date'].iloc[0] == forward_index[1]
    meta = report['meta']
    assert meta['base_end'] == prices.index[279]
    assert meta['forward_range'] == (forward_index[0], forward_index[-1])
    assert meta['n_bars'] == len(forward_index)


def test_evaluate_forward_rejects_short_windows():
    prices = rising_prices()
    with pytest.raises(ValueError, match='at least 2 bars'):
        evaluate_forward(prices, costs=FREE, forward_start=prices.index[-1])
    with pytest.raises(ValueError, match='warm-up'):
        evaluate_forward(prices, costs=FREE, forward_start=prices.index[100])
