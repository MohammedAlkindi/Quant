# experimental/

Code that is **not part of any working path** and makes **no performance claims**. It was
written during the v0.1 scaffold, was never wired into the API, and is kept here so its
status is unambiguous. See `docs/audit.md` for the full audit that led to this quarantine.

Nothing in this directory is imported by `backend/`, `ml/`, or `quant/`. It is excluded from
the test suite and carries no expectation of correctness. Running it requires the heavy ML
stack (torch, transformers, stable-baselines3), which is intentionally not part of the core
install.

| Item | What it actually is | Known defects |
|---|---|---|
| `models/lstm.py`, `models/transformer.py` | Untrained network definitions. Never imported by the API; the API's former `lstm_prediction` field was arithmetic, not inference. | No data pipeline feeds them real features. |
| `models/trainer.py` | Generic torch training loop. | Unseeded. |
| `scripts/train_lstm.py` | "Training" script whose dataset is `torch.randn` — random noise fit to random targets. | Produces a checkpoint that has learned nothing. |
| `scripts/train_rl.py` | Trains PPO on an unseeded synthetic random walk. | The env (`ml/rl/env.py`) observes raw price levels, so the policy does not transfer across price scales. |
| `scripts/seed_data.py` | Dumps yfinance history to `data_seed/*.json`. | No code reads the output. |
| `features/` | pandas-ta feature pipeline (`build_feature_matrix`). | Zero call sites. |
| `alerts.py` | Pydantic alert models. | Zero references. |
| `rl_backtest.py` | 14-line close-to-close backtest. | No commissions, spread, slippage, or borrow cost; free unlimited shorting; superseded by `quant/backtest`. |

Promotion path: anything here graduates only with a real data pipeline, seeded training,
out-of-sample evaluation through `quant/backtest`, and tests.
