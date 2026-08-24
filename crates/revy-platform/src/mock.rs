//! Fake platform with plausible data, so Phases 1-5 run on a dev machine with
//! no bench hardware. Real impls (Linux sysfs/CLI, Windows WMI/WinAPI) replace
//! this via `active_platform()` in Phases 2 and 3.

use crate::api::*;

pub struct MockPlatform;

impl MockPlatform {
    pub fn new() -> Self {
        MockPlatform
    }
}

impl Default for MockPlatform {
    fn default() -> Self {
        Self::new()
    }
}

impl SystemInfo for MockPlatform {
    fn system_info(&self) -> SysInfo {
        SysInfo {
            manufacturer: "MOCK".into(),
            product_name: "MockDevice".into(),
            serial: "MOCK-SERIAL-0001".into(),
            cpu: "Mock CPU @ 0.0GHz".into(),
            ram: "0.0 GB".into(),
            disk: "mockdisk 0G".into(),
            ip: "0.0.0.0".into(),
        }
    }
}

impl WifiScanner for MockPlatform {
    fn wifi_interface(&self) -> Option<String> {
        Some("wlan0".into())
    }

    fn wifi_scan(&self) -> Result<Vec<WifiNetwork>> {
        Ok(vec![
            WifiNetwork { ssid: "RedeCorporativa".into(), signal_dbm: -42, connected: true },
            WifiNetwork { ssid: "Visitantes".into(), signal_dbm: -67, connected: false },
            WifiNetwork { ssid: "Bancada-2G".into(), signal_dbm: -78, connected: false },
        ])
    }
}

impl EthernetInfo for MockPlatform {
    fn ethernet_carrier(&self, _iface: &str) -> bool {
        true
    }
}

impl UsbInfo for MockPlatform {
    fn usb_port_has_device(&self, _bus: &str, _port: &str) -> bool {
        true
    }
}

impl VideoOutputs for MockPlatform {
    fn video_outputs(&self, wanted: &[(String, String)]) -> Vec<VideoOutput> {
        wanted
            .iter()
            .map(|(label, entry)| VideoOutput {
                label: label.clone(),
                entry: entry.clone(),
                connected: true,
            })
            .collect()
    }
}

impl AudioJack for MockPlatform {
    fn headphone_connected(&self) -> bool {
        true
    }
}

impl SystemClock for MockPlatform {
    fn set_time(&self, _when: chrono::DateTime<chrono::Utc>) -> Result<()> {
        Ok(())
    }
}
