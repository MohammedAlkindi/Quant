# Quant — project context

Personal trading scaffold. Audience includes quant-firm readers: **never let a claim outrun
the code**. `docs/audit.md` is the standing record of what v0.1 got wrong; do not reintroduce
those patterns.

## Stack

- `backend/` — FastAPI service (Python 3.11+). Heuristic signal, market data, Alpaca paper
  calls, Claude commentary. Boots keyless without the ML stack.
- `quant/` — research package: seeds, cost-aware backtest, baseline strategies, metrics.
  Pure functions, deterministic, no network at runtime (reads vendored CSV data).
- `ml/` — the pieces actually wired into the signal path (anomaly, RL hook, FinBERT).
- `experimental/` — quarantined, unvalidated code. Never import it from live paths.
- `frontend/` — React sources only; **not buildable** (no package.json). Don't pretend otherwise.

## Commands

```bash
pytest                    # all tests (venv: .venv)
ruff check .              # lint
python -m quant.report    # reproduce the baseline backtest + metrics
python -m quant.forward   # frozen baseline on the post-snapshot forward window
python -m quant.scoring   # score the pre-registered decision log (forward/decisions/)
```

## Rules

- Virtual environment always; deps pinned in `requirements*.txt`, tooling in `pyproject.toml`.
- Heavy deps (torch, transformers, stable-baselines3) must stay lazy imports and out of core
  requirements.
- The trade path has **no pre-trade risk checks** — documented in the README. Do not extend
  live-trading behavior without being explicitly asked.
- Backtests must charge costs (commission, spread, slippage) and execute with delay; any
  reported metric must be reproducible by one command.
- `forward/decisions/` is append-only pre-registration: never edit, delete, or reorder an
  entry, never amend or rebase that directory, never squash-merge a branch carrying
  entries. Forward results never drive a parameter change (`forward/README.md`).
- README claims are verified before commit; if code and README disagree, fixing the README
  is part of the change.
