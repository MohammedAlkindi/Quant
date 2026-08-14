# Pre-registered decision log

**A prediction is only scoreable if it was written down before the outcome.**
That is this directory's entire value, and every rule below exists to protect
it.

Each file here records, *before the outcome is knowable*, what the frozen
rule says as of the latest completed daily bar: the stance, the exact numbers
behind it, and the condition under which it will have been wrong. Entries are
scored later by `python -m quant.scoring`. Nothing here is advice — an entry
records what a stated rule would do at a nominal reference size, tied to no
account.

## Append-only, enforced by convention and by git

- **One file per entry**, named by write time: `YYYY-MM-DDTHHMMSSZ.md` (UTC).
- **Never edit, delete, or reorder a past entry.** A wrong entry is corrected
  by a *new* entry that names it in a `corrects:` field. The wrong entry
  stays.
- **Each entry is committed in its own commit, as it is written.** The commit
  timestamp is the pre-registration proof.
- **Never amend or rebase anything under this directory.** An edited history
  destroys the claim that the prediction predated the outcome.
- Consequence for merges: a branch carrying entries reaches `main` **by
  merge commit only — never squash, never rebase.** Squashing collapses the
  per-entry commit dates into one; rebasing re-stamps them. Either destroys
  the timestamp evidence.

## Entry schema

Flat `key: value` front matter between `---` fences, then a prose body a
reader can recompute the decision from. Fields the scorer requires
(`quant/scoring.py` hard-fails, loudly and per-file, on anything missing or
malformed — a malformed entry is never skipped quietly):

| Field | Meaning |
|---|---|
| `entry_id` | Stable id, normally the filename stem. |
| `written_utc` | When the entry was written (UTC, ISO-8601). |
| `rule` | The exact rule evaluated, with parameters. |
| `signal_bar` | The completed daily bar whose close produced the stance. |
| `stance` | `LONG` or `FLAT` — what the rule says to hold. |
| `effective_bar` | The next trading day: the engine's one-bar delay means the stance governs from this bar's open. Pre-registration requires `written_utc` to precede this bar's open. |
| `horizon_bars` | Scoring horizon. **Fixed at 21 for every entry** (pre-registered 2026-08-14, before any outcome existed). A different horizon is a different rule and would need its own log, stated as such. |
| `falsified_if` | The pre-stated falsifier, in words matching the semantics below. |

Documented context fields (recorded, not scorer-enforced): `instrument`,
`size_fraction`, `notional_basis`, `data_source`, `data_delayed`, `ma_fast`,
`ma_slow`, `last_close`, `action`, `corrects`.

## Falsifier semantics — decided before any outcome

Let `R = close(effective_bar + horizon_bars − 1) / open(effective_bar) − 1`:
the cost-free return of a full-weight long over the entry's window, on the
spliced adjusted series (`quant.forward.load_spliced`).

- A `LONG` entry is **falsified when `R < 0`** — the rule held the market and
  the market paid nothing.
- A `FLAT` entry is **falsified when `R > 0`** — the rule stood aside and the
  market paid.
- `R = 0` exactly falsifies neither.

Costs are deliberately absent here (a 4 bps round trip cannot decide a
falsification at this horizon); the engine-based forward test
(`python -m quant.forward`) is where the cost model lives. The log is
single-instrument (SPY) like the rest of the research lane.

## What the scorer promises

`python -m quant.scoring` reports **scored, pending, and malformed counts as
numbers on every run** — a run that scored nothing must say so, never exit
quietly green. Entries whose horizon has not elapsed are pending: counted and
named, never guessed at. Malformed files are named with the reason and make
the exit code nonzero.
