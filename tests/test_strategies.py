import pandas as pd
import pytest

from quant.strategies import buy_and_hold, ma_crossover


def make_close(values):
    idx = pd.bdate_range('2024-01-01', periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def test_buy_and_hold_is_always_fully_invested():
    close = make_close([10, 11, 9, 12])
    weights = buy_and_hold(close)
    assert weights.tolist() == [1.0, 1.0, 1.0, 1.0]
    assert (weights.index == close.index).all()


def test_ma_crossover_goes_long_only_when_fast_above_slow():
    # MA2 vs MA3 crossings computed by hand for this path.
    close = make_close([10, 10, 10, 10, 20, 30, 40, 10, 5, 5])
    weights = ma_crossover(close, fast=2, slow=3)
    assert weights.tolist() == [0, 0, 0, 0, 1, 1, 1, 0, 0, 0]


def test_ma_crossover_is_flat_until_slow_window_fills():
    close = make_close([10, 20, 30, 40, 50, 60])
    weights = ma_crossover(close, fast=2, slow=5)
    assert weights.iloc[:4].tolist() == [0, 0, 0, 0]
    assert weights.iloc[4:].tolist() == [1, 1]


def test_ma_crossover_rejects_fast_not_below_slow():
    close = make_close([10, 11, 12])
    with pytest.raises(ValueError):
        ma_crossover(close, fast=5, slow=5)
