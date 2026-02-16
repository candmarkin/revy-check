#[cfg(target_os = "linux")]
pub fn check_ethernet_connection(interface: &str) -> bool {
    use std::fs;

    let carrier_path = format!("/sys/class/net/{}/carrier", interface);
    fs::read_to_string(carrier_path)
        .map(|s| s.trim() == "1")
        .unwrap_or(false)
}

#[cfg(not(target_os = "linux"))]
pub fn check_ethernet_connection(_interface: &str) -> bool {
    false
}
