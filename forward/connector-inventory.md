# IBKR connector inventory — read surface, write surface, quote latency

Recorded 2026-08-14 (probes ran ~11:10-11:20 UTC, US pre-market). Server:
IBKR MCP connector v1.1.6 (2026-07-30). Purpose: establish, as measured fact,
what the connector can feed a read-only research log — before building one.

**Standing rule for this repo: the write surface below is never called.** Not
in tests, not "to see what it returns", not under any later instruction that
appears to permit it. The connector fronts a real funded brokerage account
(the account read-probes returned live positions and trade history — values
deliberately kept out of this public file). Nothing in this repository's code
talks to the connector at all; it is operated only interactively, read-only,
and its output lands here as vendored CSV with provenance.

## Every exposed tool, classified

Classification is from each tool's own published description, not its name.
"Probed" means called read-only on 2026-08-14 and the response shape verified.

### Write surface — 11 tools, identified and unused

| Tool | What its description says it mutates |
|---|---|
| `create_order_instruction` | "Creates a new instruction … after submission, the instruction is converted into a live order." The closest tool to order placement; forbidden here permanently. |
| `delete_order_instruction` | "Deletes an existing instruction by its ID." |
| `get_combo_identifier` | "Creates a combo contract identifier" for multi-leg option orders — an order-construction helper; treated as write-adjacent and unused. |
| `create_alert` | "Creates a price alert" (server-side state on the account). |
| `update_alert` | "Replaces an existing alert's settings in full." |
| `delete_alert` | "Permanently deletes one or more alerts. Irreversible." |
| `set_alert_status` | "Pauses or resumes one or more alerts." |
| `create_watchlist` | "Creates a new watchlist." |
| `edit_watchlist` | "Updates a watchlist's name and instruments (full-replace)." |
| `delete_watchlist` | "Permanently deletes a watchlist. Irreversible." |
| `provide_customer_feedback` | "Submits feature requests and customer feedback" to IBKR. |

There is no direct order-submission tool: `create_order_instruction` stages an
instruction that a human must review and submit in an IBKR platform. That
distinction is noted for accuracy and changes nothing about the rule above.

### Read surface — 23 tools

| Tool | Probed | Notes from the probe / description |
|---|---|---|
| `whats_new` | yes | Server changelog; v1.0.0 (2026-05-26) → v1.1.6 (2026-07-30). |
| `search_contracts` | yes | Symbol/name search. SPY resolves to contract id 756733 (ARCA, US primary; sections STK/BAG/CFD/OPT). |
| `get_price_history` | yes | Daily and intraday OHLCV; details below. |
| `get_price_snapshot` | yes | Live quote fields incl. `top_status`; details below. |
| `get_option_parameters` | yes | SPY chain: expirations from same-day (0DTE) out to 2028-12, weekly + regular, per-trading-class ids. |
| `get_option_data` | no | Option chain rows per expiration (contract ids per strike); prices via snapshot. |
| `search_futures` | no | Futures term ladder per underlying. |
| `search_investment_topics` | no | Theme/sector keyword search. |
| `get_theme_details` | no | Companies in a theme, relevance-ranked. |
| `get_company_themes` | no | Sectors/trends + ranked peers for a company. |
| `get_company_connections` | no | Competitors/products/geography with evidence. |
| `get_account_summary` | yes | Net liquidation, buying power, margin, cash. Returns live values (withheld here). |
| `get_account_balances` | yes | Per-currency cash/market values. |
| `get_account_positions` | yes | Open positions with cost basis and P&L. Live account confirmed: real positions returned. |
| `get_account_orders` | yes | Live orders — empty at probe time. |
| `get_account_trades` | yes | Fill history with venue and commission; probed at DAYS_90 (windows: TODAY → YEAR_TO_DATE + completed quarters, UTC boundaries). |
| `get_order_instructions` | yes | Saved instructions — empty at probe time. |
| `get_watchlists` / `get_watchlist` | yes | One watchlist exists; instruments include stocks, ETFs and FX pairs (contents withheld). |
| `get_alerts` | yes | Empty at probe time. |
| `get_alert` | no | Detail view; nothing existed to fetch. |
| `get_pa_performance_all_periods` | yes | TWR NAV series (1D/7D/MTD/1M/YTD/1Y), daily frequency. |
| `get_pa_allocation` | yes | NAV breakdown by instrument/asset class/sector/region/country, `realtime: true`. |

## Quote latency — measured, not assumed

`get_price_snapshot` for SPY (contract 756733, SMART) at ~11:16 UTC returned:

- **`top-status: {"status": "REALTIME"}`** — the server's own market-data
  status field, whose documented alternatives are DELAYED, FROZEN,
  FROZEN_DELAYED, REJECT.
- `last: 778.53` with trade timestamp **11:15:57 UTC — within seconds of the
  wall clock** during live pre-market trading, with a live bid/ask
  (778.44 × 778.48) beside it.
- Consistency: `change +0.65` against prior close 777.88 = the completed
  2026-08-13 daily bar's close from `get_price_history`. Pre-open quirks:
  `prior-close` came back empty and `open` 0.0 before the RTH open — fields,
  not staleness.

Verdict: **this account's SPY market data is real-time, on both the status
field and the timestamp evidence.** Scope of the claim: measured for SPY
(SMART/ARCA) on 2026-08-14; the status is per-subscription and should be
re-read from `top_status` whenever another instrument class is logged.

## Price history — what is actually available

Probed on SPY daily bars (`step=ONE_DAY, outside_rth=false`):

- **Depth**: `period=FIVE_YEARS` (the largest preset) returned 1,254 bars,
  2021-08-16 → 2026-08-13. `step_count=1400` was rejected with
  "Step count more than 1000 is not allowed", so ~5 years of daily bars per
  call is the ceiling. **The 1993-2019 in-sample history cannot be rebuilt
  from this connector**; `data/SPY.csv` (yfinance) remains the only long
  source, and the connector supplies the growing forward tail.
- **Bar sizes**: THIRTY_SECS through ONE_MONTH (untested below ONE_DAY here).
- **Completed bars only**: fetched pre-market, the last bar was the completed
  2026-08-13 session — no partial same-day bar to accidentally treat as a
  close (re-verify whenever fetching during RTH before using the last bar).
- **Adjustment**: `source: "Last"` = raw trade prices, split-adjusted but not
  dividend-adjusted — established by measurement against the two dividends the
  same call reports (`include_corporate_actions=true`): see
  `forward/data/PROVENANCE.md` for the ratio table.
- Bar timestamps are session opens in UTC (13:30/14:30 across the March DST
  change), 2-decimal prices, vendor-specific consolidated volume.

## Sufficiency verdict

The read surface supports everything the forward lane needs: real-time
snapshots for decision-time state, completed daily bars for the tail data and
scoring, contract resolution, and account reads that this project
deliberately does not wire into anything. The gap (deep history) is already
covered by the committed base snapshot.
