use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceConfig {
    pub manufacturer: String,
    pub product_name: String,
    pub port_map: Vec<(String, String, String)>, // (bus, port, label)
    pub video_ports: Vec<VideoPort>,
    pub has_embedded_screen: bool,
    pub has_embedded_keyboard: bool,
    pub has_ethernet_port: bool,
    pub eth_interface: String,
    pub has_speaker: bool,
    pub has_headphone_jack: bool,
    pub has_microphone: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VideoPort {
    pub label: String,
    pub entry: String,
}

impl Default for DeviceConfig {
    fn default() -> Self {
        Self {
            manufacturer: String::new(),
            product_name: String::new(),
            port_map: Vec::new(),
            video_ports: Vec::new(),
            has_embedded_screen: true,
            has_embedded_keyboard: true,
            has_ethernet_port: false,
            eth_interface: "eth0".to_string(),
            has_speaker: true,
            has_headphone_jack: true,
            has_microphone: true,
        }
    }
}
