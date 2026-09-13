# EQ by ear

A browser tool for EQing headphones and IEMs by ear, live at https://eqbyear.com.
Play a sine tone, sweep it slowly, mark the peaks and dips you hear, and turn the marks
into an 8-band parametric EQ you can paste into any PEQ app. Static site, no backend,
no dependencies.

Tutorial video: https://youtu.be/WIWHINQ5lV8

## Run locally

```bash
python3 -m http.server 8080 --directory src
```

then open `http://localhost:8080`. Any static file server works.

## Layout

- `src/index.html`, `src/css/`, `src/js/`, `src/assets/` - the site. ES modules, no build step.
- `src/js/dsp.js` - filter math (RBJ biquads), log axis, three-point mark to band.
- `tests/dsp.test.mjs` - `node tests/dsp.test.mjs`
- `design/` - mock generator and artboards the theme was ported from.
- `docs/SPEC.md` - build contract.
- `src-tauri/` - the desktop build (see below).

## Desktop build

A Tauri shell around the same site lives in `src-tauri/`. On Windows it can sync the EQ curve
straight into EqualizerAPO. See `src-tauri/README.md`.

```bash
cargo tauri dev
cargo tauri build
```

## License

Apache License 2.0. See `LICENSE`. "DMS" and "EQ by ear" names and logo are not
licensed for use on derived works.
