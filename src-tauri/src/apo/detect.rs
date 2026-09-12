use std::path::Path;

use super::ApoError;

#[cfg(windows)]
pub fn detect_config_dir() -> Result<Option<String>, ApoError> {
    use winreg::enums::HKEY_LOCAL_MACHINE;
    use winreg::RegKey;

    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    if let Ok(key) = hklm.open_subkey("SOFTWARE\\EqualizerAPO") {
        if let Ok(path) = key.get_value::<String, _>("ConfigPath") {
            if Path::new(&path).join("config.txt").is_file() {
                return Ok(Some(path));
            }
        }
    }

    let fallback = r"C:\Program Files\EqualizerAPO\config";
    if Path::new(fallback).join("config.txt").is_file() {
        return Ok(Some(fallback.to_string()));
    }

    Ok(None)
}

#[cfg(not(windows))]
pub fn detect_config_dir() -> Result<Option<String>, ApoError> {
    Err(ApoError::Unsupported)
}
