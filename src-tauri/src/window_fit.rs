use std::fs;
use std::path::PathBuf;
use std::sync::{Mutex, MutexGuard};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use tauri::{
    App, AppHandle, Emitter, Manager, Monitor, PhysicalPosition, PhysicalSize, WebviewWindow,
    WindowEvent,
};

const DESIGN: (f64, f64) = (1440.0, 900.0);
// Smallest CSS viewport that fits 8 bands plus the EqualizerAPO panel without scrolling.
const MIN: (f64, f64) = (1100.0, 800.0);
const WORK_AREA_SHARE: f64 = 0.94;

const SCALE_MIN: f64 = 0.75;
const SCALE_MAX: f64 = 2.0;
const SCALE_STEP: f64 = 0.05;

const MAIN_WINDOW: &str = "main";
const SCALE_EVENT: &str = "ui-scale-changed";

#[derive(Debug, Clone, Copy, Serialize)]
pub struct ScaleInfo {
    pub percent: f64,
    pub min_percent: f64,
    pub max_percent: f64,
}

pub struct UiScale(Mutex<ScaleState>);

struct ScaleState {
    requested: f64,
    applied_px: f64,
    // Reused while the window keeps the size we set, so repeated steps do not drift.
    css: (f64, f64),
    set_inner: Option<PhysicalSize<u32>>,
    info: ScaleInfo,
}

#[derive(Serialize, Deserialize)]
struct StoredScale {
    ui_scale: f64,
}

#[derive(Clone, Copy, PartialEq)]
enum Reason {
    Launch,
    MonitorChanged,
    ScaleChanged,
}

pub fn setup(app: &App) {
    let requested = load_scale(app.handle()).unwrap_or(1.0);
    app.manage(UiScale(Mutex::new(ScaleState {
        requested,
        applied_px: 1.0,
        css: DESIGN,
        set_inner: None,
        info: ScaleInfo {
            percent: requested * 100.0,
            min_percent: SCALE_MIN * 100.0,
            max_percent: SCALE_MAX * 100.0,
        },
    })));

    let Some(window) = app.get_webview_window(MAIN_WINDOW) else {
        return;
    };
    apply(&window, Reason::Launch);
    let _ = window.show();

    let handle = window.clone();
    window.on_window_event(move |event| {
        if let WindowEvent::ScaleFactorChanged { .. } = event {
            // Windows applies its own suggested size right after this event; refit after it.
            let handle = handle.clone();
            std::thread::spawn(move || {
                std::thread::sleep(Duration::from_millis(150));
                let window = handle.clone();
                let _ = handle.run_on_main_thread(move || apply(&window, Reason::MonitorChanged));
            });
        }
    });
}

pub fn get_scale(app: &AppHandle) -> ScaleInfo {
    lock(app).info
}

pub fn set_scale(app: &AppHandle, percent: f64) -> ScaleInfo {
    let requested = {
        let mut state = lock(app);
        let max = (state.info.max_percent / 100.0).max(SCALE_MIN);
        state.requested = snap(percent / 100.0).clamp(SCALE_MIN, max);
        state.requested
    };
    save_scale(app, requested);
    if let Some(window) = app.get_webview_window(MAIN_WINDOW) {
        apply(&window, Reason::ScaleChanged);
    }
    get_scale(app)
}

fn lock(app: &AppHandle) -> MutexGuard<'_, ScaleState> {
    app.state::<UiScale>()
        .inner()
        .0
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

fn apply(window: &WebviewWindow, reason: Reason) {
    let Some(monitor) = monitor_of(window) else {
        return;
    };
    let app = window.app_handle();
    let (requested, old_px, old_css, old_inner) = {
        let state = lock(app);
        (state.requested, state.applied_px, state.css, state.set_inner)
    };

    let scale = monitor.scale_factor();
    let base = base_px_per_css(scale);
    let work = monitor.work_area();
    let maximized = window.is_maximized().unwrap_or(false);
    let (frame_w, frame_h) = frame_size(window);
    let inner_now = window.inner_size().ok();

    let (avail_w, avail_h) = match (maximized, inner_now) {
        (true, Some(inner)) => (inner.width as f64, inner.height as f64),
        _ => (
            work.size.width as f64 * WORK_AREA_SHARE - frame_w,
            work.size.height as f64 * WORK_AREA_SHARE - frame_h,
        ),
    };

    let px_fit = (avail_w / MIN.0).min(avail_h / MIN.1);
    let px = (base * requested).min(px_fit);

    let (want_w, want_h) = match (reason, inner_now) {
        (Reason::ScaleChanged, Some(inner)) if Some(inner) == old_inner => old_css,
        (Reason::ScaleChanged, Some(inner)) => (inner.width as f64 / old_px, inner.height as f64 / old_px),
        _ => DESIGN,
    };
    let (want_w, want_h) = (want_w.max(MIN.0), want_h.max(MIN.1));
    let css_w = want_w.min(avail_w / px);
    let css_h = want_h.min(avail_h / px);

    // Round up: a fraction of a px under MIN shows a scrollbar.
    let inner = PhysicalSize::new((css_w * px).ceil() as u32, (css_h * px).ceil() as u32);
    let min = PhysicalSize::new((MIN.0 * px).ceil() as u32, (MIN.1 * px).ceil() as u32);

    let _ = window.set_zoom(px / scale);
    let _ = window.set_min_size(Some(min));

    if !maximized {
        let _ = window.set_size(inner);
        let outer_w = inner.width as i32 + frame_w as i32;
        let outer_h = inner.height as i32 + frame_h as i32;
        let (left, top) = (work.position.x, work.position.y);
        let (right, bottom) = (left + work.size.width as i32, top + work.size.height as i32);
        let (x, y) = if reason == Reason::Launch {
            (left + (right - left - outer_w) / 2, top + (bottom - top - outer_h) / 2)
        } else {
            // Stay on this monitor so a resize cannot bounce the window between scales.
            let pos = window.outer_position().unwrap_or(PhysicalPosition::new(left, top));
            (pos.x.min(right - outer_w).max(left), pos.y.min(bottom - outer_h).max(top))
        };
        let _ = window.set_position(PhysicalPosition::new(x, y));
    }

    let info = ScaleInfo {
        percent: (px / base * 100.0).round(),
        min_percent: SCALE_MIN * 100.0,
        max_percent: ((px_fit / base).min(SCALE_MAX) / SCALE_STEP).floor() * SCALE_STEP * 100.0,
    };
    {
        let mut state = lock(app);
        state.applied_px = px;
        state.css = (want_w, want_h);
        state.set_inner = (!maximized).then_some(inner);
        state.info = info;
    }
    let _ = window.emit(SCALE_EVENT, info);
}

fn monitor_of(window: &WebviewWindow) -> Option<Monitor> {
    match window.current_monitor() {
        Ok(Some(monitor)) => Some(monitor),
        _ => window.primary_monitor().ok().flatten(),
    }
}

// Native pixels on Windows; elsewhere keep the platform scale (Retina on macOS).
fn base_px_per_css(scale: f64) -> f64 {
    if cfg!(windows) {
        1.0
    } else {
        scale
    }
}

fn snap(scale: f64) -> f64 {
    (scale / SCALE_STEP).round() * SCALE_STEP
}

fn frame_size(window: &WebviewWindow) -> (f64, f64) {
    match (window.outer_size(), window.inner_size()) {
        (Ok(outer), Ok(inner)) => (
            outer.width.saturating_sub(inner.width) as f64,
            outer.height.saturating_sub(inner.height) as f64,
        ),
        _ => (0.0, 0.0),
    }
}

fn scale_file(app: &AppHandle) -> Option<PathBuf> {
    app.path().app_config_dir().ok().map(|dir| dir.join("ui.json"))
}

fn load_scale(app: &AppHandle) -> Option<f64> {
    let text = fs::read_to_string(scale_file(app)?).ok()?;
    let stored: StoredScale = serde_json::from_str(&text).ok()?;
    Some(snap(stored.ui_scale).clamp(SCALE_MIN, SCALE_MAX))
}

fn save_scale(app: &AppHandle, ui_scale: f64) {
    let Some(path) = scale_file(app) else {
        return;
    };
    if let Some(dir) = path.parent() {
        let _ = fs::create_dir_all(dir);
    }
    if let Ok(text) = serde_json::to_string_pretty(&StoredScale { ui_scale }) {
        let _ = fs::write(path, text);
    }
}
