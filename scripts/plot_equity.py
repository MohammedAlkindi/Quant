"""Regenerate docs/assets/equity_curve.png from the vendored data.

Replays the exact protocol of `python -m quant.report` (same data, grid-picked
params, cost model, delayed execution) and cross-checks the curves against
evaluate()'s final equity, so the chart cannot silently drift from the README
table.

Usage: python scripts/plot_equity.py
"""

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from quant.backtest import CostModel, run_backtest
from quant.data import load_ohlcv
from quant.report import DEFAULT_DATA, OOS_START, evaluate
from quant.strategies import buy_and_hold, ma_crossover

# dataviz reference palette, dark mode. Two-series set validated 2026-07-23:
# CVD dE 26.8, normal-vision dE 31.8, both series >= 3:1 on the surface.
SURFACE = '#1a1a19'
INK = '#ffffff'
INK_SECONDARY = '#c3c2b7'
INK_MUTED = '#898781'
GRID = '#2c2c2a'
BASELINE = '#383835'
BENCHMARK_BLUE = '#3987e5'
STRATEGY_ORANGE = '#d95926'

OUT = Path('docs') / 'assets' / 'equity_curve.png'


def build_curves() -> tuple[dict, dict]:
    prices = load_ohlcv(DEFAULT_DATA)
    report = evaluate(prices)
    meta = report['meta']
    costs: CostModel = meta['costs']
    oos = prices[prices.index >= OOS_START]

    weight_sets = {
        'buy_and_hold': buy_and_hold(prices['close']),
        'ma_cross': ma_crossover(prices['close'], meta['fast'], meta['slow']),
    }
    curves = {
        name: run_backtest(oos, weights.loc[oos.index], costs, meta['initial_cash']).equity
        for name, weights in weight_sets.items()
    }
    for name, equity in curves.items():
        drift = abs(float(equity.iloc[-1]) - report[name]['final_equity'])
        if drift > 1e-6:
            raise SystemExit(f'{name}: chart curve diverged from quant.report by {drift}')
    return curves, meta


def main() -> None:
    curves, meta = build_curves()
    labels = {
        'buy_and_hold': ('SPY buy & hold', BENCHMARK_BLUE),
        'ma_cross': (f'MA cross {meta["fast"]}/{meta["slow"]}', STRATEGY_ORANGE),
    }

    fig, ax = plt.subplots(figsize=(9.6, 5.0), dpi=175)
    fig.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    for name, equity in curves.items():
        label, color = labels[name]
        ax.plot(equity.index, equity.values, color=color, linewidth=2, label=label, solid_capstyle='round')
        ax.scatter([equity.index[-1]], [equity.iloc[-1]], s=18, color=color, zorder=3)
        ax.annotate(
            f'{label}\n${equity.iloc[-1] / 1000:,.0f}k',
            xy=(equity.index[-1], equity.iloc[-1]),
            xytext=(10, 0),
            textcoords='offset points',
            va='center',
            fontsize=9,
            color=INK_SECONDARY,
            annotation_clip=False,
        )

    ax.set_title(
        'Out-of-sample equity, $100k start',
        loc='left', color=INK, fontsize=13, fontweight='bold', pad=26,
    )
    ax.text(
        0, 1.03,
        f'{curves["buy_and_hold"].index[0].date()} → {curves["buy_and_hold"].index[-1].date()}'
        '  ·  signals on close t, fills at open t+1  ·  2 bps/side costs'
        '  ·  dividend-adjusted SPY',
        transform=ax.transAxes, color=INK_SECONDARY, fontsize=9,
    )

    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x / 1000:,.0f}k'))
    ax.margins(x=0.01)

    legend = ax.legend(loc='upper left', frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY)
    for line in legend.get_lines():
        line.set_linewidth(3)

    fig.subplots_adjust(left=0.075, right=0.845, top=0.86, bottom=0.09)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor=SURFACE)
    print(f'wrote {OUT} ({OUT.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
