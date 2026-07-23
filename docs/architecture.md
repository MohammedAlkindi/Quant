# Architecture

![Architecture diagram](assets/architecture.svg)

Three lanes, one quarantine. The boundaries exist to keep one property intact: **nothing in
a live or reported path can claim more than the code beneath it does.**

## `backend/` — the serving lane

FastAPI service: `api/` routes delegate to `services/`, which own all external I/O
(`data/` clients for yfinance/Polygon/Alpha Vantage, Redis, the Alpaca REST client, the
Anthropic client). Routes never touch a data provider directly.

Why the boundary: providers are optional and key-gated. The service boots and serves with
zero keys — signal quality degrades (sentiment 0.0, RL vote `hold`) instead of the process
failing. Heavy SDKs load lazily so torch, transformers, stable-baselines3, and the broker
SDK are never boot dependencies (`requirements-ml.txt` / `requirements-broker.txt` are
opt-in overlays; the broker overlay exists because the deprecated Alpaca SDK's `websockets`
pin conflicts with modern yfinance — see the file header).

### Endpoints

| Endpoint | What it does |
|---|---|
| `GET /api/prices/{ticker}` | 30 days of candles (Polygon if keyed, else yfinance) + fundamentals if keyed |
| `GET /api/quote/{ticker}` | Latest price; Redis-cached 5 s |
| `GET /api/history/{ticker}` | yfinance OHLCV (auto-adjusted) |
| `POST /api/signal/predict` | Heuristic signal (below) |
| `GET /api/anomaly/{ticker}` | Runs the signal pipeline, returns the anomaly flags |
| `POST /api/trade/execute` | Alpaca paper market order behind `confirmed=true` — no other checks; see the README warning |
| `GET /api/portfolio` | Alpaca equity, cash, positions |
| `POST /api/analyze`, `POST /api/explain` | Claude commentary on a context dict |

Errors are not normalized yet: upstream failures surface as raw 500s
([roadmap](roadmap.md)).

### Environment

`POSTGRES_URL` and `REDIS_URL` are required by the settings model (`.env.example` values
work; Postgres is never contacted, Redis only on `/quote`). `POLYGON_API_KEY`,
`ALPHA_VANTAGE_API_KEY`, `ALPACA_API_KEY`/`ALPACA_SECRET_KEY`/`ALPACA_BASE_URL`, and
`ANTHROPIC_API_KEY`/`CLAUDE_MODEL` unlock their respective endpoints; everything else
degrades gracefully without them.

## `ml/` — signal components wired into the API

What `POST /api/signal/predict` actually computes from ~3 months of daily closes:

```
momentum = close[-1] / close[-5] - 1            # return over the last 4 sessions
score    = 0.4·tanh(3·momentum) + 0.3·sentiment + 0.3·rl_vote
score    = score / 2 if anomaly flagged
signal   = BUY if score > 0.2, SELL if score < -0.2, else HOLD
```

`confidence` is `clip(|score|, 0.5, 0.99)` — a clamped magnitude, not a calibrated
probability. The anomaly gate is a z-score of the latest close against the 3-month mean
plus a per-request IsolationForest on price levels, which flags fresh range extremes by
construction — it damps exactly the strong-momentum states. In a keyless deployment
sentiment and the RL vote are both 0, so the system reduces to a momentum threshold that
practically always says HOLD. All of this is tested (`tests/test_signal_service.py`), and
no predictive value is claimed for it.

Why the boundary: these components are *wired but honest* — FinBERT runs only with an
Alpha Vantage key, the PPO hook only if a checkpoint exists (none ships). Keeping them in
`ml/` (rather than `experimental/`) marks the line between "runs in the live path" and
"exists as unvalidated code."

## `quant/` — the research lane

`data` (validated CSV loader) → `strategies` (target weights) → `backtest` (cost-aware
engine) → `metrics` (pure portfolio math) → `report` (protocol + CLI). Offline by design:
it reads the committed `data/SPY.csv` snapshot, uses no network, and has no randomness —
`python -m quant.report` reproduces the README table bit-for-bit, and a golden test pins
those numbers in CI.

Why the boundary: reported numbers must be reproducible by a reader, offline, from a clean
clone. Serving code changes for product reasons; research code changes only with its
methodology ([docs/backtest.md](backtest.md)). Keeping the engine free of I/O also keeps
every accounting rule unit-testable against hand-computed fixtures.

## `experimental/` — the quarantine

Unvalidated model code with zero call sites (LSTM/Transformer definitions, a feature
pipeline, RL training on synthetic data, the old cost-free backtest). Its
[README](../experimental/README.md) lists each item's known defects, and its graduation
path runs through the research lane: real data, seeded training, out-of-sample evaluation
via `quant.backtest`, tests.

## Known-dead infrastructure

Kept deliberately visible rather than half-wired: the Postgres schema + Alembic migration
(no application reads or writes), and `frontend/src` (React sources with no build
scaffolding — not runnable). Both are decision points on the [roadmap](roadmap.md), and
the [v0.1 audit](audit.md) records how they got here.
