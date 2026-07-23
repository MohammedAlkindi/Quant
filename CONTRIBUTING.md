# Contributing

The house rule, enforced by review and CI: **no claim outruns the code.** Anything stated
in the README or docs must be traceable to code in the tree or a command a reader can run.
`docs/audit.md` records what happened when v0.1 broke that rule.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; use .venv/bin/activate on Unix
pip install -r requirements.txt   # core API deps
pip install -e ".[dev]"           # quant package + pytest + ruff + matplotlib
cp .env.example .env
```

Optional overlays: `requirements-ml.txt` (FinBERT/PPO/experimental),
`requirements-broker.txt` (Alpaca — read its header, the install is deliberately two-step).

## Before every commit

```bash
ruff check .
pytest
```

Both must be clean — CI runs exactly these on every push and PR. Write the failing test
before the fix or feature; the engine's accounting tests
(`tests/test_backtest.py`) are the model: hand-computed expectations, not
recomputed formulas.

## Commit style

Conventional commits with a scope (`fix(trade): …`, `docs(backtest): …`), one logical
change per commit, staged by explicit file path (never `git add .`). See `AGENTS.md` for
the rules AI agents follow in this repo, including what requires the owner's explicit
confirmation (anything touching the order path, credentials, or pushes).

## Changing reported numbers

The README/backtest tables, `tests/test_report_golden.py`, and
`docs/assets/equity_curve.png` are one atomic unit pinned to `data/SPY.csv`. If you
refresh the data or touch the engine/protocol:

1. `python -m quant.report` — regenerate the table,
2. update the golden constants and both docs tables,
3. `python scripts/plot_equity.py` — regenerate the chart,
4. commit all of it together, stating the cause in the body.

A green golden test on stale prose is still a broken claim — the test exists to make that
loud.

## Scope guardrails

- Nothing promotes out of `experimental/` without real data, seeded training, and
  out-of-sample evaluation through `quant.backtest` — see `experimental/README.md`.
- Live-trading behavior (risk checks, order types, brokers) follows `docs/roadmap.md`
  order — risk layer first. Don't extend the order path ahead of it.
