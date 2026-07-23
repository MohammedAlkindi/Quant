import pandas as pd
import pytest

from quant.metrics import annual_turnover, cagr, max_drawdown, sharpe, total_return


def test_total_return_is_end_over_start():
    equity = pd.Series([100.0, 110.0, 121.0])
    assert total_return(equity) == pytest.approx(0.21)


def test_cagr_annualizes_over_return_periods():
    # 252 daily periods (253 points) doubling once: CAGR == 100%.
    equity = pd.Series([1.0] * 1 + [2.0] * 252, dtype=float)
    equity.iloc[:] = [1.0 * (2.0 ** (i / 252)) for i in range(253)]
    assert cagr(equity, periods_per_year=252) == pytest.approx(1.0)


def test_sharpe_matches_hand_computation():
    # mean 0.005, sample std 0.021213203; 0.005 / 0.021213203 * sqrt(252) = 3.74166
    returns = pd.Series([0.02, -0.01])
    assert sharpe(returns, periods_per_year=252) == pytest.approx(3.74166, rel=1e-4)


def test_sharpe_subtracts_risk_free_rate():
    returns = pd.Series([0.02, -0.01])
    # Annual rf of 2.52% is 0.0001 per period: mean excess 0.0049.
    expected = 0.0049 / 0.021213203 * (252**0.5)
    assert sharpe(returns, periods_per_year=252, rf_annual=0.0252) == pytest.approx(expected, rel=1e-4)


def test_sharpe_of_constant_returns_is_zero_by_convention():
    returns = pd.Series([0.01, 0.01, 0.01])
    assert sharpe(returns) == 0.0


def test_max_drawdown_finds_worst_peak_to_trough():
    equity = pd.Series([100.0, 120.0, 90.0, 130.0, 65.0])
    assert max_drawdown(equity) == pytest.approx(-0.5)


def test_max_drawdown_is_zero_for_monotonic_rise():
    equity = pd.Series([100.0, 101.0, 105.0])
    assert max_drawdown(equity) == 0.0


def test_annual_turnover_scales_notional_by_equity_and_time():
    # 1000 traded against 500 average equity over one year = 2x per year.
    assert annual_turnover(traded_notional=1000.0, avg_equity=500.0, n_periods=252) == pytest.approx(2.0)
    # Same trading over two years halves the annual rate.
    assert annual_turnover(traded_notional=1000.0, avg_equity=500.0, n_periods=504) == pytest.approx(1.0)
