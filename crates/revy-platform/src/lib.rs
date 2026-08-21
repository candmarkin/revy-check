//! `revy-platform` — the OS-abstraction layer for revy-check.
//!
//! The app holds a `Box<dyn Platform>` and never touches sysfs / WMI directly.
//! `active_platform()` picks the concrete impl at compile time.

pub mod api;
pub mod mock;

pub use api::*;

/// The platform impl for the current target.
///
/// Phase 1 always returns [`mock::MockPlatform`]. Phases 2/3 switch this to a
/// `#[cfg(target_os = ...)]` selection between `LinuxPlatform` / `WindowsPlatform`.
pub fn active_platform() -> Box<dyn Platform> {
    // TODO(phase 2/3):
    //   #[cfg(target_os = "linux")]   return Box::new(linux::LinuxPlatform::new());
    //   #[cfg(target_os = "windows")] return Box::new(windows::WindowsPlatform::new());
    Box::new(mock::MockPlatform::new())
}

/// RAII kiosk lock. Engaging it disables the OS task-switcher; dropping it
/// (including on panic) restores the previous state — this replaces the Python
/// `try/finally` around `disable_alt_tab`/`restore_alt_tab`.
pub struct KioskGuard {
    restore: Option<Box<dyn FnOnce()>>,
}

impl KioskGuard {
    /// A guard that does nothing (mock / platforms without a lock).
    pub fn noop() -> Self {
        KioskGuard { restore: None }
    }

    /// A guard whose drop runs `restore`.
    pub fn with_restore(restore: Box<dyn FnOnce()>) -> Self {
        KioskGuard { restore: Some(restore) }
    }
}

impl Drop for KioskGuard {
    fn drop(&mut self) {
        if let Some(restore) = self.restore.take() {
            restore();
        }
    }
}

/// Engage the kiosk task-switch lock for the current target.
///
/// Phase 1 is a no-op. Phase 2 disables GNOME Alt-Tab via `gsettings`; Phase 3
/// installs a low-level Windows keyboard hook (note: a real Windows kiosk should
/// use Assigned Access / Shell Launcher — see the plan's risks section).
pub fn engage_kiosk_lock() -> KioskGuard {
    KioskGuard::noop()
}
