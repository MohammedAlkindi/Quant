"""Pins the forward-window numbers to the committed base + IBKR tail data.

If this fails, the spliced snapshot, the engine, or the frozen protocol
changed -- and every documented forward figure is stale until regenerated
with `python -m quant.forward`. Extending the tail with newer bars is the
one expected cause: refresh the constants and the docs tables together
(see forward/README.md).
"""

from pathlib import Path

import pandas as pd
import pytest

from quant.forward import evaluate_forward, load_spliced

ROOT = Path(__file__).resolve().parents[1]
DATA_BASE = ROOT / 'data' / 'SPY.csv'
DATA_TAIL = ROOT / 'forward' / 'data' / 'SPY_tail_ibkr.csv'

# Over 2026-07-23 -> 2026-08-13 the crossover was long on every bar (no cross
# fired), so the strategy and the benchmark are the same portfolio: one entry
# fill at the 2026-07-24 open, identical rows. Divergence only appears once a
# forward bar produces a cross.
EXPECTED = {
    'buy_and_hold': {
        'total_return': 0.053057,
        'cagr': 1.383357,
        'sharpe': 6.451822,
        'max_drawdown': -0.015388,
        'annual_turnover': 15.368059,
        'n_trades': 1,
    },
    'ma_cross': {
        'total_return': 0.053057,
        'cagr': 1.383357,
        'sharpe': 6.451822,
        'max_drawdown': -0.015388,
        'annual_turnover': 15.368059,
        'n_trades': 1,
    },
}


@pytest.fixture(scope='module')
def report():
    return evaluate_forward(load_spliced(DATA_BASE, DATA_TAIL))


def test_window_boundaries_and_frozen_parameters(report):
    meta = report['meta']
    assert meta['base_end'] == pd.Timestamp('2026-07-22')
    assert meta['forward_range'] == (pd.Timestamp('2026-07-23'), pd.Timestamp('2026-08-13'))
    assert meta['n_bars'] == 16
    assert (meta['fast'], meta['slow']) == (10, 200)


def test_forward_metrics_match_the_docs(report):
    for strategy, expected in EXPECTED.items():
        for metric, value in expected.items():
            assert report[strategy][metric] == pytest.approx(value, rel=1e-4), f'{strategy}.{metric}'
