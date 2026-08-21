//! Test log — mirrors `app_state.LOG_DATA` + `add_log` + `save_log`'s JSON write.

use serde::Serialize;
use std::io;
use std::path::Path;

/// One checklist entry. Field order/names match the Python dicts so existing
/// JSON/DB consumers stay compatible.
#[derive(Debug, Clone, Serialize)]
pub struct LogEntry {
    pub step: String,
    pub time: String,
    pub result: String,
}

#[derive(Debug, Default)]
pub struct Log {
    pub entries: Vec<LogEntry>,
}

/// Timestamp in the same shape as Python's `str(datetime.now())`.
pub fn now_string() -> String {
    chrono::Local::now().format("%Y-%m-%d %H:%M:%S%.6f").to_string()
}

impl Log {
    pub fn new() -> Self {
        Log { entries: Vec::new() }
    }

    /// Append `entry`, deduplicated by `step` (matches Python `add_log`).
    pub fn add(&mut self, entry: LogEntry) {
        if !self.entries.iter().any(|e| e.step == entry.step) {
            self.entries.push(entry);
        }
    }

    /// Convenience: add `step`/`result` stamped with the current time.
    pub fn add_now(&mut self, step: &str, result: &str) {
        self.add(LogEntry {
            step: step.to_owned(),
            time: now_string(),
            result: result.to_owned(),
        });
    }

    /// Write `checklist_log.json` (pretty, indent 2 — same as the Python dump).
    pub fn save_json<P: AsRef<Path>>(&self, path: P) -> io::Result<()> {
        let json = serde_json::to_string_pretty(&self.entries)
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
        std::fs::write(path, json)
    }

    /// Last `n` entries, for the save-log preview screen.
    pub fn tail(&self, n: usize) -> &[LogEntry] {
        let start = self.entries.len().saturating_sub(n);
        &self.entries[start..]
    }
}
