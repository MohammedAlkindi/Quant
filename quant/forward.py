"""Forward test: the frozen baseline on bars that postdate the committed snapshot.

The committed backtest picked MA 10/200 in-sample (1993-2019) and evaluated it
once out of sample (2020-01-02 -> 2026-07-22, the data/SPY.csv snapshot). Both
of those windows have now been looked at. This module evaluates the same frozen
strategy, through the same engine and cost model, on bars the repo had never
seen when those numbers were produced: the forward window, 2026-07-23 onward.

    python -m quant.forward

Constraints, stated so the tests can hold them to account:

- Parameters are frozen at 10/200. Nothing here re-runs grid selection;
  re-picking on data that includes the evaluation window would be tuning.
- MA state warms up on the full spliced history, exactly as the committed
  backtest warms up across its own in-sample/OOS boundary.
- The forward tail (forward/data/SPY_tail_ibkr.csv) is raw IBKR trade prices
  (split-adjusted, not dividend-adjusted). Splicing raw bars onto the
  dividend-adjusted base is valid only while no SPY ex-dividend falls after
  the base snapshot's last row, so splice() refuses when the overlap between
  the two files disagrees beyond price-feed rounding.
  forward/data/PROVENANCE.md records the seam measurements and refresh rule.
- No network and no re-fetch at runtime: two committed CSVs, deterministic.
"""

from pathlib import Path

import pandas as pd

from quant.backtest import CostModel, run_backtest
from quant.data import load_ohlcv
from quant.report import _stats
from quant.strategies import buy_and_hold, ma_crossover

FROZEN_FAST = 10
FROZEN_SLOW = 200
FORWARD_START = pd.Timestamp('2026-07-23')
BASE_DATA = Path('data') / 'SPY.csv'
TAIL_DATA = Path('forward') / 'data' / 'SPY_tail_ibkr.csv'
CLOSE_TOLERANCE = 0.005  # dollars/share; measured seam gap is $0.00003 (PROVENANCE.md)
MIN_OVERLAP = 10


def splice(base: pd.DataFrame, tail: pd.DataFrame, close_tolerance: float = CLOSE_TOLERANCE) -> pd.DataFrame:
    """Append the tail rows that postdate the base snapshot, guarding the seam.

    The overlap between the two files is a measurement seam: if the vendors
    disagree there (for instance because a new dividend has shifted the
    adjusted base since the tail was fetched), extending the series would
    silently change what the backtest sees, so this refuses instead. Base
    rows win inside the overlap; only strictly newer tail rows are appended.
    """
    overlap = base.index.intersection(tail.index)
    if len(overlap) < MIN_OVERLAP:
        raise ValueError(f'need at least {MIN_OVERLAP} overlapping bars to verify the splice seam, got {len(overlap)}')
    gap = float((base.loc[overlap, 'close'] - tail.loc[overlap, 'close']).abs().max())
    if gap > close_tolerance:
        raise ValueError(
            f'splice seam: overlap closes disagree by up to {gap:.4f} (tolerance {close_tolerance}); '
            f're-fetch the base snapshot instead of splicing across an adjustment event'
        )
    new = tail[tail.index > base.index[-1]]
    if new.empty:
        raise ValueError('tail adds no bars beyond the base snapshot')
    return pd.concat([base, new])


def load_spliced(base_path: str | Path = BASE_DATA, tail_path: str | Path = TAIL_DATA) -> pd.DataFrame:
    return splice(load_ohlcv(base_path), load_ohlcv(tail_path))


def evaluate_forward(
    prices: pd.DataFrame,
    costs: CostModel | None = None,
    forward_start: pd.Timestamp = FORWARD_START,
    initial_cash: float = 100_000.0,
) -> dict:
    costs = costs if costs is not None else CostModel()
    history = prices[prices.index < forward_start]
    prices_fwd = prices[prices.index >= forward_start]
    if len(history) < FROZEN_SLOW:
        raise ValueError(f'need at least {FROZEN_SLOW} warm-up bars before {forward_start.date()}, got {len(history)}')
    if len(prices_fwd) < 2:
        raise ValueError(f'forward window needs at least 2 bars on or after {forward_start.date()}')

    close = prices['close']
    weight_sets = {
        'buy_and_hold': buy_and_hold(close),
        'ma_cross': ma_crossover(close, FROZEN_FAST, FROZEN_SLOW),
    }
    report: dict = {
        name: _stats(run_backtest(prices_fwd, weights.loc[prices_fwd.index], costs, initial_cash))
        for name, weights in weight_sets.items()
    }
    report['meta'] = {
        'fast': FROZEN_FAST,
        'slow': FROZEN_SLOW,
        'costs': costs,
        'initial_cash': initial_cash,
        'base_end': history.index[-1],
        'forward_range': (prices_fwd.index[0], prices_fwd.index[-1]),
        'n_bars': len(prices_fwd),
    }
    return report


def main() -> None:
    prices = load_spliced()
    report = evaluate_forward(prices)
    meta = report['meta']
    costs: CostModel = meta['costs']

    def pct(x: float) -> str:
        return f'{x * 100:+.2f}%'

    print(f'base data      {BASE_DATA} (dividend/split-adjusted, ends {meta["base_end"].date()})')
    print(f'forward tail   {TAIL_DATA} (raw IBKR daily bars; seam-checked, see forward/data/PROVENANCE.md)')
    print('in-sample      1993-01-29 -> 2019-12-31 (parameter selection, done in the committed backtest)')
    print('seen OOS       2020-01-02 -> 2026-07-22 (committed backtest evaluation; already looked at)')
    print(
        f'forward        {meta["forward_range"][0].date()} -> {meta["forward_range"][1].date()} '
        f'({meta["n_bars"]} bars no committed decision has seen)'
    )
    print(f'ma params      fast={meta["fast"]}, slow={meta["slow"]} (frozen from the 1993-2019 selection; never re-fit here)')
    print(
        f'costs/side     {costs.commission_bps} bps commission + {costs.half_spread_bps} bps half-spread '
        f'+ {costs.slippage_bps} bps slippage'
    )
    print('execution      signal on close t, fill at open t+1; long-only; fractional shares')
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
    print(f'Sharpe uses rf=0. Costs are dollars paid on ${meta["initial_cash"]:,.0f} initial equity.')
    print(f'Sample size: {meta["n_bars"]} daily bars, {report["ma_cross"]["n_trades"]} strategy trade(s).')
    print('A window this short cannot distinguish skill from luck; it exists to accumulate.')
    print('Annualized figures (cagr, sharpe, turnover) extrapolate a few weeks and are format compatibility only.')


if __name__ == '__main__':
    main()
