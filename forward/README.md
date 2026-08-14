# Forward lane — the frozen strategy on data nobody has seen

One question, asked honestly: **does the system beat doing nothing on data
that did not exist when its parameters were chosen?** The committed backtest
already says buy-and-hold won its window (+155.26% vs +94.60%,
`docs/backtest.md`). This lane keeps asking on bars that postdate every
committed decision, with nothing tunable left to touch.

## The three windows — kept distinct

| Window | Range | Status |
|---|---|---|
| In-sample | 1993-01-29 → 2019-12-31 | Used once, to pick 10/200 from a 3×3 grid. |
| Seen out-of-sample | 2020-01-02 → 2026-07-22 | The committed backtest's evaluation window. Honest, but **looked at** — its result is known and quoted; nothing about it is a forward claim anymore. |
| Forward | 2026-07-23 → last committed tail bar | Bars fetched after the snapshot was frozen. Genuinely unseen at parameter-choice time and at snapshot time. Grows with each refresh. |

## Standing result — 2026-08-14, 16 bars

```
strategy                total return     cagr  sharpe   max dd  turnover/yr     costs  trades
---------------------------------------------------------------------------------------------
SPY buy & hold                +5.31% +138.34%    6.45   -1.54%       15.37x       20       1
MA cross 10/200               +5.31% +138.34%    6.45   -1.54%       15.37x       20       1
```

Reproduce with `python -m quant.forward`; pinned to the committed data by
`tests/test_forward_golden.py`. Read it straight: no cross fired in the
window, the strategy was long on every bar, so it and the benchmark are the
same portfolio down to the fill. **16 daily bars support no conclusion in
either direction** — the annualized columns are format compatibility, not
information. The lane's value arrives with accumulation, and its first real
test is the next cross.

## What lives here

- `data/SPY_tail_ibkr.csv` + `data/PROVENANCE.md` — vendored IBKR daily tail
  and the measurements behind it (raw-vs-adjusted, seam checks, fetch facts).
- `connector-inventory.md` — the IBKR connector's read/write surface, probed
  2026-08-14; the write tools are named and permanently unused.
- `decisions/` — the pre-registered decision log. Append-only; contract in
  `decisions/README.md`. Scored by `python -m quant.scoring`.
- `ASSESSMENT.md` — what this design can and cannot detect, and on what
  timescale.

No code in this repository calls IBKR or any broker. The tail is fetched
read-only, interactively, and committed as data with provenance — the
research lane stays offline and deterministic (`quant/` rules in
`CLAUDE.md`), and the roadmap's "no IBKR integration" stands: vendored bars
are data, not an integration.

## Refresh procedure (extending the forward window)

1. Fetch fresh daily bars for SPY read-only (completed sessions only — drop
   any partial same-day bar; note `top_status` at fetch time).
2. **If any new SPY ex-dividend has occurred since `data/SPY.csv` was
   fetched** (next expected ~2026-09-18): do not splice across it. Re-fetch
   the base with `python scripts/fetch_data.py`, then rebuild the tail from
   the new last base row, and regenerate the *backtest* goldens and tables
   too, per `docs/backtest.md`'s refresh caveat.
3. Otherwise: extend `data/SPY_tail_ibkr.csv` with the new completed bars
   (keep the existing overlap rows; `quant.forward.splice` re-verifies the
   seam on every run and refuses on disagreement).
4. `python -m quant.forward`, update `tests/test_forward_golden.py` constants
   and every documented forward table together, one commit —
   `CONTRIBUTING.md`'s atomic-unit rule applies to forward numbers exactly as
   it does to backtest numbers.
5. `python -m quant.scoring` — entries whose horizons have elapsed move from
   pending to scored. Never touch `decisions/` in a refresh commit.

## Rules that keep this worth doing

- **Parameters stay frozen at 10/200.** No re-selection, no threshold nudges,
  no cost-model softening — nothing changes because forward results were
  seen. A strategy change is a new lane: new directory, new start date, its
  own log, stated as such. `tests/test_forward.py` trips on grid-selection
  code reappearing in `quant/forward.py`.
- **A losing forward result is a successful run.** The lane measures; it does
  not advocate. Nothing here is investment advice — it records what a stated
  rule would have done at nominal size.
- **`decisions/` is append-only** — the full contract, including the no-amend
  / no-rebase / no-squash requirement that protects commit-date
  pre-registration, is in `decisions/README.md`.
