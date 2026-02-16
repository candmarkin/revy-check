use anyhow::Result;

#[cfg(target_os = "linux")]
pub fn get_device_info() -> Result<(String, String)> {
    use std::fs;

    let manufacturer = fs::read_to_string("/sys/class/dmi/id/sys_vendor")
        .unwrap_or_else(|_| "Unknown".to_string())
        .trim()
        .to_string();

    let product_name = if manufacturer.to_uppercase().contains("LENOVO") {
        fs::read_to_string("/sys/class/dmi/id/product_version")
            .unwrap_or_else(|_| "UnknownDevice".to_string())
    } else {
        fs::read_to_string("/sys/class/dmi/id/product_name")
            .unwrap_or_else(|_| "UnknownDevice".to_string())
    };

    Ok((manufacturer, product_name.trim().to_string()))
}

#[cfg(not(target_os = "linux"))]
pub fn get_device_info() -> Result<(String, String)> {
    Ok(("Unknown".to_string(), "UnknownDevice".to_string()))
}
