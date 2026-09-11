# DMS Sweep — master document

The single living record for this project. Update it every session: position, log,
decisions, next steps. Read it first when resuming. Technical contract for the code is
in `docs/SPEC.md`; this file is the plan and the history.

---

## 1. What this is

A website that walks people through the DMS method for EQing headphones and IEMs by
ear, and turns the result into a parametric EQ they can paste into any PEQ app.

**The method, as the owner does it**

1. Set playback level to where you normally listen to music.
2. Play a sine tone and sweep it slowly by hand from low to high.
3. Where a peak or a steep rise jumps out, stop and mark it.
4. Cut that peak with a parametric band, then re-sweep through it and adjust until it
   sits flat. One peak at a time.
5. When the peaks are handled, lower the preamp and fill in what's missing: sub-bass,
   upper treble, or any major dip.

**Product principles**

- Rev 1 is the tool only. No explanatory prose beyond labels and the volume warning.
  Info sections come later.
- Quiet, minimal, human. Type, hairlines, whitespace, the graph. No panels, gradients,
  or the generic web-app look.
- Ear safety is non-negotiable: warning gate, quiet default level, hard output ceiling.

---

## 2. Decisions (locked)

| Date | Decision |
|------|----------|
| 2026-09-09 | Headphones and IEMs. 20 Hz to 20 kHz. Desktop browsers first, no phone layout in rev 1. |
| 2026-09-09 | Tone is not loudness-compensated; that matches the method. Possible later option. |
| 2026-09-09 | Tone latches after mouse release. Space or Stop silences. |
| 2026-09-09 | Three-point peaks: mark start of rise, top, end. fc from top, Q from the edges (Q = fc ÷ bandwidth, clamped 0.3–10). Single-point marks allowed with Q 2. |
| 2026-09-09 | Dips use the same flow with positive gain. Band types Peak, Low shelf, High shelf. |
| 2026-09-09 | 8 bands max. Preamp auto-suggested from the largest boost, editable. |
| 2026-09-09 | Export as generic PEQ text (Equalizer APO style), copy and download. Session JSON export/import. Browser autosave. |
| 2026-09-09 | Out of rev 1: music preview, separate L/R sweeps, phone layout. |
| 2026-09-09 | Design: "Quiet" direction. Light by default with a dark toggle. System Arial stack, monospace only for the export text. Logo inside a black circle. Accent #FCBE11 only where it means something. |
| 2026-09-09 | Stack: vanilla HTML/CSS/JS ES modules, no build step, no dependencies. Localhost for testing. |
| 2026-09-09 | Domain: owner registered **eqbyear.com**. Site name on the page is just "DMS". |
| 2026-09-09 | Design v3 (2026-09-09, later): owner loves the FastGraph 95 mock (G) and asked to implement it: Win95-style volume slider instead of a dB box, bands stacked in a right-hand column. FastGraph 95 becomes the default theme; FastGraph 95 Dark behind the toggle. Supersedes v2. |
| 2026-09-09 | Design v2: Fastgraph theme approved (direction F). Fastgraph dark tokens, Inter + Inconsolata, accent #66CCFF, recessed glow buttons, segmented marks, panels, status bar. Dark by default, Fastgraph light tokens as the toggle. Gate level starts at −20 dB. Bands rows roomier than the mock. Supersedes the quiet-light decision. |

---

## 3. Architecture (short)

```
index.html          page skeleton, first-run gate
css/tokens.css      light/dark tokens on <html data-theme>
css/app.css         layout and components
js/dsp.js           biquad math (RBJ), log axis, 3-point → band, formatting
js/audio.js         AudioEngine: osc → tone gain → preamp → 8 biquads → level → ceiling → clipper → analyser
js/sweep.js         the tape: pointer drag → frequency, needle
js/graph.js         SVG response plot: grid, ghost bands, summed curve, marks, playhead
js/store.js         state + actions + subscribe
js/export.js        PEQ text, clipboard, downloads, session JSON
js/storage.js       localStorage autosave/restore
js/app.js           wiring, band list, mark panel, keyboard, theme
tests/dsp.test.mjs  node tests for dsp.js against the Python reference
design/             mock generator (build_mocks.py) and artboards; dms-sweep.html is the assembled canvas (gitignored)
docs/SPEC.md        the build contract (APIs, tokens, acceptance list)
```

Deploy: `npx wrangler deploy` from the repo root (Wrangler is logged in on this Mac;
`wrangler.jsonc` names the Worker and both custom domains; `.assetsignore` keeps non-site
files out of the upload).

Run locally:

```
python3 -m http.server 8080
```
then open http://localhost:8080. `window.dmsSweep` exposes `{store, engine, graph, sweep}`
in the browser console for checks.

Keyboard: click or drag the tape to sweep · ← → nudge (Shift for coarse) · Space play/stop ·
1 2 3 mark start/top/end · D peak/dip · Z undo · Esc clear · Enter commit a top-only mark.

---

## 4. Phases

| # | Phase | Status |
|---|-------|--------|
| 0 | Records and scaffolding | Done 2026-09-09 |
| 1 | Design directions, owner picks | Done 2026-09-09 (three rounds; Fastgraph theme chosen after the quiet theme read as generic) |
| 2 | Core build: audio, sweep, graph, marking, bands, re-sweep | Done 2026-09-09 |
| 3 | Export and persistence | Done 2026-09-09 |
| 4 | Polish and QA after owner's first real use; Safari and Firefox pass | Next |
| 5 | Hosting on eqbyear.com | Done 2026-09-09 (Cloudflare Workers static assets, custom domains apex + www) |
| 6 | Info sections (the method explained, tips) | Later |

---

## 5. Work log

One row per shipped slice. Newest last.

| Date | Slice | Notes |
|------|-------|-------|
| 2026-09-09 | Project folder, git, records, launch config | Logo moved to `assets/`. |
| 2026-09-09 | Round 1 design directions (A bench instrument, B lab notebook, C broadcast console) | Owner: too dense. |
| 2026-09-09 | Round 2 directions (D quiet light, E quiet dark) | Owner chose D with a dark toggle, Arial, circle logo. Canvas: https://claude.ai/code/artifact/275c965b-2451-48cc-ba31-910cb3e2dc39 |
| 2026-09-09 | `docs/SPEC.md` and `js/dsp.js` | Spec is the contract; dsp ported 1:1 from the mock's Python. |
| 2026-09-09 | Modules built in parallel: audio + tests, graph + sweep, page + store + export + app | Delegated per module, reviewed and integrated in the main session. |
| 2026-09-09 | Integration and acceptance in the in-app Chromium | All items in SPEC.md acceptance passed. Fixes: compressor replaced by a hard clipper (its makeup gain skewed levels 1.6 dB), clipboard fallback, band numbers lifted off the axis labels. |
| 2026-09-09 | Top bar: wordmark is just "DMS", Tutorial button added (link TBD) | Owner review of the first build: "brilliant" otherwise. |
| 2026-09-09 | Floatplane and Patreon buttons in the top bar; hidden affiliate gear section scaffolded | Gear section unpublished until links exist. |
| 2026-09-09 | Round 3 design direction: F · Fastgraph (tokens + button recipe lifted from DMS Fastgraph's default dark theme) | Feedback on the live site: still reads "vibe coded". Canvas page "Round 3 · Fastgraph". Awaiting owner pick; if approved, port offline, verify, then deploy. |
| 2026-09-09 | Fastgraph theme ported to the site and deployed | Dark default, light via toggle. Gate starts at −20 dB. Cache-busting `?v=` on CSS/JS links (bump the query when CSS/JS change). One-time localStorage flag `dms-sweep:theme-v2` moves pre-existing sessions to dark. Verified with headless Chrome renders + in-pane functional checks (marks, export, theme toggle). |
| 2026-09-09 | FastGraph 95 theme ported and deployed | Default = FastGraph 95 (teal/silver), toggle = FastGraph 95 Dark. Win95 range slider for level, bands column right, no webfonts (Tahoma stack). One-time flag `dms-sweep:theme-v3` resets saved sessions to the light 95 theme. |
| 2026-09-09 | Live on https://eqbyear.com | Cloudflare Workers static assets, Worker `eqbyear`, config `wrangler.jsonc`, upload filter `.assetsignore`. Deploy: `npx wrangler deploy` from the repo root. |

---

## 6. Session handoff (keep current)

**Position**: Rev 1 is live on eqbyear.com in the FastGraph 95 theme (light default, 95-dark toggle). Owner has not yet used it with headphones for real. The blue Fastgraph theme (v2) survives only in git history and the canvas.

**Fastgraph theme source** (read-only reference): `/Users/dms/Documents/DMS Fastgraph/dms/ui/style_tokens.py` (DARK_TOKENS, GeometryTokens, MotionTokens), `dms/theme.py` (`_stylesheet_body`), `dms/ui/modern_button.py` (glow button paint). The mock's `F_CSS` in `design/build_mocks.py` is the web port of those.

**Next actions**

- Owner: try it with headphones and note what feels wrong (sweep feel, mark flow, how
  gain is adjusted, anything visual). Review the canvas if useful.
- Then: Phase 4 polish from that feedback. Safari and Firefox sanity pass.
- Optional: a redirect rule so www.eqbyear.com redirects to eqbyear.com (both currently
  serve the site).

**Open questions**

- Tutorial button links to https://youtu.be/WIWHINQ5lV8 (set 2026-09-10). Floatplane and
  Patreon buttons sit beside it (https://www.floatplane.com/channel/DMS3,
  https://www.patreon.com/DMS3TV).
- Affiliate "Run this EQ on" section exists in `index.html` as `#gear` with the `hidden`
  attribute; it stays unpublished until the owner has affiliate links (Qudelix etc.; the
  owner's favourite PEQ device is not on Amazon). Remove `hidden` and fill `.gear-list`.

- Commit attribution: the Claude Code harness appends a `Co-Authored-By` trailer to
  commits, which conflicts with the owner's global no-attribution rule. All commits so far
  carry it. Nothing is pushed, so trailers can be rewritten before any remote exists.
  Owner to decide.
- Gain adjustment by ear: rev 1 adjusts gain by typing or arrow keys in the band row.
  Dragging on the graph is a likely Phase 4 addition if the owner wants it.
- Shelf Q: Web Audio ignores Q on shelf filters while the graph draws RBJ shelves with Q.
  Shelf curves can differ slightly from what is heard. Acceptable for rev 1; noted in code.

**Machine facts**: macOS (Darwin 25.6), python3 3.14, node v26.5 via Homebrew, Claude Code CLI 2.1.251.
Git user DMS, no remote yet. Local preview config in `.claude/launch.json`.
Cloudflare plugin (skills + MCP servers) installed in Claude Code at user scope on 2026-09-09 from
https://developers.cloudflare.com/agent-setup/prompt.md; Cloudflare OAuth login happens on first tool use.

**Other records**: approved plan file `~/.claude/plans/zazzy-juggling-kurzweil.md` (STATUS
block); Claude memory entry `dms-sweep-project` points here.

---

## 7. Ideas parked for later

- Equal-loudness weighting option for the tone (ISO 226) for people who want it.
- Music preview with the EQ applied, drop a file in and toggle.
- Separate left and right sweeps for driver mismatch.
- Dragging bands directly on the graph.
- Phone layout.
- Share link that encodes the session.
- Presets export for specific apps (Wavelet, Poweramp, Qudelix) if the generic text isn't enough.

---

## 8. Monetization notes (2026-09-09)

Free access stays. AdSense is a poor fit (low yield on a tool page, clashes with the design).
Preferred, in order: affiliate links in a short "what to run this EQ on" section (Amazon,
Linsoul, HiFiGo, Drop, Headphones.com programs); a quiet footer support link (Ko-fi / BMAC /
GitHub Sponsors / Patreon); the site as a funnel for the YouTube channel via the Tutorial
button; one direct "supported by" sponsor once traffic exists. Optional pay-what-you-want
extras (cloud profiles, share links, music preview) only if the owner is comfortable. Merch
is on brand but low revenue.
