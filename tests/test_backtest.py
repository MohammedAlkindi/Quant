import pandas as pd
import pytest

from quant.backtest import CostModel, run_backtest

DRAG = CostModel(commission_bps=10, half_spread_bps=5, slippage_bps=5)  # 20 bps one way
FREE = CostModel(commission_bps=0, half_spread_bps=0, slippage_bps=0)


def make_prices(opens, closes):
    idx = pd.bdate_range('2024-01-01', periods=len(opens))
    return pd.DataFrame({'open': opens, 'close': closes}, index=idx, dtype=float)


def weights_for(prices, values):
    return pd.Series([float(v) for v in values], index=prices.index)


def test_delayed_execution_and_cost_accounting_match_hand_computation():
    prices = make_prices(opens=[100, 102, 104, 106], closes=[101, 103, 105, 104])
    weights = weights_for(prices, [1, 1, 0, 0])
    result = run_backtest(prices, weights, DRAG, initial_cash=10_000.0)

    # Weight decided at bar 0's close fills at bar 1's open, 102, buy-side drag 20 bps.
    shares = 10_000.0 / (102 * 1.002)
    expected_equity = [
        10_000.0,             # bar 0: flat, nothing executed yet
        shares * 103,         # bar 1: entered at open, marked at close
        shares * 105,         # bar 2: still long (weight change at close 2 fills next open)
        shares * 106 * 0.998, # bar 3: sold at open 106 with sell-side drag; all cash
    ]
    assert result.equity.tolist() == pytest.approx(expected_equity)

    assert len(result.trades) == 2
    assert result.trades['side'].tolist() == ['buy', 'sell']
    assert result.traded_notional == pytest.approx(shares * 102 + shares * 106)
    assert result.total_costs == pytest.approx(shares * 102 * 0.002 + shares * 106 * 0.002)
    assert result.final_equity == pytest.approx(shares * 106 * 0.998)


def test_no_target_change_means_no_trades_and_no_costs():
    prices = make_prices(opens=[100, 90, 80], closes=[95, 85, 75])
    weights = weights_for(prices, [0, 0, 0])
    result = run_backtest(prices, weights, DRAG, initial_cash=5_000.0)
    assert len(result.trades) == 0
    assert result.total_costs == 0.0
    assert result.equity.tolist() == [5_000.0, 5_000.0, 5_000.0]


def test_zero_cost_buy_and_hold_tracks_the_market_exactly():
    prices = make_prices(opens=[50, 52, 48, 51], closes=[51, 50, 49, 53])
    weights = weights_for(prices, [1, 1, 1, 1])
    result = run_backtest(prices, weights, FREE, initial_cash=1_000.0)
    shares = 1_000.0 / 52  # fills at bar 1's open with no drag
    assert result.equity.tolist() == pytest.approx([1_000.0, shares * 50, shares * 49, shares * 53])
    assert result.total_costs == 0.0
    assert result.traded_notional == pytest.approx(1_000.0)


def test_full_weight_buy_internalizes_costs_without_negative_cash():
    prices = make_prices(opens=[100, 100], closes=[100, 100])
    weights = weights_for(prices, [1, 1])
    result = run_backtest(prices, weights, DRAG, initial_cash=10_000.0)
    buy = result.trades.iloc[0]
    # Buy is sized against the cost-adjusted fill, so cash lands on exactly zero.
    assert buy['shares'] * 100 * 1.002 == pytest.approx(10_000.0)
    assert result.final_equity < 10_000.0  # the drag was genuinely paid


def test_decision_on_last_bar_never_executes():
    prices = make_prices(opens=[10, 11, 12], closes=[10, 11, 12])
    weights = weights_for(prices, [0, 0, 1])
    result = run_backtest(prices, weights, DRAG)
    assert len(result.trades) == 0


def test_rejects_leverage_shorts_and_misaligned_weights():
    prices = make_prices(opens=[10, 11], closes=[10, 11])
    with pytest.raises(ValueError):
        run_backtest(prices, weights_for(prices, [1.5, 1]), FREE)
    with pytest.raises(ValueError):
        run_backtest(prices, weights_for(prices, [-0.2, 0]), FREE)
    bad_index = pd.Series([1.0, 1.0], index=pd.bdate_range('2030-01-01', periods=2))
    with pytest.raises(ValueError):
        run_backtest(prices, bad_index, FREE)


def test_returns_are_equity_percent_changes():
    prices = make_prices(opens=[100, 100, 100], closes=[100, 110, 99])
    weights = weights_for(prices, [1, 1, 1])
    result = run_backtest(prices, weights, FREE, initial_cash=1_000.0)
    assert result.returns.tolist() == pytest.approx([0.10, -0.10])
