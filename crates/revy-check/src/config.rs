//! Which tests run for this device — the `fetch_device_info()` result.
//!
//! Phase 1 uses [`mock_config`]. Phase 5 replaces it with a MySQL lookup keyed
//! by the machine serial (see the plan) in `db.rs`.

/// A USB port to test, from `device_usb_ports` (`bus`, `port`, `label`).
#[derive(Debug, Clone)]
pub struct UsbPort {
    pub bus: String,
    pub port: String,
    pub label: String,
}

/// A video connector to test, from `device_video_ports` (`label`, `entry`).
#[derive(Debug, Clone)]
pub struct VideoPortSpec {
    pub label: String,
    pub entry: String,
}

/// The per-device feature flags + port maps that gate the state machine.
#[derive(Debug, Clone)]
pub struct DeviceConfig {
    pub manufacturer: String,
    pub product_name: String,
    pub port_map: Vec<UsbPort>,
    pub video_ports: Vec<VideoPortSpec>,
    pub has_embedded_screen: bool,
    pub has_embedded_keyboard: bool,
    pub has_ethernet_port: bool,
    pub eth_interface: String,
    pub has_speaker: bool,
    pub has_headphone_jack: bool,
    pub has_microphone: bool,
    pub has_wifi: bool,
    pub has_touchpad: bool,
    pub has_camera: bool,
}

impl Default for DeviceConfig {
    fn default() -> Self {
        DeviceConfig {
            manufacturer: String::new(),
            product_name: String::new(),
            port_map: Vec::new(),
            video_ports: Vec::new(),
            has_embedded_screen: false,
            has_embedded_keyboard: false,
            has_ethernet_port: false,
            eth_interface: "eth0".into(),
            has_speaker: false,
            has_headphone_jack: false,
            has_microphone: false,
            has_wifi: false,
            has_touchpad: false,
            has_camera: false,
        }
    }
}

/// Everything enabled, so the whole flow is walkable without a DB or hardware.
pub fn mock_config() -> DeviceConfig {
    DeviceConfig {
        manufacturer: "MOCK".into(),
        product_name: "MockDevice".into(),
        port_map: vec![
            UsbPort { bus: "1".into(), port: "1".into(), label: "USB Esquerda".into() },
            UsbPort { bus: "1".into(), port: "2".into(), label: "USB Direita".into() },
        ],
        video_ports: vec![
            VideoPortSpec { label: "HDMI".into(), entry: "card1-HDMI-A-1".into() },
            VideoPortSpec { label: "DisplayPort".into(), entry: "card1-DP-1".into() },
        ],
        has_embedded_screen: true,
        has_embedded_keyboard: true,
        has_ethernet_port: true,
        eth_interface: "eth0".into(),
        has_speaker: true,
        has_headphone_jack: true,
        has_microphone: true,
        has_wifi: true,
        has_touchpad: true,
        has_camera: true,
    }
}
