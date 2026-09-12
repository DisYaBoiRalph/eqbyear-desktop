use std::fs;
use std::path::PathBuf;

use tauri::{AppHandle, Manager};

use super::{ApoError, ApoSettings};

fn settings_path(app: &AppHandle) -> Result<PathBuf, ApoError> {
    let dir = app.path().app_config_dir().map_err(|e| ApoError::NotFound(e.to_string()))?;
    fs::create_dir_all(&dir)?;
    Ok(dir.join("settings.json"))
}

pub fn get_settings(app: &AppHandle) -> Result<ApoSettings, ApoError> {
    let path = settings_path(app)?;
    if !path.is_file() {
        return Ok(ApoSettings::default());
    }
    let text = fs::read_to_string(&path)?;
    Ok(serde_json::from_str(&text).unwrap_or_default())
}

pub fn save_settings(app: &AppHandle, settings: &ApoSettings) -> Result<(), ApoError> {
    let path = settings_path(app)?;
    let text = serde_json::to_string_pretty(settings).map_err(|e| ApoError::NotFound(e.to_string()))?;
    fs::write(&path, text)?;
    Ok(())
}
