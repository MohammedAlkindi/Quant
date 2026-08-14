# Cost study — pre-registered protocol

Registered: 2026-08-14, **before any grid cell was computed**. The commit that adds this
file is the pre-registration proof. If a strategy later turns out mis-specified, a dated
correction entry is appended under *Corrections* — the original text is never edited.

## Question

For each of a set of commonly recommended retail trading strategies on SPY: **at what
per-side transaction cost does its out-of-sample result stop beating buy-and-hold?**

The contribution is one number per strategy — the break-even cost — not a return table.
A study in which every strategy loses is a successful study. Nothing here will be tuned
to produce a winner.

## Engine (unmodified)

`quant.backtest.run_backtest`, exactly as shipped in v0.1.0:

- A target weight decided on bar *t*'s close fills at bar *t+1*'s **open**. Nothing
  trades on the bar whose close produced the signal.
- One-way drag = `(commission_bps + half_spread_bps + slippage_bps) / 1e4` of the fill;
  buys fill at `open*(1+drag)`, sells receive `open*(1-drag)`.
- Trades only on target-weight changes; long-only, unlevered, fractional shares;
  equity marked at each close.
- `annual_turnover` = summed absolute traded notional / average equity / years. **Both
  legs of a round trip are counted**, so annual cost drag ≈ turnover × cost-per-side —
  with no further factor of two.

The fill model, delay, and accounting are not modified by this study. Cost levels are
expressed as `CostModel(commission_bps=0, half_spread_bps=0, slippage_bps=c)`; the
engine uses only the sum, so `c = 2` is drag-identical to the repo default
`CostModel(0.5, 0.5, 1.0)`.

## Data

`data/SPY.csv` — daily OHLCV, dividend/split-adjusted, 1993-01-29 → 2026-07-22,
8,426 rows (provenance: `docs/backtest.md`). **Single instrument: every conclusion in
this study is about SPY and claims nothing beyond it.**

## Windows

Repo discipline, unchanged:

- **In-sample (selection only):** 1993-01-29 → 2019-12-31.
- **Out-of-sample (all reported metrics):** 2020-01-02 → 2026-07-22.
- Signals warm up on full history; the OOS backtest starts fresh at $100,000, so every
  strategy (including buy-and-hold) pays its opening fill inside the OOS window.

## Cost levels

Per side, in bps: **0, 1, 2, 5, 10, 20.** The engine accepts any non-negative level;
these six bracket free trading, the repo's 2 bps reference, and expensive retail.

## Parameter-selection rule (one rule, every strategy)

For each strategy, grid-search its pre-specified grid below **on the in-sample window
only**, scored by net in-sample Sharpe at the reference cost of **2 bps/side**,
deterministic iteration order, strictly-greater comparison (ties keep the first entry).
The selected parameters are then **held fixed across all six cost levels** out of
sample.

Rejected alternative: re-selecting parameters at each cost level. That would change the
trading rule along the cost axis; the study isolates the effect of cost on one fixed
rule. Where a recommendation's canonical parameters are themselves the specification,
the grid is that singleton and no search occurs.

## Strategies

All emit daily target weights in {0.0, 1.0} decided on bar *t*'s close from data through
bar *t* only. Monthly rules decide at each month-end close and hold through the next
month. Warm-up bars (any indicator still undefined) emit weight 0.0; warm-up completes
decades before the OOS window. EMAs use `ewm(span=n, adjust=False)`; Wilder smoothing
uses `ewm(alpha=1/n, adjust=False)` on gains/losses; rolling std uses ddof=0 (population,
per Bollinger). "Total return over n months" uses the adjusted close ratio.

| # | Key | Rule (long / flat) | Grid | Source |
|---|---|---|---|---|
| 1 | `ma_cross` | SMA(fast) > SMA(slow) → long, else flat | fast {10, 20, 50} × slow {100, 150, 200} (the repo's existing grid) | Golden-cross family; Brock, Lakonishok & LeBaron (1992), *J. Finance*, variable-length MA rules |
| 2 | `price_vs_sma` | close > SMA(n) → long, else flat | n {50, 150, 200} | BLB (1992) VMA rules with the short leg = price (their 1-50, 1-150, 1-200); the retail "200-day rule"; Siegel, *Stocks for the Long Run*, tests the 200-day variant |
| 3 | `faber_tma` | At month-end: long iff monthly close > SMA of the last n monthly closes (incl. current); hold one month | n {8, 10, 12} months | Faber (2007), *J. Wealth Management*, "A Quantitative Approach to Tactical Asset Allocation" (canonical n=10) |
| 4 | `tsmom` | At month-end: long iff trailing n-month total return > 0; hold one month | n {6, 9, 12} months | Moskowitz, Ooi & Pedersen (2012), *JFE*, "Time Series Momentum" (12m canonical); Antonacci (2014), absolute momentum. Adaptation: rf=0 (repo convention), so "excess of cash" becomes "above zero" |
| 5 | `rsi2` | Enter long when Wilder RSI(2) < threshold AND close > SMA(200); exit when close > SMA(5); else hold prior state | threshold {5, 10} | Connors & Alvarez (2009), *Short Term Trading Strategies That Work* |
| 6 | `macd` | EMA(12) − EMA(26) > its EMA(9) signal → long, else flat | singleton (12, 26, 9) | Appel (2005), *Technical Analysis: Power Tools for Active Investors*; Murphy (1999) textbook treatment |
| 7 | `bollinger_mr` | Enter long when close < SMA(20) − 2·σ(20); exit when close ≥ SMA(20); else hold prior state | singleton (20, 2.0) | Bollinger (2001), *Bollinger on Bollinger Bands*; Murphy (1999) |
| 8 | `donchian` | Long when close > max(high of prior N bars); flat when close < min(low of prior M bars); else hold prior state | (N, M) {(20, 10), (55, 20)} | Donchian channels; Turtle rules, Faith (2007), *Way of the Turtle*. Adaptation: entries/exits on the daily close (the engine cannot fill intraday breakouts) |
| 9 | `halloween` | Weight 1.0 in Nov–Apr, 0.0 in May–Oct, by calendar month of the bar | singleton | Bouman & Jacobsen (2002), *American Economic Review*, "The Halloween Indicator". Fill mechanics lag entry/exit by one trading day (engine delay), immaterial at a 6-month hold |

Nine strategies, seventeen in-sample grid variants. Trend/momentum: 1, 2, 3, 4, 6, 8.
Mean reversion: 5, 7. Calendar: 9.

## Reported per grid cell

Total return, CAGR, Sharpe (rf=0, 252), max drawdown, turnover/yr, costs paid ($ on
$100,000), trade count — via the existing `quant.metrics`. **Buy-and-hold on SPY over
the identical window at the identical cost level appears beside every cell.**

## Break-even definition

edge(c) = strategy OOS total return − buy-and-hold OOS total return, both at cost c.

- If edge(0) ≤ 0: **no break-even exists** — the strategy loses to buy-and-hold even at
  zero cost, and costs are not why it fails.
- Else the break-even is the c where edge crosses 0, **linearly interpolated** between
  the bracketing grid levels (and disclosed as interpolated).
- If edge(20) > 0: reported as "> 20 bps", with the multiple-comparisons caveat attached.

## What would make this study wrong (pre-registered)

1. **Look-ahead** — a signal reading the bar it acts on. Mitigation: the engine
   structurally delays fills; each weight function will additionally be audited for
   window alignment (traced, not assumed).
2. **Parameter contamination** — any parameter chosen on data from the reported window.
   Mitigation: grids and the selection rule are fixed in this file before any run;
   selection touches in-sample data only. The OOS window has also been *seen* by prior
   repo work (the 10/200 result), so it is not virgin data; no specification in this
   file was written in response to any OOS number, but the reader should know the
   window's history.
3. **Multiple comparisons** — 9 strategies × 6 cost levels (plus 17 selection variants)
   ≈ 54 reported comparisons. If one strategy beats buy-and-hold somewhere, that is
   roughly what chance produces. Any positive result carries this caveat inline.
4. **Survivorship / single instrument** — SPY only, and SPY is itself the survivor
   benchmark. The study cannot and does not generalise beyond it.
5. **Regime dependence** — the OOS window (2020-01 → 2026-07) contains the COVID crash,
   the 2020–21 stimulus bull, the 2022 hiking bear, and the 2023–26 AI-led bull: net
   strongly upward. Timing rules that exit the market are structurally disadvantaged in
   such a window; a strategy failing here might not fail in every regime.
6. **Adjusted-price anachronism** — signals use today's back-adjusted series; the
   adjusted series available in real time at bar *t* would differ (adjustment factors
   change at each distribution). Standard practice, identical for all strategies and
   the benchmark, but named.
7. **Post-hoc respecification** — any strategy whose spec changes after a result is
   seen. Mitigation: corrections are append-only, below.

## Temptation log

(Empty at registration. Any urge to tune after seeing a result gets logged here instead
of acted on.)

## Corrections

- **2026-08-14 (same day, before results were recorded):** the registration text says
  "seventeen in-sample grid variants" and "(plus 17 selection variants)". The grids
  enumerated in the strategy table sum to **25** (9 + 3 + 3 + 3 + 2 + 1 + 1 + 2 + 1) —
  the 17 was an arithmetic slip in the prose. No grid, rule, or specification changed;
  the enumerated table is authoritative. Caught by
  `tests/test_cost_study.py::test_every_registered_grid_is_nonempty_and_pre_registered_size`.
