"""Regenerate docs/assets/cost_degradation.png from the vendored data.

Plots out-of-sample total return against per-side cost for every strategy in
the cost study, with buy-and-hold flat across the top. The curves are read
straight out of quant.cost_study.evaluate_study - the same values pinned by
tests/test_cost_study_golden.py - so the chart cannot drift from
docs/cost-study/results.md.

Usage: python scripts/plot_cost_study.py
"""

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from quant.cost_study import evaluate_study
from quant.data import load_ohlcv
from quant.report import DEFAULT_DATA

# dataviz reference palette, dark mode - same surface/ink set as plot_equity.py.
SURFACE = '#1a1a19'
INK = '#ffffff'
INK_SECONDARY = '#c3c2b7'
INK_MUTED = '#898781'
GRID = '#2c2c2a'
BASELINE = '#383835'
BENCHMARK_BLUE = '#3987e5'

STRATEGY_COLORS = {
    'tsmom': '#d95926',
    'price_vs_sma': '#e5b83c',
    'ma_cross': '#7fbf4d',
    'donchian': '#3fbfa8',
    'faber_tma': '#b085e8',
    'macd': '#e06ba8',
    'bollinger_mr': '#e08b8b',
    'halloween': '#a8b23c',
    'rsi2': '#8f9fb3',
}

OUT = Path('docs') / 'assets' / 'cost_degradation.png'
MIN_LABEL_GAP = 6.5  # percentage points between right-edge labels


def spread_labels(targets: list[float], min_gap: float) -> list[float]:
    """Nudge label y-positions downward from the top so none overlap."""
    positions: list[float] = []
    for y in targets:  # targets must be sorted descending
        if positions and positions[-1] - y < min_gap:
            y = positions[-1] - min_gap
        positions.append(y)
    return positions


def main() -> None:
    study = evaluate_study(load_ohlcv(DEFAULT_DATA))
    costs = list(study['meta']['cost_levels_bps'])

    series: list[tuple[str, str, list[float]]] = [
        ('SPY buy & hold', BENCHMARK_BLUE, [study['buy_and_hold'][c]['total_return'] * 100 for c in costs]),
    ]
    for key, color in STRATEGY_COLORS.items():
        entry = study['strategies'][key]
        series.append((entry['label'], color, [entry['cells'][c]['total_return'] * 100 for c in costs]))

    fig, ax = plt.subplots(figsize=(9.6, 5.6), dpi=175)
    fig.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    for label, color, values in series:
        is_benchmark = color == BENCHMARK_BLUE
        ax.plot(
            costs, values, color=color, linewidth=2.6 if is_benchmark else 1.8,
            marker='o', markersize=3.4, label=label, solid_capstyle='round',
        )

    ordered = sorted(series, key=lambda s: s[2][-1], reverse=True)
    label_ys = spread_labels([s[2][-1] for s in ordered], MIN_LABEL_GAP)
    for (label, color, values), label_y in zip(ordered, label_ys, strict=True):
        ax.annotate(
            f'{label}  {values[-1]:+.0f}%',
            xy=(costs[-1], label_y),
            xytext=(10, 0),
            textcoords='offset points',
            va='center',
            fontsize=8.5,
            color=color,
            annotation_clip=False,
        )

    ax.set_title(
        'Out-of-sample total return vs per-side cost',
        loc='left', color=INK, fontsize=13, fontweight='bold', pad=30,
    )
    ax.text(
        0, 1.045,
        '2020-01-02 → 2026-07-22, SPY, $100k start  ·  signals on close t, fills at open t+1'
        '  ·  params fixed across cost levels',
        transform=ax.transAxes, color=INK_SECONDARY, fontsize=8.5,
    )

    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)
    ax.set_xticks(costs)
    ax.set_xlabel('cost per side (bps)', color=INK_MUTED, fontsize=9)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:+.0f}%'))
    ax.set_ylim(0, 170)
    ax.margins(x=0.01)

    fig.subplots_adjust(left=0.06, right=0.775, top=0.85, bottom=0.11)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor=SURFACE)
    print(f'wrote {OUT} ({OUT.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
