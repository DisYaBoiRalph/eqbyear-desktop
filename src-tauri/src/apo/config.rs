use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use super::{ApoError, ApoStatus, IncludeResult, WriteResult};

const PRESET_FILENAME: &str = "eqbyear.txt";
const INCLUDE_LINE: &str = "Include: eqbyear.txt";

fn config_txt_path(config_dir: &str) -> PathBuf {
    Path::new(config_dir).join("config.txt")
}

fn preset_path(config_dir: &str) -> PathBuf {
    Path::new(config_dir).join(PRESET_FILENAME)
}

// Also matches a commented-out line, so a manually disabled include is not re-added.
fn line_is_include_directive(line: &str) -> bool {
    line.trim().trim_start_matches('#').trim().eq_ignore_ascii_case(INCLUDE_LINE)
}

// Temp file plus rename, so EqualizerAPO never reads a half-written file.
fn write_atomic(path: &Path, content: &str) -> Result<(), ApoError> {
    let tmp = path.with_extension("tmp");
    fs::write(&tmp, content)?;
    fs::rename(&tmp, path)?;
    Ok(())
}

// Appends the include as the last line, once, after backing up config.txt.
pub fn ensure_include_directive(config_dir: &str) -> Result<IncludeResult, ApoError> {
    let path = config_txt_path(config_dir);
    if !path.is_file() {
        return Err(ApoError::NotFound(
            "config.txt not found. Is EqualizerAPO installed?".to_string(),
        ));
    }

    let original = fs::read_to_string(&path)?;
    let already_present = original.lines().any(line_is_include_directive);
    if already_present {
        return Ok(IncludeResult { already_present: true, backed_up: false, backup_path: None });
    }

    let stamp = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    let backup_path = path.with_file_name(format!("config.txt.bak-{stamp}"));
    fs::copy(&path, &backup_path)?;

    let mut updated = original;
    if !updated.ends_with('\n') {
        updated.push('\n');
    }
    updated.push_str(INCLUDE_LINE);
    updated.push('\n');
    write_atomic(&path, &updated)?;

    Ok(IncludeResult {
        already_present: false,
        backed_up: true,
        backup_path: Some(backup_path.to_string_lossy().to_string()),
    })
}

pub fn write_eqbyear_preset(config_dir: &str, content: &str) -> Result<WriteResult, ApoError> {
    let mut body = content.to_string();
    if !body.ends_with('\n') {
        body.push('\n');
    }
    write_atomic(&preset_path(config_dir), &body)?;

    let written_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis().to_string())
        .unwrap_or_default();
    Ok(WriteResult { written_at, bytes_written: body.len() })
}

pub fn check_status(config_dir: &str) -> Result<ApoStatus, ApoError> {
    let dir = Path::new(config_dir);
    let config_txt = config_txt_path(config_dir);
    let preset = preset_path(config_dir);

    let config_txt_exists = config_txt.is_file();
    // Unlike the guard above, only an active line counts as present.
    let include_present = config_txt_exists
        && fs::read_to_string(&config_txt)
            .map(|s| s.lines().any(|line| line.trim().eq_ignore_ascii_case(INCLUDE_LINE)))
            .unwrap_or(false);

    Ok(ApoStatus {
        config_dir_exists: dir.is_dir(),
        config_txt_exists,
        include_present,
        preset_exists: preset.is_file(),
        preset_path: preset.to_string_lossy().to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU32, Ordering};

    struct TempDir(PathBuf);

    impl TempDir {
        fn new(tag: &str) -> Self {
            static COUNTER: AtomicU32 = AtomicU32::new(0);
            let n = COUNTER.fetch_add(1, Ordering::SeqCst);
            let dir = std::env::temp_dir().join(format!("eqbyear-apo-test-{tag}-{n}"));
            fs::create_dir_all(&dir).unwrap();
            TempDir(dir)
        }

        fn path(&self) -> &str {
            self.0.to_str().unwrap()
        }
    }

    impl Drop for TempDir {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    fn write_config(dir: &TempDir, content: &str) {
        fs::write(Path::new(dir.path()).join("config.txt"), content).unwrap();
    }

    fn read_config(dir: &TempDir) -> String {
        fs::read_to_string(Path::new(dir.path()).join("config.txt")).unwrap()
    }

    #[test]
    fn ensure_include_directive_appends_once_at_the_bottom() {
        let dir = TempDir::new("include");
        write_config(&dir, "Preamp: -4 dB\nInclude: peace.txt\n# Channel: L");

        let result = ensure_include_directive(dir.path()).unwrap();
        assert!(!result.already_present);
        assert!(result.backed_up);
        assert!(result.backup_path.is_some());

        let updated = read_config(&dir);
        assert_eq!(
            updated,
            "Preamp: -4 dB\nInclude: peace.txt\n# Channel: L\nInclude: eqbyear.txt\n"
        );

        let backup = fs::read_to_string(result.backup_path.unwrap()).unwrap();
        assert_eq!(backup, "Preamp: -4 dB\nInclude: peace.txt\n# Channel: L");
    }

    #[test]
    fn ensure_include_directive_is_idempotent() {
        let dir = TempDir::new("idempotent");
        write_config(&dir, "Preamp: -4 dB\n");

        let first = ensure_include_directive(dir.path()).unwrap();
        assert!(!first.already_present);
        let after_first = read_config(&dir);

        let second = ensure_include_directive(dir.path()).unwrap();
        assert!(second.already_present);
        assert!(!second.backed_up);
        assert_eq!(read_config(&dir), after_first);

        let backups = fs::read_dir(dir.path())
            .unwrap()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_name().to_string_lossy().starts_with("config.txt.bak-"))
            .count();
        assert_eq!(backups, 1);
    }

    #[test]
    fn ensure_include_directive_respects_a_manually_commented_line() {
        let dir = TempDir::new("commented");
        write_config(&dir, "Preamp: -4 dB\n# Include: eqbyear.txt\n");

        let result = ensure_include_directive(dir.path()).unwrap();
        assert!(result.already_present);
        assert!(!result.backed_up);
        assert_eq!(read_config(&dir), "Preamp: -4 dB\n# Include: eqbyear.txt\n");
    }

    #[test]
    fn ensure_include_directive_errors_without_config_txt() {
        let dir = TempDir::new("missing");
        let err = ensure_include_directive(dir.path()).unwrap_err();
        assert!(matches!(err, ApoError::NotFound(_)));
    }

    #[test]
    fn write_eqbyear_preset_writes_the_preset_file_only() {
        let dir = TempDir::new("preset");
        write_config(&dir, "Preamp: -4 dB\n");

        let result = write_eqbyear_preset(dir.path(), "Preamp: -2.0 dB\nFilter 1: ON PK Fc 105 Hz Gain 2.0 dB Q 0.70").unwrap();
        assert!(result.bytes_written > 0);

        let preset = fs::read_to_string(Path::new(dir.path()).join(PRESET_FILENAME)).unwrap();
        assert_eq!(preset, "Preamp: -2.0 dB\nFilter 1: ON PK Fc 105 Hz Gain 2.0 dB Q 0.70\n");
        assert_eq!(read_config(&dir), "Preamp: -4 dB\n");
    }

    #[test]
    fn check_status_reports_accurately() {
        let dir = TempDir::new("status");
        write_config(&dir, "Preamp: -4 dB\n");

        let before = check_status(dir.path()).unwrap();
        assert!(before.config_dir_exists);
        assert!(before.config_txt_exists);
        assert!(!before.include_present);
        assert!(!before.preset_exists);

        ensure_include_directive(dir.path()).unwrap();
        write_eqbyear_preset(dir.path(), "Preamp: 0.0 dB").unwrap();

        let after = check_status(dir.path()).unwrap();
        assert!(after.include_present);
        assert!(after.preset_exists);
    }
}
