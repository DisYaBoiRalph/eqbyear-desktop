use std::fmt;

#[derive(Debug)]
pub enum ApoError {
    Io(std::io::Error),
    NotFound(String),
    // Only constructed on non-Windows builds (see apo/detect.rs).
    #[allow(dead_code)]
    Unsupported,
}

impl fmt::Display for ApoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ApoError::Io(e) => write!(f, "{e}"),
            ApoError::NotFound(msg) => write!(f, "{msg}"),
            ApoError::Unsupported => write!(f, "EqualizerAPO integration is only available on Windows."),
        }
    }
}

impl From<std::io::Error> for ApoError {
    fn from(e: std::io::Error) -> Self {
        ApoError::Io(e)
    }
}
