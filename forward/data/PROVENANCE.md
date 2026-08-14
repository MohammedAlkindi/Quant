# Provenance: `SPY_tail_ibkr.csv`

Daily OHLCV bars for SPY (SPDR S&P 500 ETF Trust, ARCA, IBKR contract id 756733),
**2026-06-18 -> 2026-08-13**, 39 rows, schema identical to `data/SPY.csv`.

## Fetch

- **Source**: Interactive Brokers via the IBKR MCP connector (server v1.1.6),
  tool `get_price_history`, parameters `contract_id=756733, security_type=STK,
  step=ONE_DAY, outside_rth=false` (`period=SIX_MONTHS` and `period=FIVE_YEARS`
  calls, cross-checked against each other on four spot closes — identical).
- **Fetched**: 2026-08-14 ~11:15 UTC, pre-market. The market-data subscription
  reported `top_status: REALTIME` (not delayed) on the same contract at fetch
  time, and the response contained **no partial bar for 2026-08-14** — the last
  row is the completed 2026-08-13 session.
- Prices arrive with 2 decimal places (`source: "Last"` = trade prices).

## What these bars are — measured, not assumed

IBKR daily bars are **raw trade prices: split-adjusted, NOT dividend-adjusted**.
`data/SPY.csv` (yfinance, `auto_adjust=True`, fetched 2026-07-23) is adjusted
for splits **and** dividends. Verified against the connector's own
`corp_actions` (last two ex-dividends: 2026-06-18 at $1.903516, 2026-03-20 at
$1.796999):

| Window | Predicted csv/ibkr ratio | Measured (ratio, or close error where flagged) | n |
|---|---|---|---|
| 2026-06-18 -> 2026-07-22 (after last ex-div) | 1.0 | max absolute close error **$0.000029** | 23 |
| 2026-03-20 -> 2026-06-17 (one dividend back) | 0.99743101 | 0.99743039 (0.99743030..0.99743045) | 62 |
| 2026-01-02 -> 2026-03-19 (two dividends back) | 0.99471446 | 0.99471380 (0.99471370..0.99471389) | 53 |

The post-ex-div overlap therefore agrees to price-feed rounding, which is what
makes splicing valid **for this window**: no ex-dividend falls between the base
snapshot's last row (2026-07-22) and this file's last row (2026-08-13).
`quant.forward.splice()` re-verifies that overlap on every run and refuses at
a >$0.005 close disagreement.

Rows before 2026-06-18 exist in this file only to feed that overlap check and
to document the adjustment measurement; the spliced series always prefers
`data/SPY.csv` inside the overlap.

## Known seams, quantified

- **Opens differ across vendors by up to $0.07** (~0.9 bps) in the overlap —
  different opening-print conventions. Closes are the signal input and agree to
  $0.000029; opens matter only on a fill. In this tail's window the strategy
  traded once (the window's initial entry), so the seam's effect is bounded by
  ~1 bp on that single fill.
- **Volume differs from yfinance** by a few percent (consolidated-tape scope).
  The engine never reads volume.
- **Dividend seam rule for refreshes**: SPY's next ex-dividend is expected
  ~2026-09-18. A tail that crosses a new ex-div must NOT be spliced — the base
  series no longer carries that dividend's adjustment. At the first refresh
  after any new ex-dividend, re-fetch the full base via `scripts/fetch_data.py`
  and regenerate every golden and documented table together (the procedure
  `docs/backtest.md` already prescribes for data refreshes). The splice guard
  cannot detect this case from the overlap (raw history does not shift), which
  is why it is written down here instead of assumed.
