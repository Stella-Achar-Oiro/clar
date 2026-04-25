# CLAR — Claude Code Instructions

## Worktrees
Worktree directory: `.worktrees/` (project-local, hidden, gitignored)

## Project
CLAR is a FastAPI + LangGraph + Next.js 14 medical report analysis app.
See `docs/superpowers/specs/2026-04-25-clar-system-design.md` for the full design.
See `docs/superpowers/plans/` for the three implementation plans.

## Rules
- Never add Co-Authored-By to commit messages or PRs
- No emojis anywhere in UI or code — SVG icons only
- TDD: write the test first, run it (red), implement, run it (green)
- Never log `raw_text` or `deid_text` — metadata only
- Design tokens live in `styles/tokens.ts` — no hardcoded hex in components
- 150-line hard cap per file in the frontend — split before hitting the limit
- Pin Clerk to `@clerk/nextjs@6.x` — v7 removed SignedIn/SignedOut
