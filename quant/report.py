"""Reproduce the baseline backtest and print its metrics.

    python -m quant.report [path/to/ohlcv.csv]

Protocol, fixed before looking at out-of-sample data:

- In-sample = everything before OOS_START (2020-01-01); out-of-sample = the rest.
- The MA-crossover pair is chosen from a small fixed grid by net in-sample
  Sharpe, then evaluated once out of sample. Buy-and-hold is the benchmark and
  needs no selection.
- Both strategies run through quant.backtest.run_backtest: signals on the
  close, fills at the next open, costs charged per side (see CostModel).
- MA state warms up on full history: crossing into 2020 already long is
  information that was genuinely available on 2019-12-31.
- Sharpe uses rf=0 and is annualized at 252 periods/year.
"""

import sys
from pathlib import Path

import pandas as pd

from quant.backtest import BacktestResult, CostModel, run_backtest
from quant.data import load_ohlcv
from quant.metrics import annual_turnover, cagr, max_drawdown, sharpe, total_return
from quant.strategies import buy_and_hold, ma_crossover

OOS_START = pd.Timestamp('2020-01-01')
FAST_GRID = (10, 20, 50)
SLOW_GRID = (100, 150, 200)
DEFAULT_DATA = Path('data') / 'SPY.csv'


def split_is_oos(prices: pd.DataFrame, oos_start: pd.Timestamp = OOS_START) -> tuple[pd.DataFrame, pd.DataFrame]:
    return prices[prices.index < oos_start], prices[prices.index >= oos_start]


def select_ma_params(
    prices_is: pd.DataFrame,
    costs: CostModel,
    fast_grid: tuple[int, ...] = FAST_GRID,
    slow_grid: tuple[int, ...] = SLOW_GRID,
) -> tuple[int, int, float]:
    """Grid-pick (fast, slow) by net in-sample Sharpe. Deterministic: fixed
    iteration order, strictly-greater comparison, so ties keep the first pair."""
    best: tuple[int, int, float] | None = None
    for fast in fast_grid:
        for slow in slow_grid:
            weights = ma_crossover(prices_is['close'], fast, slow)
            result = run_backtest(prices_is, weights, costs)
            score = sharpe(result.returns)
            if best is None or score > best[2]:
                best = (fast, slow, score)
    assert best is not None
    return best


def _stats(result: BacktestResult) -> dict:
    return {
        'total_return': total_return(result.equity),
        'cagr': cagr(result.equity),
        'sharpe': sharpe(result.returns),
        'max_drawdown': max_drawdown(result.equity),
        'annual_turnover': annual_turnover(result.traded_notional, float(result.equity.mean()), len(result.equity)),
        'total_costs': result.total_costs,
        'n_trades': len(result.trades),
        'final_equity': result.final_equity,
        'trades': result.trades,
    }


def evaluate(
    prices: pd.DataFrame,
    costs: CostModel | None = None,
    oos_start: pd.Timestamp = OOS_START,
    initial_cash: float = 100_000.0,
) -> dict:
    costs = costs if costs is not None else CostModel()
    prices_is, prices_oos = split_is_oos(prices, oos_start)
    if len(prices_oos) < 2:
        raise ValueError(f'no out-of-sample data: prices end before {oos_start.date()}')
    if len(prices_is) <= max(SLOW_GRID):
        raise ValueError(f'in-sample window too short to fit a {max(SLOW_GRID)}-day moving average')

    fast, slow, is_sharpe = select_ma_params(prices_is, costs)
    close = prices['close']
    weight_sets = {
        'buy_and_hold': buy_and_hold(close),
        'ma_cross': ma_crossover(close, fast, slow),
    }
    report: dict = {
        name: _stats(run_backtest(prices_oos, weights.loc[prices_oos.index], costs, initial_cash))
        for name, weights in weight_sets.items()
    }
    report['meta'] = {
        'fast': fast,
        'slow': slow,
        'is_sharpe': is_sharpe,
        'oos_start': oos_start,
        'costs': costs,
        'initial_cash': initial_cash,
        'is_range': (prices_is.index[0], prices_is.index[-1]),
        'oos_range': (prices_oos.index[0], prices_oos.index[-1]),
    }
    return report


def main(data_path: Path = DEFAULT_DATA) -> None:
    prices = load_ohlcv(data_path)
    report = evaluate(prices)
    meta = report['meta']
    costs: CostModel = meta['costs']

    def pct(x: float) -> str:
        return f'{x * 100:+.2f}%'

    print(f'data           {data_path} ({len(prices)} rows, dividend/split-adjusted)')
    print(f'in-sample      {meta["is_range"][0].date()} -> {meta["is_range"][1].date()} (parameter selection only)')
    print(f'out-of-sample  {meta["oos_range"][0].date()} -> {meta["oos_range"][1].date()} (all metrics below)')
    print(
        f'costs/side     {costs.commission_bps} bps commission + {costs.half_spread_bps} bps half-spread '
        f'+ {costs.slippage_bps} bps slippage'
    )
    print('execution      signal on close t, fill at open t+1; long-only; fractional shares')
    print(f'ma params      fast={meta["fast"]}, slow={meta["slow"]} (grid-picked in-sample, net Sharpe {meta["is_sharpe"]:.2f})')
    print()
    header = f'{"strategy":<22}{"total return":>14}{"cagr":>9}{"sharpe":>8}{"max dd":>9}{"turnover/yr":>13}{"costs":>10}{"trades":>8}'
    print(header)
    print('-' * len(header))
    labels = {'buy_and_hold': 'SPY buy & hold', 'ma_cross': f'MA cross {meta["fast"]}/{meta["slow"]}'}
    for key, label in labels.items():
        s = report[key]
        print(
            f'{label:<22}{pct(s["total_return"]):>14}{pct(s["cagr"]):>9}{s["sharpe"]:>8.2f}'
            f'{pct(s["max_drawdown"]):>9}{s["annual_turnover"]:>12.2f}x{s["total_costs"]:>9.0f}{s["n_trades"]:>8}'
        )
    print()
    print('Sharpe uses rf=0. Costs are dollars paid on $100,000 initial equity.')


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA)
