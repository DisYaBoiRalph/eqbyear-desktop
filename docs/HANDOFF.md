# Session handoff — DMS Sweep

Read this first when resuming. Keep it current at every checkpoint.

## Position
- Phase 1, round 2 delivered 2026-09-09: owner found round 1 (A/B/C) too dense. Added D · Quiet light (= Main.dc.html) and E · Quiet dark: hairlines, one grotesk + one mono, no boxes. Canvas has two pages: 'Round 2 · quiet' (opens first) and 'Round 1 · dense'.
  Canvas: https://claude.ai/code/artifact/275c965b-2451-48cc-ba31-910cb3e2dc39
- Mock sources: `design/build_mocks.py` generates the `*.dc.html` artboards and `canvas.json` (run from `design/`). `design/dms-sweep.html` is the assembled canvas (gitignored, regenerate with the design skill helper).
- Owner chose D (quiet, light) with a dark toggle, Arial, circle logo. Mock updated to match.
- Phase 2 in progress: `docs/SPEC.md` is the contract. `js/dsp.js` done (main loop). Delegated: `js/audio.js` + `tests/dsp.test.mjs`; `js/graph.js` + `js/sweep.js`; `index.html` + `css/*` + `js/store.js` + `js/export.js` + `js/storage.js` + `js/app.js`.
- If resuming mid-build: check which of those files exist, run `node tests/dsp.test.mjs`, serve with `python3 -m http.server 8080` and walk the SPEC.md acceptance list.

## Pending owner actions
- None until the Phase 2 build is up for review.
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
