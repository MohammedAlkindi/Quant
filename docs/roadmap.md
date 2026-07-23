# Roadmap

Direction: the repo description ("cost-aware backtesting, deterministic risk controls,
broker-independent execution") names where this is headed. As of v0.1.0 the first clause
is built; risk controls and broker-independence are roadmap items below, not shipped
features. This file is the honest ledger of that gap.

## Next — in rough order

1. **Error normalization at the API boundary.** Today any upstream failure is a raw 500.
   One exception handler, typed error payloads, no stack traces to clients.
2. **Risk layer before any order path grows.** Position and notional caps, buying-power
   check, symbol/side validation, idempotency keys, and a *real* stop order placed with
   the broker (today's `stop_loss` response field is informational only). Deterministic
   and unit-tested, in the spirit of `quant/` — this is the "deterministic risk controls"
   the description promises, and it gates everything in the out-of-scope list.
3. **Auth on mutating endpoints.** `/trade/execute` is currently open to anyone who can
   reach the host.
4. **Persistence: wire it or drop it.** The Postgres schema and migration exist with zero
   readers/writers. Either signals and trades get recorded (useful for audit trails) or
   the schema leaves the tree.
5. **Broker abstraction.** Replace the deprecated `alpaca-trade-api` (and its `--no-deps`
   overlay workaround) with a thin execution interface + `alpaca-py` as the first
   implementation — the path to "broker-independent execution."
6. **Frontend: build it or remove it.** `frontend/src` has no build scaffolding. Decide,
   then make the tree match the decision.
7. **Observability.** Structured logs and basic request/latency metrics for the API.
8. **Strategy research, gated.** New strategies (including anything graduating from
   `experimental/`) must beat the baselines in `docs/backtest.md` out of sample, net of
   costs, through the same engine — before any claim lands in a README.

## Explicitly out of scope

- **Live trading with real money** — out of scope until items 1–3 exist and are tested.
  The paper endpoint is the ceiling for now.
- **IBKR integration.**
- **New ML models in the live path** — nothing promotes out of `experimental/` without
  real training data, seeded runs, and out-of-sample evaluation through `quant.backtest`
  (see `experimental/README.md`).
- **Intraday data, multi-asset portfolios, tax/dividend cash-flow modeling** — the
  single-asset daily baseline stays the reference until the layers above exist.
- **Coverage badges or metrics we don't measure.** If it isn't measured in CI, it doesn't
  get a shield.
