# EQ by ear Desktop (Tauri shell)

This folder wraps the site at the repo root in a Tauri window. The site itself needs no build
step; `frontendDist` in `tauri.conf.json` points straight at the repo root.

## Build

Install the Rust toolchain and the Tauri CLI once:

```
cargo install tauri-cli --version "^2" --locked
```

Then, from the repo root:

```
cargo tauri dev      # run the app
cargo tauri build    # produce an installer for the current OS
```

## EqualizerAPO sync (Windows only)

When the app runs on Windows and finds EqualizerAPO installed, an "EqualizerAPO sync" panel
appears. Turning sync on:

1. Finds EqualizerAPO's config folder from the registry (`HKLM\SOFTWARE\EqualizerAPO\ConfigPath`),
   or lets you pick the folder yourself.
2. Adds one line, `Include: eqbyear.txt`, to the end of `config.txt`, once. A timestamped backup
   of `config.txt` is made first. This file is never edited again after that.
3. From then on, every change to a band writes only `eqbyear.txt` in that same folder, which
   EqualizerAPO reloads live. This changes real-time system audio, not only the in-app tone.

Turning sync off, or running on macOS/Linux, or running the plain web build at eqbyear.com, keeps
the app working exactly as the web version does today: nothing outside the app is touched.
