# Backtest methodology

Everything reported in the README reproduces from committed data with:

```bash
python -m quant.report
```

## Data

- **Source**: Yahoo Finance daily OHLCV via yfinance 1.5.1, `auto_adjust=True` — prices
  adjusted for splits **and dividends**, so buy-and-hold on `close` approximates total
  return. Fetched 2026-07-23 by `scripts/fetch_data.py`.
- **Range**: SPY, 1993-01-29 → 2026-07-22 (8,426 rows), committed at `data/SPY.csv` so
  runs are offline and deterministic.
- **Caveat**: dividend adjustment is retroactive. Refetching after new dividends shifts
  the whole adjusted history, and therefore every number below. The golden test
  (`tests/test_report_golden.py`) pins the reported numbers to the committed snapshot; a
  data refresh must regenerate the README table, the golden constants, and the equity
  chart together.

## Protocol

- **In-sample**: everything before 2020-01-01, used *only* to pick the MA pair from a
  fixed 3×3 grid (fast ∈ {10, 20, 50}, slow ∈ {100, 150, 200}) by net Sharpe → 10/200.
- **Out-of-sample**: 2020-01-02 → 2026-07-22. No parameter, threshold, or design choice
  was revisited after looking at this window.
- **Warm-up**: MA state at the OOS boundary is computed from full history — being long on
  2020-01-02 because fast MA > slow MA through 2019 is information that genuinely existed
  on 2019-12-31.
- **Benchmark**: SPY buy-and-hold *through the same engine and costs*. The strategy trades
  SPY itself, so holding SPY is the only honest benchmark; running it through the engine
  (rather than quoting raw index return) makes the comparison symmetric — same entry
  timing, same cost model.

## Execution and cost model

A target weight decided on bar *t*'s close fills at bar *t+1*'s **open** — nothing ever
trades on the bar that produced its signal. Long-only, unlevered, fractional shares,
$100,000 initial equity.

| Cost component | Value | Rationale |
|---|---|---|
| Commission | 0.5 bps/side | above typical per-share retail commission on SPY at ~$500+ |
| Half bid-ask spread | 0.5 bps/side | SPY's penny spread is ~0.2 bps; rounded up |
| Slippage | 1.0 bps/side | conservative for small market-on-open orders in SPY |
| **Total drag** | **2.0 bps/side** | |

Buys fill at `open × (1 + drag)` and are sized against that fill (cash can never go
negative); sells fill at `open × (1 − drag)`. The engine trades only when the target
weight changes. Accounting is tested against hand-computed fixtures in
`tests/test_backtest.py`.

## Results (out of sample, 2020-01-02 → 2026-07-22)

| Strategy | Total return | CAGR | Sharpe (rf=0) | Max drawdown | Turnover/yr | Costs paid | Trades |
|---|---|---|---|---|---|---|---|
| SPY buy & hold (benchmark) | +155.26% | +15.44% | 0.81 | −33.72% | 0.10× | $20 | 1 |
| MA crossover 10/200 | +94.60% | +10.74% | 0.83 | −20.51% | 1.88× | $337 | 13 |

The crossover underperforms buy-and-hold on total return and wins on drawdown — the
standard trend-following tradeoff over a mostly-rising window. **No alpha is claimed.**
Sharpe uses rf=0 (disclosed, not hidden — with 2020-26 T-bill rates above zero, both
Sharpes are overstated by the same construction).

## Known limitations

Single instrument, single OOS window, no taxes, no borrow (long-only by construction),
grid limited to 9 canonical pairs, costs modeled in bps rather than order-book depth, and
Sharpe at rf=0. These are disclosed bounds, not fine print.

## Reproduce

```bash
pytest tests/test_report_golden.py   # asserts the table above against data/SPY.csv
python -m quant.report               # prints the table
python scripts/plot_equity.py        # regenerates docs/assets/equity_curve.png
python scripts/fetch_data.py         # optional refresh — see the caveat above
```
