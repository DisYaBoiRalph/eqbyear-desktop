mod config;
mod detect;
mod error;
mod settings;

pub use config::{check_status, ensure_include_directive, write_eqbyear_preset};
pub use detect::detect_config_dir;
pub use error::ApoError;
pub use settings::{get_settings, save_settings};

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApoSettings {
    pub config_dir: Option<String>,
    pub sync_enabled: bool,
}

impl Default for ApoSettings {
    fn default() -> Self {
        ApoSettings { config_dir: None, sync_enabled: false }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct IncludeResult {
    pub already_present: bool,
    pub backed_up: bool,
    pub backup_path: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct WriteResult {
    pub written_at: String,
    pub bytes_written: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct ApoStatus {
    pub config_dir_exists: bool,
    pub config_txt_exists: bool,
    pub include_present: bool,
    pub preset_exists: bool,
    pub preset_path: String,
}
