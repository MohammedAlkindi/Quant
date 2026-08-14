"""Golden test: pins the cost-study grid and break-even table to data/SPY.csv.

Every value in docs/cost-study/results.md is enforced here at reported
precision, the same way tests/test_report_golden.py pins the README table.
If this test fails, either the data changed or the study changed - and
results.md must be regenerated, not hand-edited.
"""

import pytest

from quant.cost_study import evaluate_study
from quant.data import load_ohlcv

# (total_return, n_trades, annual_turnover) per cost level in bps/side.
BH = {
    0: (1.5531, 1, 0.10),
    1: (1.5529, 1, 0.10),
    2: (1.5526, 1, 0.10),
    5: (1.5518, 1, 0.10),
    10: (1.5506, 1, 0.10),
    20: (1.5480, 1, 0.10),
}

STRATS = {
    'ma_cross': {
        'params': (10, 200),
        'label': 'MA cross 10/200',
        'cells': {0: (0.9510, 13, 1.88), 1: (0.9485, 13, 1.88), 2: (0.9460, 13, 1.88), 5: (0.9384, 13, 1.88), 10: (0.9258, 13, 1.88), 20: (0.9010, 13, 1.88)},
        'edge0': -0.6021,
    },
    'price_vs_sma': {
        'params': (200,),
        'label': 'price > SMA 200',
        'cells': {0: (1.0222, 37, 5.07), 1: (1.0147, 37, 5.08), 2: (1.0073, 37, 5.08), 5: (0.9851, 37, 5.08), 10: (0.9488, 37, 5.09), 20: (0.8780, 37, 5.11)},
        'edge0': -0.5309,
    },
    'faber_tma': {
        'params': (8,),
        'label': 'Faber 8m TMA',
        'cells': {0: (0.7886, 15, 2.17), 1: (0.7859, 15, 2.17), 2: (0.7833, 15, 2.17), 5: (0.7753, 15, 2.17), 10: (0.7620, 15, 2.17), 20: (0.7358, 15, 2.17)},
        'edge0': -0.7645,
    },
    'tsmom': {
        'params': (12,),
        'label': 'TS momentum 12m',
        'cells': {0: (1.1805, 5, 0.55), 1: (1.1794, 5, 0.55), 2: (1.1783, 5, 0.55), 5: (1.1751, 5, 0.55), 10: (1.1697, 5, 0.55), 20: (1.1588, 5, 0.55)},
        'edge0': -0.3726,
    },
    'rsi2': {
        'params': (10.0,),
        'label': 'RSI(2) < 10',
        'cells': {0: (0.3764, 118, 18.34), 1: (0.3603, 118, 18.33), 2: (0.3443, 118, 18.32), 5: (0.2976, 118, 18.29), 10: (0.2232, 118, 18.25), 20: (0.0871, 118, 18.16)},
        'edge0': -1.1767,
    },
    'macd': {
        'params': (12, 26, 9),
        'label': 'MACD 12/26/9',
        'cells': {0: (0.5450, 150, 22.95), 1: (0.5220, 150, 22.95), 2: (0.4994, 150, 22.95), 5: (0.4334, 150, 22.94), 10: (0.3298, 150, 22.93), 20: (0.1446, 150, 22.92)},
        'edge0': -1.0081,
    },
    'bollinger_mr': {
        'params': (20, 2.0),
        'label': 'Bollinger 20d/2sd',
        'cells': {0: (0.4061, 58, 9.10), 1: (0.3980, 58, 9.10), 2: (0.3899, 58, 9.10), 5: (0.3659, 58, 9.09), 10: (0.3269, 58, 9.07), 20: (0.2521, 58, 9.05)},
        'edge0': -1.1470,
    },
    'donchian': {
        'params': (20, 10),
        'label': 'Donchian 20/10',
        'cells': {0: (0.9480, 63, 9.54), 1: (0.9358, 63, 9.54), 2: (0.9236, 63, 9.54), 5: (0.8876, 63, 9.54), 10: (0.8291, 63, 9.55), 20: (0.7174, 63, 9.56)},
        'edge0': -0.6051,
    },
    'halloween': {
        'params': (),
        'label': 'Halloween (Nov-Apr)',
        'cells': {0: (0.3859, 14, 2.12), 1: (0.3840, 14, 2.12), 2: (0.3820, 14, 2.12), 5: (0.3762, 14, 2.12), 10: (0.3666, 14, 2.12), 20: (0.3476, 14, 2.12)},
        'edge0': -1.1672,
    },
}


@pytest.fixture(scope='module')
def study():
    return evaluate_study(load_ohlcv('data/SPY.csv'))


def test_buy_and_hold_grid_is_pinned(study):
    for c, (ret, trades, turnover) in BH.items():
        cell = study['buy_and_hold'][c]
        assert cell['total_return'] == pytest.approx(ret, abs=1e-4)
        assert cell['n_trades'] == trades
        assert cell['annual_turnover'] == pytest.approx(turnover, abs=5e-3)


@pytest.mark.parametrize('key', sorted(STRATS))
def test_strategy_grid_is_pinned(study, key):
    pin = STRATS[key]
    entry = study['strategies'][key]
    assert entry['params'] == pin['params']
    assert entry['label'] == pin['label']
    for c, (ret, trades, turnover) in pin['cells'].items():
        cell = entry['cells'][c]
        assert cell['total_return'] == pytest.approx(ret, abs=1e-4)
        assert cell['n_trades'] == trades
        assert cell['annual_turnover'] == pytest.approx(turnover, abs=5e-3)
    assert entry['edges'][0.0] == pytest.approx(pin['edge0'], abs=1e-4)


def test_no_strategy_has_a_break_even_on_this_window(study):
    """The study's headline: every rule loses to buy-and-hold at ZERO cost
    on 2020-01 -> 2026-07 SPY, so no break-even cost exists anywhere."""
    for key, entry in study['strategies'].items():
        assert entry['break_even'] == {'kind': 'none', 'value': None}, key
        assert entry['edges'][0.0] < 0, key


def test_study_agrees_with_readme_table_at_reference_cost(study):
    """Cross-check against the numbers pinned by tests/test_report_golden.py:
    the 2 bps/side column must reproduce the README baseline exactly."""
    assert study['buy_and_hold'][2.0]['total_return'] == pytest.approx(1.5526, abs=1e-4)
    ma = study['strategies']['ma_cross']
    assert ma['params'] == (10, 200)
    assert ma['cells'][2.0]['total_return'] == pytest.approx(0.9460, abs=1e-4)
    assert ma['cells'][2.0]['n_trades'] == 13
