use crate::config::VideoPort;

pub struct VideoPortStatus {
    pub label: String,
    pub entry: String,
    pub connected: bool,
}

#[cfg(target_os = "linux")]
pub fn check_video_ports(ports: &[VideoPort]) -> Vec<VideoPortStatus> {
    use std::fs;

    ports
        .iter()
        .map(|port| {
            let status_path = format!("/sys/class/drm/{}/status", port.entry);
            let connected = fs::read_to_string(&status_path)
                .map(|s| s.trim() == "connected")
                .unwrap_or(false);

            VideoPortStatus {
                label: port.label.clone(),
                entry: port.entry.clone(),
                connected,
            }
        })
        .collect()
}

#[cfg(not(target_os = "linux"))]
pub fn check_video_ports(ports: &[VideoPort]) -> Vec<VideoPortStatus> {
    ports
        .iter()
        .map(|port| VideoPortStatus {
            label: port.label.clone(),
            entry: port.entry.clone(),
            connected: false,
        })
        .collect()
}
