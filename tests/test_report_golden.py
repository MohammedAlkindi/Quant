"""Pins the README's reported numbers to the vendored data and the engine.

If this fails, either the data snapshot, the engine, or the protocol changed —
and the README table is stale until it is regenerated with `python -m quant.report`.
"""

from pathlib import Path

import pytest

from quant.data import load_ohlcv
from quant.report import evaluate

DATA = Path(__file__).resolve().parents[1] / 'data' / 'SPY.csv'

EXPECTED = {
    'buy_and_hold': {
        'total_return': 1.552611,
        'cagr': 0.154374,
        'sharpe': 0.810652,
        'max_drawdown': -0.337172,
        'annual_turnover': 0.097239,
        'n_trades': 1,
    },
    'ma_cross': {
        'total_return': 0.945959,
        'cagr': 0.107370,
        'sharpe': 0.831572,
        'max_drawdown': -0.205137,
        'annual_turnover': 1.875766,
        'n_trades': 13,
    },
}


@pytest.fixture(scope='module')
def report():
    return evaluate(load_ohlcv(DATA))


def test_grid_selects_10_200_in_sample(report):
    meta = report['meta']
    assert (meta['fast'], meta['slow']) == (10, 200)
    assert meta['is_sharpe'] == pytest.approx(0.795225, rel=1e-4)


def test_out_of_sample_metrics_match_the_readme(report):
    for strategy, expected in EXPECTED.items():
        for metric, value in expected.items():
            assert report[strategy][metric] == pytest.approx(value, rel=1e-4), f'{strategy}.{metric}'
