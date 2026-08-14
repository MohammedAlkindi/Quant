"""Unit tests for the cost-study runner's pure logic."""

import pytest

from quant.backtest import CostModel
from quant.cost_study import COST_LEVELS_BPS, REF_COST_BPS, STRATEGIES, break_even, cost_model


def test_cost_model_matches_repo_default_drag_at_reference():
    assert cost_model(REF_COST_BPS).one_way_drag == CostModel().one_way_drag


def test_cost_levels_are_ascending_and_include_reference():
    assert list(COST_LEVELS_BPS) == sorted(COST_LEVELS_BPS)
    assert REF_COST_BPS in COST_LEVELS_BPS


def test_break_even_none_when_losing_at_zero():
    edges = [(0.0, -0.0413), (1.0, -0.0527), (2.0, -0.0641)]
    assert break_even(edges) == {'kind': 'none', 'value': None}


def test_break_even_interpolates_between_bracketing_levels():
    # Edge +0.031 at 5 bps, -0.017 at 10 bps: crossing at 5 + 0.031/0.048 * 5.
    edges = [(0.0, 0.089), (5.0, 0.031), (10.0, -0.017)]
    result = break_even(edges)
    assert result['kind'] == 'crossing'
    assert result['value'] == pytest.approx(5.0 + 0.031 * 5.0 / 0.048)


def test_break_even_exact_zero_at_grid_point_returns_that_point():
    edges = [(0.0, 0.062), (5.0, 0.0), (10.0, -0.029)]
    result = break_even(edges)
    assert result['kind'] == 'crossing'
    assert result['value'] == pytest.approx(5.0)


def test_break_even_above_max_when_positive_everywhere():
    edges = [(0.0, 0.057), (10.0, 0.023), (20.0, 0.004)]
    assert break_even(edges) == {'kind': 'above_max', 'value': 20.0}


def test_every_registered_grid_is_nonempty_and_pre_registered_size():
    # 25 in-sample variants across 9 strategies, per the protocol's strategy
    # table (its prose said 17 - see the dated correction in protocol.md).
    sizes = {key: len(grid) for key, (_, grid, _) in STRATEGIES.items()}
    assert sum(sizes.values()) == 25
    assert set(sizes) == {
        'ma_cross',
        'price_vs_sma',
        'faber_tma',
        'tsmom',
        'rsi2',
        'macd',
        'bollinger_mr',
        'donchian',
        'halloween',
    }
