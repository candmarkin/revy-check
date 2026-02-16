#[cfg(target_os = "linux")]
pub fn disable_alt_tab() {
    use std::process::Command;
    
    let _ = Command::new("gsettings")
        .args(&["set", "org.gnome.desktop.wm.keybindings", "switch-applications", "[]"])
        .output();
    
    let _ = Command::new("gsettings")
        .args(&["set", "org.gnome.desktop.wm.keybindings", "switch-windows", "[]"])
        .output();
}

#[cfg(target_os = "linux")]
pub fn restore_alt_tab() {
    use std::process::Command;
    
    let _ = Command::new("gsettings")
        .args(&["reset", "org.gnome.desktop.wm.keybindings", "switch-applications"])
        .output();
    
    let _ = Command::new("gsettings")
        .args(&["reset", "org.gnome.desktop.wm.keybindings", "switch-windows"])
        .output();
}

#[cfg(not(target_os = "linux"))]
pub fn disable_alt_tab() {}

#[cfg(not(target_os = "linux"))]
pub fn restore_alt_tab() {}

#[cfg(target_os = "linux")]
pub fn sync_ntp_time() {
    use std::process::Command;
    
    // Try to sync with NTP server
    let _ = Command::new("sudo")
        .args(&["ntpdate", "200.160.0.8"])
        .output();
}

#[cfg(not(target_os = "linux"))]
pub fn sync_ntp_time() {}
