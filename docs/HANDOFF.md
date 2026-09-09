# Session handoff — DMS Sweep

Read this first when resuming. Keep it current at every checkpoint.

## Position
- Phase 0 done. Next: Phase 1, three design-direction mockups on a design canvas.
- No app code exists yet.

## Pending owner actions
- Pick a design direction once the canvas is published.
- Decide on commit attribution trailer (see Notes).

## Machine facts
- macOS (Darwin 25.6), python3 3.14 at /Library/Frameworks/Python.framework, node v26.5 via Homebrew.
- Local preview: `.claude/launch.json` config `dms-sweep` → http://localhost:8080.
- Git user: DMS, noreply GitHub email. No remote yet.

## Records
- Master plan + progress log: `docs/PLAN.md`
- Approved plan file: `~/.claude/plans/zazzy-juggling-kurzweil.md` (has a STATUS block)
- Memory pointer: `dms-sweep-project` in Claude memory
- Logo: `assets/dms-logo-2026.png`

## Notes
- The Claude Code harness currently appends a `Co-Authored-By: Claude Fable 5.1` trailer to commits, which conflicts with the owner's global no-attribution rule. Repo is local only, so trailers can be rewritten before any push. Owner to decide.
