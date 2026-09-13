use tauri::AppHandle;

use crate::apo::{self, ApoSettings, ApoStatus, IncludeResult, WriteResult};
use crate::window_fit::{self, ScaleInfo};

#[tauri::command]
pub fn get_ui_scale(app: AppHandle) -> ScaleInfo {
    window_fit::get_scale(&app)
}

#[tauri::command]
pub fn set_ui_scale(app: AppHandle, percent: f64) -> ScaleInfo {
    window_fit::set_scale(&app, percent)
}

#[tauri::command]
pub fn detect_apo_config_dir() -> Result<Option<String>, String> {
    apo::detect_config_dir().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_apo_settings(app: AppHandle) -> Result<ApoSettings, String> {
    apo::get_settings(&app).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_apo_settings(app: AppHandle, settings: ApoSettings) -> Result<(), String> {
    apo::save_settings(&app, &settings).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn ensure_include_directive(config_dir: String) -> Result<IncludeResult, String> {
    apo::ensure_include_directive(&config_dir).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn write_eqbyear_preset(config_dir: String, content: String) -> Result<WriteResult, String> {
    apo::write_eqbyear_preset(&config_dir, &content).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn check_apo_status(config_dir: String) -> Result<ApoStatus, String> {
    apo::check_status(&config_dir).map_err(|e| e.to_string())
}
