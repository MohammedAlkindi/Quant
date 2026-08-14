# Agent rules for this repo

Scope and conduct for AI agents working in Quant. `CLAUDE.md` has project context; the
`~/Github/CLAUDE.md` workflow conventions apply on top of this file.

## Branch policy

- Never commit to `main`. Work on `<type>/<kebab-description>` branches; agent-initiated
  branches use the `claude/` prefix.
- Do not delete branches; the owner handles branch cleanup. Merging is covered by the
  grant below.

## Commits

Format, sizing, attribution and staging discipline are global — see `~/.claude/CLAUDE.md`.
This repo tightens two of them:

- Conventional commits **always carry a scope** here, not only when it adds clarity.
- **Lint** must pass too, not just tests, before any commit that touches code.

## Requires explicit confirmation from the owner

- Anything touching the order path (`backend/services/trade_service.py`,
  `backend/api/routes_trade.py`) beyond documentation.
- Adding live-broker credentials, endpoints, or SDKs; changing `ALPACA_BASE_URL` handling.
- Force-pushing anywhere, and any history rewrite.
- Publishing: releases, packages, repo-visibility changes.
- Pushing to, or opening PRs against, any repo that is not the owner's.
- Deleting files outside `experimental/`.

## Allowed without asking (owner grant, 2026-08-14)

- Pushing branches of this repo to `origin`.
- Merging the owner's own PRs in this repo — **only when CI is green on the head commit
  and the trailer scan (`commit-guard.js` patterns) is clean**. Branches carrying
  `forward/decisions/` entries merge by merge commit only, never squash or rebase
  (`CLAUDE.md`).

## Standing expectations

- Promote nothing out of `experimental/` without real training data, seeded runs, and
  out-of-sample evaluation through `quant/backtest`.
- Every README claim you add must be true at the commit that adds it.
