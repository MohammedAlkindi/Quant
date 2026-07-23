import numpy as np
import pandas as pd
import pytest

from quant.backtest import CostModel
from quant.report import FAST_GRID, OOS_START, SLOW_GRID, evaluate, select_ma_params, split_is_oos

FREE = CostModel(commission_bps=0, half_spread_bps=0, slippage_bps=0)


def rising_prices(periods=750, start='2018-01-02'):
    idx = pd.bdate_range(start, periods=periods)
    close = np.linspace(100.0, 200.0, periods)
    return pd.DataFrame(
        {'open': close - 0.05, 'high': close + 0.5, 'low': close - 0.5, 'close': close, 'volume': 1e6},
        index=idx,
    )


def test_split_is_oos_partitions_on_the_boundary():
    prices = rising_prices()
    is_df, oos_df = split_is_oos(prices, OOS_START)
    assert is_df.index.max() < OOS_START
    assert oos_df.index.min() >= OOS_START
    assert len(is_df) + len(oos_df) == len(prices)


def test_select_ma_params_is_deterministic_and_from_the_grid():
    prices = rising_prices()
    first = select_ma_params(prices, FREE)
    second = select_ma_params(prices, FREE)
    assert first == second
    fast, slow, is_sharpe = first
    assert fast in FAST_GRID and slow in SLOW_GRID and fast < slow
    assert np.isfinite(is_sharpe)


def test_evaluate_warms_up_ma_from_pre_oos_history():
    # Monotone rise: fast MA > slow MA across the boundary, so the MA strategy
    # is long from the first out-of-sample decision, entering at the second
    # OOS bar's open exactly like buy-and-hold, and never exits.
    prices = rising_prices()
    report = evaluate(prices, costs=FREE)
    oos_index = prices.index[prices.index >= OOS_START]
    for name in ('buy_and_hold', 'ma_cross'):
        trades = report[name]['trades']
        assert len(trades) == 1
        assert trades['date'].iloc[0] == oos_index[1]


def test_evaluate_reports_the_agreed_metrics_for_both_strategies():
    report = evaluate(rising_prices(), costs=FREE)
    for name in ('buy_and_hold', 'ma_cross'):
        stats = report[name]
        for key in ('total_return', 'cagr', 'sharpe', 'max_drawdown', 'annual_turnover', 'total_costs', 'n_trades', 'final_equity'):
            assert np.isfinite(stats[key]), f'{name}.{key}'
    assert report['buy_and_hold']['n_trades'] == 1
    assert report['meta']['fast'] < report['meta']['slow']
    assert report['meta']['oos_start'] == OOS_START


def test_evaluate_charges_costs_when_cost_model_is_nonzero():
    priced = evaluate(rising_prices(), costs=CostModel(commission_bps=10, half_spread_bps=5, slippage_bps=5))
    free = evaluate(rising_prices(), costs=FREE)
    assert priced['buy_and_hold']['total_costs'] > 0
    assert priced['buy_and_hold']['final_equity'] < free['buy_and_hold']['final_equity']


def test_evaluate_rejects_data_ending_before_oos_start():
    prices = rising_prices(periods=200)  # ends mid-2018
    with pytest.raises(ValueError):
        evaluate(prices, costs=FREE)
