# Quant v0.1 — code vs. claims audit

Date: 2026-07-23. Scope: every tracked file at commit `b616230`. Method: manual trace of the
signal path (`/signal/predict` → services → `ml/`), the order path (`/trade/execute` → Alpaca),
the training scripts, and a cross-reference of each README claim against the code that would
have to exist for it to be true.

## Verdicts on README claims

| README claim (v0.1) | Verdict | Evidence |
|---|---|---|
| "production-ready MVP" | False | No tests, no CI, no lint config, no error handling on any route, API cannot boot offline (see §6), frontend cannot build (see §5). |
| "LSTM/Transformer forecasting" | False | `ml/models/lstm.py` and `ml/models/transformer.py` are never imported by the backend. The API's `lstm_prediction` field is `close * (1 + momentum * 0.2)` — arithmetic, not a model (`backend/services/signal_service.py:14`). The only LSTM training script fits random noise to random targets (`infra/scripts/train_lstm.py:10-11`). |
| "FinBERT sentiment" | Partial | FinBERT genuinely runs (`ml/sentiment/finbert.py`), but headlines come only from Alpha Vantage; with no API key the score is silently `0.0` for every ticker (`ml/sentiment/news_scraper.py:7-8`, `ml/sentiment/aggregator.py:10`). The model also loads at import time — see §6. |
| "PPO RL" | Partial | Wired (`signal_service.py:15`) but inert: no checkpoint is shipped, so `get_rl_action` always returns `'hold'` (`ml/rl/agent.py:20-22`). If trained, the shipped script trains on an unseeded synthetic random walk (`infra/scripts/train_rl.py:7`), and the env observes raw price levels, so a policy trained at one price scale is meaningless at another (`ml/rl/env.py:24-27`). |
| "anomaly detection" | Partial | Implemented as a z-score of the latest price against the 3-month mean plus an IsolationForest refit per request on 1-D price levels (`ml/anomaly/detector.py:9-13`). With `contamination=0.05`, range extremes are flagged by construction — fresh 3-month highs read as "anomalies" and halve the signal score (`signal_service.py:20-21`), damping exactly the states a momentum signal needs. |
| "Polygon + yfinance + Alpha Vantage with Redis caching" | Partial | All three clients exist. Caching covers only `/quote` with a 5 s TTL (`backend/services/market_service.py:18-29`); the history calls used by the signal path are uncached (`market_service.py:31-32`). |
| "Anthropic Claude for explainable recommendations" | True | `backend/llm/client.py` calls the configured model; `config.py:22` matches the README's model ID. Parsing is a greedy regex over the reply (`backend/llm/parser.py:6`), and `/explain` forwards an arbitrary client-supplied dict into the prompt (`backend/api/routes_llm.py:27-29`). |
| "dashboard-based execution" | False | React sources exist, but no `package.json`, lockfile, `index.html`, or Vite config is tracked — `docker-compose`'s `npm install && npm run dev` cannot succeed. The trade panel also hardcodes `confirmed: true` (`frontend/src/components/TradePanel.jsx:10`), defeating the API's only order gate. |
| "`POST /api/trade/execute` (requires `confirmed=true`)" | True but hollow | The flag is checked (`backend/services/trade_service.py:12-13`) and auto-set by the UI. It is the only check — see §4. |
| "LSTM/Transformer consume 60-day rolling OHLCV + technical features" | False | The feature pipeline (`ml/features/pipeline.py`) is imported by nothing. The training data is `torch.randn(points, 60, 8)` (`infra/scripts/train_lstm.py:10`). No script trains the Transformer at all. |
| "RL environment uses discrete actions and Sharpe-like reward" | True | `ml/rl/env.py:12,38-39`. The reward is the running Sharpe of all returns so far, recomputed each step, with no transaction costs. |
| "Checkpoints are saved to `ml/models/checkpoints/`" | True for the scripts | No checkpoint is tracked, so a fresh clone has no trained artifacts. |
| API endpoint list | True | All nine routes exist and are mounted (`backend/main.py:23-26`). |

## 1. What the signal function actually computes

`SignalService.predict` (`backend/services/signal_service.py`):

1. `momentum` = return between the last close and the close 4 trading sessions earlier
   (`close[-1]/close[-5] - 1`, line 13).
2. `lstm_prediction` = `close[-1] * (1 + momentum * 0.2)` (line 14). The name is false; no
   neural network is involved anywhere in the request path.
3. `score = 0.4·tanh(3·momentum) + 0.3·sentiment + 0.3·rl_vote`, halved if the anomaly flag
   is set (lines 19-21). BUY above +0.2, SELL below −0.2 (line 23).
4. `confidence = clip(|score|, 0.5, 0.99)` (line 24) — a clamped score magnitude, not a
   calibrated probability. Any HOLD reports "confidence 0.5".

In the default deployment (no Alpha Vantage key, no PPO checkpoint), sentiment = 0 and
rl_vote = 0, so the entire system reduces to `0.4·tanh(3·momentum)` against a ±0.2 threshold:
it emits BUY only when the 4-session return exceeds ~+18.3 % and SELL below ~−18.3 %.
Outside single-name crashes, the product recommends HOLD at confidence 0.5 forever.

## 2. Model components: wired vs. dead

| Component | Modules | In live path? | Notes |
|---|---|---|---|
| LSTM | `ml/models/lstm.py`, `trainer.py` | No | Referenced only by `infra/scripts/train_lstm.py`, which trains on `torch.randn`. |
| Transformer | `ml/models/transformer.py` | No | Imported by nothing. Never trained, never loaded. |
| PPO | `ml/rl/agent.py`, `env.py` | Yes, inert | Loads a checkpoint that does not exist → constant `'hold'`. `PPO.load` from disk on every request if it did (agent.py:23). |
| FinBERT | `ml/sentiment/*` | Yes | Loads ~440 MB at import time; silently returns 0.0 without an Alpha Vantage key. |
| IsolationForest + z-score | `ml/anomaly/detector.py` | Yes | Refit per request; flags range extremes as anomalies. |
| Feature pipeline | `ml/features/*` | No | `build_feature_matrix` has zero call sites. |
| Alert models | `ml/anomaly/alerts.py` | No | Pydantic classes with zero references. |

## 3. Backtest

`ml/rl/backtest.py` is the only backtest in the repo (14 lines):

- No commissions, no bid-ask spread, no slippage, no borrow cost on shorts.
- Position from action at bar *i−1* is applied to the *i−1 → i* close-to-close return —
  i.e., execution at the same close the signal was derived from.
- Unlimited free short-selling (`position = -1`).
- Reports ending equity and max drawdown only; no Sharpe, no turnover, no benchmark.
- Zero call sites in the repo (the "RL backtest" notebook is an empty shell — §5).

Verdict: the repo contains no cost-aware backtest and no evidence any strategy was ever
evaluated against a benchmark.

## 4. Order path and risk checks

`/trade/execute` (`backend/api/routes_trade.py` → `backend/services/trade_service.py`) submits
a live market order to Alpaca (line 15) after checking exactly one thing: the `confirmed`
boolean — which the shipped UI hardcodes to `true`.

Not checked before an order reaches the broker: buying power, position or notional limits,
max order size (any `qty > 0` passes), symbol validity, side validity (`side` is an arbitrary
string passed through), duplicate submission / idempotency, market hours. There is no
authentication on any endpoint, and nginx publishes the API on port 80
(`infra/nginx/nginx.conf`), so anyone who can reach the host can trade.

The `stop_loss` in the response is computed *after* the entry order from the latest trade
price and **is never submitted as an order** (`trade_service.py:17-19`). Nothing is persisted
either — the `trades` table exists but no code writes to it (§5). Mitigating: the default
`ALPACA_BASE_URL` is the paper endpoint (`backend/config.py:20`).

## 5. Dead code and phantom infrastructure

- **Database layer**: `backend/db/models.py` + Alembic migrations define three tables; no
  engine, session, or query exists anywhere in application code (only Alembic's own `env.py`
  imports the models). Postgres runs in compose purely to satisfy a required-but-unused
  `POSTGRES_URL` setting (`config.py:13`).
- **Frontend build**: no `package.json`, no lockfile, no entry HTML, no bundler config.
  `useWebSocket.js` targets a WebSocket endpoint the backend does not have; `client.js`
  attaches a bearer token no backend route ever checks.
- **Notebooks**: all four are single-markdown-cell shells. No code, no outputs. The names
  ("LSTM Research", "RL Backtest", "Sentiment Evaluation") imply research that does not exist.
- **`infra/scripts/seed_data.py`**: writes `data_seed/*.json` that nothing reads.
- **`ml/features/`, `ml/anomaly/alerts.py`**: unreferenced (§2).

## 6. Operational and reproducibility defects

- **The API cannot boot without downloading FinBERT.** `backend/main.py` → `routes_signal` →
  `signal_service` → `ml.sentiment.finbert`, which calls `from_pretrained` at module level
  (`finbert.py:4-6`). First start requires internet, torch, transformers, and ~440 MB of
  weights — to serve `/healthz`.
- The full ML stack (torch, transformers, stable-baselines3) is a hard install dependency of
  the web API; `requirements.txt` is one flat list.
- `docker-compose.yml` pip-installs that list on every container start (line 8) and injects
  `.env.example` — the empty-key file — as the runtime environment (lines 9-10). No Dockerfile.
- No tests, no CI, no linter. No seed management: `train_rl.py` and `train_lstm.py` are
  unseeded; results are unreproducible even at their (synthetic) tasks.
- No error normalization anywhere: any yfinance/Redis/Alpaca/Anthropic failure surfaces as a
  raw 500.
- `alpaca-trade-api` is the deprecated SDK (superseded by `alpaca-py`).
- Verified during this audit: a fresh install of the v0.1 pins cannot boot at all —
  `anthropic==0.35.0` passes `proxies=` to httpx, which pip resolves to ≥0.28 (the pin list
  omits transitive deps), raising `TypeError` at import. Fixed on this branch by pinning
  `httpx==0.27.2`.
- Also verified: with empty Alpaca keys, `tradeapi.REST('')` raises `ValueError` while
  `routes_trade` is imported (`trade_service.py:9` at v0.1) — so a keyless v0.1 deployment
  could not boot even with the FinBERT download available. Fixed on this branch by
  constructing the client on first use.

## 7. What is genuinely sound

- Clean route → service → data-client layering; secrets only via `pydantic-settings` and
  `.env` (untracked); example env has empty keys; pinned `requirements.txt`; Alpaca defaults
  to the paper endpoint; the confirmation flag exists (even if the UI defeats it); the
  endpoint list in the README is accurate.

## Disposition for v0.2

The v0.2 branch removes the false claims from the README, quarantines the unwired model code
under `experimental/` with its status labeled, adds lint/test/CI foundations, and replaces
the 14-line cost-free backtest with a cost-aware engine evaluated out of sample against SPY.
Live execution and the broker path are out of scope for v0.2 and are documented as unsafe
for real keys until risk checks exist.
