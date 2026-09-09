# Session handoff — DMS Sweep

Read this first when resuming. Keep it current at every checkpoint.

## Position
- Rev 1 tool is built and working locally (Phases 2 and 3 done, 2026-09-09). Run `python3 -m http.server 8080` in the repo root and open http://localhost:8080.
- Acceptance (docs/SPEC.md) verified in the in-app Chromium: gate → audio start, drag/keys → readout/needle/playhead, three-point mark → band (fc 3097, Q 2.45, −3 dB), EQ cut measured 3.00 dB via analyser, levels within 0.1 dB of design, export text format exact, reload restores state, theme toggle persists, Copy works (fallback path in the embedded browser).
- `window.dmsSweep` exposes {store, engine, graph, sweep} for console QA.
- Not yet done: Safari and Firefox sanity pass; Phase 4 polish pass after owner tries it with headphones; hosting/domain.

## Pending owner actions
- Try the tool locally with headphones and report what feels wrong (sweep feel, mark flow, gain adjustment, anything visual).
- Decide on commit attribution trailer (see Notes).
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
