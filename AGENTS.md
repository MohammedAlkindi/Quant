# Agent rules for this repo

Scope and conduct for AI agents working in Quant. `CLAUDE.md` has project context; the
`~/Github/CLAUDE.md` workflow conventions apply on top of this file.

## Branch policy

- Never commit to `main`. Work on `<type>/<kebab-description>` branches; agent-initiated
  branches use the `claude/` prefix.
- Do not merge or delete branches; the owner reviews and merges.

## Commits

Format, sizing, attribution and staging discipline are global — see `~/.claude/CLAUDE.md`.
This repo tightens two of them:

- Conventional commits **always carry a scope** here, not only when it adds clarity.
- **Lint** must pass too, not just tests, before any commit that touches code.

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
