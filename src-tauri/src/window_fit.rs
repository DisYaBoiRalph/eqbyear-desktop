use std::time::Duration;

use tauri::{Monitor, PhysicalPosition, PhysicalSize, WebviewWindow, WindowEvent};

const DESIGN: (f64, f64) = (1440.0, 900.0);
// Smallest CSS viewport that fits 8 bands plus the EqualizerAPO panel without scrolling.
const MIN: (f64, f64) = (1100.0, 800.0);
const WORK_AREA_SHARE: f64 = 0.94;

pub fn fit_to_screen(window: &WebviewWindow) {
    if let Some(monitor) = monitor_of(window) {
        fit(window, &monitor, true);
    }
    let _ = window.show();

    let handle = window.clone();
    window.on_window_event(move |event| {
        if let WindowEvent::ScaleFactorChanged { .. } = event {
            // Windows applies its own suggested size right after this event; refit after it.
            let handle = handle.clone();
            std::thread::spawn(move || {
                std::thread::sleep(Duration::from_millis(150));
                let window = handle.clone();
                let _ = handle.run_on_main_thread(move || {
                    if let Some(monitor) = monitor_of(&window) {
                        fit(&window, &monitor, false);
                    }
                });
            });
        }
    });
}

fn monitor_of(window: &WebviewWindow) -> Option<Monitor> {
    match window.current_monitor() {
        Ok(Some(monitor)) => Some(monitor),
        _ => window.primary_monitor().ok().flatten(),
    }
}

// Native pixels on Windows; elsewhere keep the platform scale (Retina on macOS).
fn preferred_px_per_css(scale: f64) -> f64 {
    if cfg!(windows) {
        1.0
    } else {
        scale
    }
}

fn fit(window: &WebviewWindow, monitor: &Monitor, center: bool) {
    let scale = monitor.scale_factor();
    let work = monitor.work_area();
    let (frame_w, frame_h) = frame_size(window);

    let avail_w = work.size.width as f64 * WORK_AREA_SHARE - frame_w;
    let avail_h = work.size.height as f64 * WORK_AREA_SHARE - frame_h;

    let px = preferred_px_per_css(scale).min(avail_w / MIN.0).min(avail_h / MIN.1);
    let css_w = DESIGN.0.min(avail_w / px);
    let css_h = DESIGN.1.min(avail_h / px);

    // Round up: a fraction of a px under MIN shows a scrollbar.
    let inner = PhysicalSize::new((css_w * px).ceil() as u32, (css_h * px).ceil() as u32);
    let min = PhysicalSize::new((MIN.0 * px).ceil() as u32, (MIN.1 * px).ceil() as u32);

    let _ = window.set_zoom(px / scale);
    let _ = window.set_min_size(Some(min));
    let _ = window.set_size(inner);

    let outer_w = inner.width as i32 + frame_w as i32;
    let outer_h = inner.height as i32 + frame_h as i32;
    let (left, top) = (work.position.x, work.position.y);
    let (right, bottom) = (left + work.size.width as i32, top + work.size.height as i32);

    let (x, y) = if center {
        (left + (right - left - outer_w) / 2, top + (bottom - top - outer_h) / 2)
    } else {
        // Stay on this monitor so a resize cannot bounce the window between scales.
        let pos = window.outer_position().unwrap_or(PhysicalPosition::new(left, top));
        (
            pos.x.min(right - outer_w).max(left),
            pos.y.min(bottom - outer_h).max(top),
        )
    };
    let _ = window.set_position(PhysicalPosition::new(x, y));
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
