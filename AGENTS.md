# Agent rules for this repo

Scope and conduct for AI agents working in Quant. `CLAUDE.md` has project context; the
`~/Github/CLAUDE.md` workflow conventions apply on top of this file.

## Branch policy

- Never commit to `main`. Work on `<type>/<kebab-description>` branches; agent-initiated
  branches use the `claude/` prefix.
- Do not merge or delete branches; the owner reviews and merges.

## Commits

- Stage by explicit file path — never `git add .` or `git add -A`.
- Conventional commits with a scope, one logical change per commit.
- No `Co-Authored-By` or any AI attribution lines.
- Tests and lint must pass before any commit that touches code.

## Requires explicit confirmation from the owner

- Anything touching the order path (`backend/services/trade_service.py`,
  `backend/api/routes_trade.py`) beyond documentation.
- Adding live-broker credentials, endpoints, or SDKs; changing `ALPACA_BASE_URL` handling.
- Pushing to any remote; force-pushing anywhere.
- Deleting files outside `experimental/`.

## Standing expectations

- Promote nothing out of `experimental/` without real training data, seeded runs, and
  out-of-sample evaluation through `quant/backtest`.
- Every README claim you add must be true at the commit that adds it.
