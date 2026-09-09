# DMS Sweep — master plan and progress log

Approved plan (full text): `~/.claude/plans/zazzy-juggling-kurzweil.md`.
Live position and pending owner actions: `docs/HANDOFF.md`.

## What this is
A static website for the owner's headphone/IEM EQ method: sine tone at normal
listening level, slow manual sweep by dragging, mark peaks (three points: start
of rise, top, end) and dips by ear, cut them with parametric EQ one at a time
while re-sweeping, then lower preamp and fill sub-bass / upper treble / major
dips. Output: generic 8-band PEQ text. Rev 1 is the tool with minimal prose.

## Locked decisions (2026-09-09)
- Headphones and IEMs, 20 Hz–20 kHz, hearing/equipment warning on first use.
- No loudness compensation (matches the method). Possible later option.
- Tone latches after mouse release; Space or Stop silences.
- Three-point peaks. Q = fc / (f_end − f_start), clamped 0.3–10. Single-point marks allowed.
- Dips = same flow with positive gain. Band types: Peak, Low shelf, High shelf.
- 8 bands max. Preamp auto-suggested from largest boost, editable.
- Re-sweep with EQ engaged; global EQ on/off, per-band enable.
- Export: generic PEQ text (Equalizer APO style), copy + download; session JSON; localStorage autosave.
- Out of rev 1: music preview, L/R sweeps, phone layout.
- Dark theme, DMS logo from `assets/dms-logo-2026.png`, accent #FCBE11.
- Mockups first (three directions on a design canvas), owner picks, then build.
- Stack: vanilla HTML/CSS/JS ES modules, no build step, `python3 -m http.server`.

## Phases
0. Records and scaffolding
1. Design directions on a design canvas; owner picks
2. Core build: audio engine, sweep strip, graph, marking, bands, re-sweep
3. Export and persistence
4. Polish and QA

## Progress log
| Date | Slice | Notes |
|------|-------|-------|
| 2026-09-09 | Phase 0: folder, git, records, launch config | Logo moved to `assets/`. |
| 2026-09-09 | Phase 1: three design directions on a design canvas | Artboards + generator in `design/`. Canvas: https://claude.ai/code/artifact/275c965b-2451-48cc-ba31-910cb3e2dc39 . Awaiting owner pick. |
| 2026-09-09 | Phase 1 round 2: minimal light (D) + dark (E) boards added; canvas now two pages | Owner found round 1 too dense. Same canvas URL. |
