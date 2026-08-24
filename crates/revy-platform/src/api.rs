//! Platform-abstraction contract.
//!
//! Every OS-specific data source the app needs is expressed as a trait here.
//! `Platform` is the aggregate the app holds as `Box<dyn Platform>`; a blanket
//! impl gives it to anything that implements all the sub-traits, so an impl
//! only has to implement the pieces it cares about.
//!
//! Linux data sources (current Python app) and their Windows counterparts:
//! - SystemInfo: `/sys/class/dmi/*`, `/proc/*`, `lsblk`, `hostname -I`
//!               -> WMI Win32_BIOS/ComputerSystem/Processor/DiskDrive + GetAdaptersAddresses
//! - WifiScanner: `iw`/`ip`/`nmcli` -> wlanapi (WlanScan/WlanGetNetworkBssList)
//! - EthernetInfo: `/sys/class/net/<if>/carrier` -> GetAdaptersAddresses IfOperStatusUp
//! - UsbInfo: `lsusb -t` -> SetupAPI / WMI Win32_DiskDrive (degrades to presence)
//! - VideoOutputs: `/sys/class/drm/*/status` -> QueryDisplayConfig (degrades to count)
//! - AudioJack: pulsectl sink port -> MMDevice form-factor (degrades)
//! - SystemClock: `sudo date` -> clock_settime (Linux) / SetSystemTime (Windows)

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum PlatformError {
    #[error("command failed: {0}")]
    Command(String),
    #[error("capability not supported on this platform: {0}")]
    Unsupported(String),
    #[error("{0}")]
    Other(String),
}

pub type Result<T> = std::result::Result<T, PlatformError>;

/// Serial/CPU/RAM/disk/IP overlay data (mirrors `system_info.get_system_info`).
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SysInfo {
    pub manufacturer: String,
    pub product_name: String,
    pub serial: String,
    pub cpu: String,
    pub ram: String,
    pub disk: String,
    pub ip: String,
}

/// One scanned wifi network (mirrors the rows `wifi.py` renders as signal bars).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WifiNetwork {
    pub ssid: String,
    /// Signal strength in dBm (negative; closer to 0 is stronger).
    pub signal_dbm: i32,
    pub connected: bool,
}

/// A video connector under test (mirrors `device_video_ports` rows).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VideoOutput {
    pub label: String,
    /// DRM entry name on Linux (e.g. `card1-HDMI-A-1`); free-form on Windows.
    pub entry: String,
    pub connected: bool,
}

pub trait SystemInfo {
    fn system_info(&self) -> SysInfo;
}

pub trait WifiScanner {
    fn wifi_interface(&self) -> Option<String>;
    fn wifi_scan(&self) -> Result<Vec<WifiNetwork>>;
}

pub trait EthernetInfo {
    fn ethernet_carrier(&self, iface: &str) -> bool;
}

pub trait UsbInfo {
    /// Whether a USB mass-storage device is present on the given bus/port
    /// (Python `usb.port_has_device`). Windows degrades to "any USB storage".
    fn usb_port_has_device(&self, bus: &str, port: &str) -> bool;
}

pub trait VideoOutputs {
    /// Report connection status for the requested `(label, entry)` connectors.
    fn video_outputs(&self, wanted: &[(String, String)]) -> Vec<VideoOutput>;
}

pub trait AudioJack {
    fn headphone_connected(&self) -> bool;
}

pub trait SystemClock {
    /// Set the system clock (needs root / SeSystemtimePrivilege).
    fn set_time(&self, when: chrono::DateTime<chrono::Utc>) -> Result<()>;
}

/// Aggregate the app depends on. Implemented for free by anything that
/// implements every sub-trait.
pub trait Platform:
    SystemInfo + WifiScanner + EthernetInfo + UsbInfo + VideoOutputs + AudioJack + SystemClock
{
}

impl<T> Platform for T where
    T: SystemInfo + WifiScanner + EthernetInfo + UsbInfo + VideoOutputs + AudioJack + SystemClock
{
}
