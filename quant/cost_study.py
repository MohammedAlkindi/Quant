"""Cost study: at what per-side cost does each commonly recommended retail
rule stop beating buy-and-hold on SPY?

    python -m quant.cost_study [path/to/ohlcv.csv]

Implements docs/cost-study/protocol.md verbatim: parameters grid-picked
in-sample (1993-2019) by net Sharpe at the 2 bps/side reference cost, then
held fixed while the out-of-sample window (2020-01-02 onward) is evaluated
at {0, 1, 2, 5, 10, 20} bps/side. Break-even is where the strategy's OOS
total return crosses buy-and-hold's at the same cost, linearly interpolated
between bracketing grid levels.

The engine is quant.backtest.run_backtest, unmodified; a cost level c is
CostModel(0, 0, c), drag-identical at c=2 to the repo default (0.5, 0.5, 1).
"""

import sys
from pathlib import Path

import pandas as pd

from quant.backtest import BacktestResult, CostModel, run_backtest
from quant.data import load_ohlcv
from quant.metrics import annual_turnover, cagr, max_drawdown, sharpe, total_return
from quant.report import DEFAULT_DATA, OOS_START, split_is_oos
from quant.strategies import buy_and_hold, ma_crossover
from quant.study_strategies import bollinger_mr, donchian, faber_tma, halloween, macd, rsi2, tsmom

COST_LEVELS_BPS = (0.0, 1.0, 2.0, 5.0, 10.0, 20.0)
REF_COST_BPS = 2.0

# key -> (label template, pre-registered grid, builder(prices, params) -> weights)
STRATEGIES = {
    'ma_cross': (
        'MA cross {0}/{1}',
        tuple((f, s) for f in (10, 20, 50) for s in (100, 150, 200)),
        lambda p, params: ma_crossover(p['close'], *params),
    ),
    'price_vs_sma': (
        'price > SMA {0}',
        ((50,), (150,), (200,)),
        lambda p, params: ma_crossover(p['close'], 1, params[0]),
    ),
    'faber_tma': (
        'Faber {0}m TMA',
        ((8,), (10,), (12,)),
        lambda p, params: faber_tma(p['close'], params[0]),
    ),
    'tsmom': (
        'TS momentum {0}m',
        ((6,), (9,), (12,)),
        lambda p, params: tsmom(p['close'], params[0]),
    ),
    'rsi2': (
        'RSI(2) < {0:g}',
        ((5.0,), (10.0,)),
        lambda p, params: rsi2(p['close'], params[0]),
    ),
    'macd': (
        'MACD {0}/{1}/{2}',
        ((12, 26, 9),),
        lambda p, params: macd(p['close'], *params),
    ),
    'bollinger_mr': (
        'Bollinger {0}d/{1:g}sd',
        ((20, 2.0),),
        lambda p, params: bollinger_mr(p['close'], *params),
    ),
    'donchian': (
        'Donchian {0}/{1}',
        ((20, 10), (55, 20)),
        lambda p, params: donchian(p, *params),
    ),
    'halloween': (
        'Halloween (Nov-Apr)',
        ((),),
        lambda p, params: halloween(p['close']),
    ),
}


def cost_model(bps_per_side: float) -> CostModel:
    return CostModel(commission_bps=0.0, half_spread_bps=0.0, slippage_bps=bps_per_side)


def _stats(result: BacktestResult) -> dict:
    return {
        'total_return': total_return(result.equity),
        'cagr': cagr(result.equity),
        'sharpe': sharpe(result.returns),
        'max_drawdown': max_drawdown(result.equity),
        'annual_turnover': annual_turnover(result.traded_notional, float(result.equity.mean()), len(result.equity)),
        'total_costs': result.total_costs,
        'n_trades': len(result.trades),
    }


def select_params(prices_is: pd.DataFrame, key: str, costs: CostModel) -> tuple[tuple, float]:
    """Grid-pick by net in-sample Sharpe: fixed iteration order, strictly
    greater, ties keep the first entry - the protocol's one rule."""
    _, grid, builder = STRATEGIES[key]
    best: tuple[tuple, float] | None = None
    for params in grid:
        weights = builder(prices_is, params)
        score = sharpe(run_backtest(prices_is, weights, costs).returns)
        if best is None or score > best[1]:
            best = (params, score)
    assert best is not None
    return best


def break_even(edges: list[tuple[float, float]]) -> dict:
    """edges = [(cost_bps, strategy_return - bh_return)] in ascending cost.
    Returns {'kind': 'none' | 'crossing' | 'above_max', 'value': float | None}."""
    if edges[0][1] <= 0:
        return {'kind': 'none', 'value': None}
    for (c1, e1), (c2, e2) in zip(edges, edges[1:], strict=False):
        if e1 > 0 >= e2:
            return {'kind': 'crossing', 'value': c1 + e1 * (c2 - c1) / (e1 - e2)}
    return {'kind': 'above_max', 'value': edges[-1][0]}


def evaluate_study(prices: pd.DataFrame, initial_cash: float = 100_000.0) -> dict:
    prices_is, prices_oos = split_is_oos(prices)
    ref_costs = cost_model(REF_COST_BPS)

    bh_weights = buy_and_hold(prices['close'])
    bh_cells = {
        c: _stats(run_backtest(prices_oos, bh_weights.loc[prices_oos.index], cost_model(c), initial_cash))
        for c in COST_LEVELS_BPS
    }

    strategies: dict = {}
    for key, (label_tpl, _grid, builder) in STRATEGIES.items():
        params, is_sharpe = select_params(prices_is, key, ref_costs)
        weights = builder(prices, params).loc[prices_oos.index]
        cells = {
            c: _stats(run_backtest(prices_oos, weights, cost_model(c), initial_cash)) for c in COST_LEVELS_BPS
        }
        edges = [(c, cells[c]['total_return'] - bh_cells[c]['total_return']) for c in COST_LEVELS_BPS]
        strategies[key] = {
            'label': label_tpl.format(*params) if params else label_tpl,
            'params': params,
            'is_sharpe': is_sharpe,
            'cells': cells,
            'edges': dict(edges),
            'break_even': break_even(edges),
        }

    return {
        'meta': {
            'cost_levels_bps': COST_LEVELS_BPS,
            'ref_cost_bps': REF_COST_BPS,
            'oos_start': OOS_START,
            'is_range': (prices_is.index[0], prices_is.index[-1]),
            'oos_range': (prices_oos.index[0], prices_oos.index[-1]),
            'initial_cash': initial_cash,
            'n_rows': len(prices),
        },
        'buy_and_hold': bh_cells,
        'strategies': strategies,
    }


def _sort_key(entry: dict) -> tuple:
    be = entry['break_even']
    rank = {'above_max': 0, 'crossing': 1, 'none': 2}[be['kind']]
    value = -(be['value'] if be['value'] is not None else float('-inf'))
    return (rank, value, -entry['edges'][0.0])


def main(data_path: Path = DEFAULT_DATA) -> None:
    prices = load_ohlcv(data_path)
    study = evaluate_study(prices)
    meta = study['meta']

    def pct(x: float) -> str:
        return f'{x * 100:+.2f}%'

    print(f'data           {data_path} ({meta["n_rows"]} rows, dividend/split-adjusted; SPY only)')
    print(f'in-sample      {meta["is_range"][0].date()} -> {meta["is_range"][1].date()} (selection at {meta["ref_cost_bps"]:g} bps/side)')
    print(f'out-of-sample  {meta["oos_range"][0].date()} -> {meta["oos_range"][1].date()} (all numbers below)')
    print('execution      signal on close t, fill at open t+1; long-only; params fixed across cost levels')
    print('protocol       docs/cost-study/protocol.md (pre-registered)')

    for c in meta['cost_levels_bps']:
        print()
        header = (
            f'--- {c:g} bps/side '
            f'{"strategy":<21}{"total return":>13}{"cagr":>9}{"sharpe":>8}{"max dd":>9}{"turnover/yr":>13}{"costs":>9}{"trades":>8}'
        )
        print(header)
        rows = [('SPY buy & hold', study['buy_and_hold'][c])] + [
            (entry['label'], entry['cells'][c]) for entry in study['strategies'].values()
        ]
        for label, s in rows:
            print(
                f'{"":>16}{label:<21}{pct(s["total_return"]):>13}{pct(s["cagr"]):>9}{s["sharpe"]:>8.2f}'
                f'{pct(s["max_drawdown"]):>9}{s["annual_turnover"]:>12.2f}x{s["total_costs"]:>9.0f}{s["n_trades"]:>8}'
            )

    print()
    print('Break-even per-side cost vs buy-and-hold (OOS total return; linear interpolation between grid levels)')
    header = f'{"strategy":<22}{"turnover/yr":>12}{"gross edge":>12}  {"break-even":<18}'
    print(header)
    print('-' * len(header))
    for entry in sorted(study['strategies'].values(), key=_sort_key):
        turnover = entry['cells'][meta['ref_cost_bps']]['annual_turnover']
        edge0 = entry['edges'][0.0]
        be = entry['break_even']
        if be['kind'] == 'none':
            be_text = 'none - loses at 0'
        elif be['kind'] == 'above_max':
            be_text = f'> {be["value"]:g} bps'
        else:
            be_text = f'~{be["value"]:.1f} bps (interp.)'
        print(f'{entry["label"]:<22}{turnover:>11.2f}x{edge0 * 100:>+10.1f}pp  {be_text:<18}')
    print()
    print('Gross edge = OOS total return minus buy-and-hold at 0 bps/side. Turnover counts')
    print('both legs, so annual cost drag ~ turnover x cost per side. SPY only; see protocol')
    print('for the multiple-comparisons and regime caveats.')


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA)
