# Honest assessment — what this design can detect, and after how long

Written 2026-08-14, before any forward outcome exists. Every number below is
computed from the committed series; the reproduction snippet is at the end.

## The measured shape of the strategy's difference from doing nothing

Over the full out-of-sample span available today (2020-01-02 → 2026-08-13,
1,661 daily bars ≈ 6.59 years, engine and costs unchanged):

| Quantity | Value |
|---|---|
| Days the crossover sat flat | 19.9% |
| Trades | 13 (≈ 2.0/yr — about one round-trip regime bet per year) |
| Annualized active return (crossover − buy-and-hold) | **−5.27%/yr** |
| Tracking error (annualized) | 15.21% |
| Information ratio | **−0.346** |
| Sharpe, crossover vs buy-and-hold | 0.87 vs 0.84 (difference ≪ noise) |

## Detection horizon — the arithmetic nobody can negotiate with

To reject "no edge" at |t| ≈ 2, forward years needed ≈ (2 / IR)²:

| True information ratio | Forward data required |
|---|---|
| 0.10 | ~400 years |
| 0.20 | ~100 years |
| 0.35 (the size actually measured, as a deficit) | ~33 years |
| 0.50 | ~16 years |
| 1.00 (elite) | ~4 years |

The strategy expresses its difference from the benchmark through roughly
**one independent trend bet per year**. Decision-log entries accrue ~12/yr at
the 21-bar horizon, but consecutive entries overlap and restate the same
regime bet — they measure the discipline of the record, not independent
draws of skill.

**Plainly: this design cannot statistically confirm a plausible-size edge in
a daily single-instrument MA strategy on any human timescale.** That is a
property of the strategy class and the data frequency, not of the harness.
What the lane CAN deliver, and quickly: proof the implementation does what
it claims out of sample, a scoreable record that no parameter moved after
results were seen, the strategy's behavior at the next cross (the drawdown
half of the trend-following trade-off), and whether the already-measured
out-of-sample deficit persists directionally.

## What would make this misleading — hunted specifically

1. **Delayed quotes treated as live.** Measured: `top_status = REALTIME` with
   a trade timestamp seconds from wall clock (inventory doc). Design margin:
   signals consume completed daily bars, so latency could at worst mistime
   the writing of an entry, never the signal's content. Residual: the status
   is per-subscription — re-read it at every future fetch.
2. **A forming bar read as a close.** Today's fetch was pre-market and the
   last bar was the completed prior session. An RTH-time refresh could
   include a partial bar; the refresh procedure forbids using it, and the
   entry schema's `signal_bar` makes any violation visible after the fact.
3. **Look-ahead in execution.** The engine fills at the next bar's open and
   its accounting is pinned by hand-computed tests; the forward lane reuses
   it unchanged.
4. **A parameter touched after seeing forward data.** Constants are frozen,
   a tripwire test fails if grid selection re-enters `quant/forward.py`, and
   the contract says a strategy change is a new lane, not an edit. The
   temptation log is this file and the rule: none has been acted on.
5. **Vendor/adjustment seams.** Raw-vs-adjusted measured to six decimals and
   guarded at every run; the ex-dividend refresh rule is written down
   because the guard cannot see that case; vendor opens differ by ≤ $0.07
   (~1 bp, fills only — one fill so far).
6. **Survivorship.** SPY-on-SPY carries no cross-sectional survivorship, but
   the design inherits selection-on-history: 10/200 was still the best of
   nine grid cells on 1993-2019. The forward lane exists because of exactly
   that contamination; its windows stay labeled.
7. **Pre-registration that could be quietly rewritten.** Append-only
   contract, one commit per entry, no amend/rebase/squash. Named weakness:
   a local commit timestamp is self-attested until the branch is pushed —
   pushing gives the timestamps a third-party receive time. Pushing awaits
   the owner (AGENTS.md gate).
8. **Metric shopping.** One horizon (21 bars), one falsifier per stance,
   fixed before any outcome; the scorer reports scored / pending /
   malformed as numbers on every run, so nothing can be dropped silently.

## Is this worth continuing?

**The harness is sound, and the strategy has no detectable edge — and on the
seen window it is behind by an amount (−5.27%/yr active) that decades would
be needed to distinguish from an equal-size true deficit.** That is the
honest standing answer, and it is a good outcome: the question "does my
system beat doing nothing" currently reads *no* on total return, *tie* on
risk-adjusted terms, *unknowable soon* on statistical proof.

Worth continuing at the current cost (one refresh cycle per update, zero
risk, zero orders): as an integrity record, as the only place the next
cross's drawdown behavior will be measured honestly, and as evidence of
method. Not worth continuing as an edge-confirmation instrument — no amount
of daily SPY data arriving at realistic speed can deliver that, and this
file exists so nobody quietly forgets it.

## Reproduce

```python
import numpy as np, pandas as pd
from quant.backtest import CostModel, run_backtest
from quant.forward import FROZEN_FAST, FROZEN_SLOW, load_spliced
from quant.strategies import buy_and_hold, ma_crossover

prices = load_spliced()
oos = prices[prices.index >= pd.Timestamp('2020-01-02')]
w = ma_crossover(prices['close'], FROZEN_FAST, FROZEN_SLOW).loc[oos.index]
b = buy_and_hold(prices['close']).loc[oos.index]
active = (run_backtest(oos, w, CostModel()).returns
          - run_backtest(oos, b, CostModel()).returns).dropna()
mu, te = active.mean() * 252, active.std(ddof=1) * np.sqrt(252)
print(mu, te, mu / te)  # -0.0527, 0.1521, -0.346
```
