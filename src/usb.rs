use anyhow::Result;

#[cfg(target_os = "linux")]
pub fn check_usb_device(bus: &str, port: &str) -> bool {
    use std::process::Command;

    if let Ok(output) = Command::new("lsusb").arg("-t").output() {
        if let Ok(text) = String::from_utf8(output.stdout) {
            for bus_section in text.split("/:") {
                if bus_section.contains(bus) && bus_section.contains("Class=Mass Storage") && bus_section.contains(port) {
                    return true;
                }
            }
        }
    }
    false
}

#[cfg(not(target_os = "linux"))]
pub fn check_usb_device(_bus: &str, _port: &str) -> bool {
    false
}
