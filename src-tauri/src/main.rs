#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod apo;
mod commands;
mod window_fit;

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
            commands::get_ui_scale,
            commands::set_ui_scale,
        ])
        .setup(|app| {
            window_fit::setup(app);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
