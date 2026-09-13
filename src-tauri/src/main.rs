#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod apo;
mod commands;
mod window_fit;

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            commands::detect_apo_config_dir,
            commands::get_apo_settings,
            commands::save_apo_settings,
            commands::ensure_include_directive,
            commands::write_eqbyear_preset,
            commands::check_apo_status,
        ])
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                window_fit::fit_to_screen(&window);
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
