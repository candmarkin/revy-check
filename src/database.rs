use crate::config::{DeviceConfig, VideoPort};
use crate::device_info::get_device_info;
use crate::log_manager::LogEntry;
use anyhow::{anyhow, Result};
use mysql::prelude::*;
use mysql::{Pool, PooledConn};

const DB_HOST: &str = "revy.selbetti.com.br";
const DB_PORT: u16 = 3306;
const DB_USER: &str = "drack";
const DB_PASSWORD: &str = "jdVg2dF2@";
const DB_NAME: &str = "revycheck";

fn get_connection() -> Result<PooledConn> {
    let url = format!(
        "mysql://{}:{}@{}:{}/{}",
        DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
    );
    let pool = Pool::new(url.as_str())?;
    Ok(pool.get_conn()?)
}

pub fn check_db_connection() -> bool {
    get_connection().is_ok()
}

pub fn fetch_device_info() -> Result<DeviceConfig> {
    let (manufacturer, product_name) = get_device_info()?;
    let mut conn = get_connection()?;

    // Get device ID
    let device_id: Option<u32> = conn.exec_first(
        "SELECT id FROM devices WHERE name = ?",
        (&product_name,),
    )?;

    let device_id = device_id.ok_or_else(|| {
        anyhow!("Device '{}' not found in database. Please register it first.", product_name)
    })?;

    // Get USB ports
    let port_map: Vec<(String, String, String)> = conn
        .exec_map(
            "SELECT bus, port, label FROM device_usb_ports WHERE device_id = ?",
            (device_id,),
            |(bus, port, label)| (bus, port, label),
        )?;

    // Get video ports
    let video_ports: Vec<VideoPort> = conn
        .exec_map(
            "SELECT label, entry FROM device_video_ports WHERE device_id = ?",
            (device_id,),
            |(label, entry)| VideoPort { label, entry },
        )?;

    // Get device details
    let device: Option<(bool, bool, bool, String, bool, bool, bool)> = conn.exec_first(
        "SELECT has_embedded_screen, has_embedded_keyboard, has_ethernet, \
         eth_interface, has_speaker, has_headphone_jack, has_microphone \
         FROM devices WHERE id = ?",
        (device_id,),
    )?;

    let (has_screen, has_keyboard, has_eth, eth_interface, has_speaker, has_headphone, has_mic) =
        device.ok_or_else(|| anyhow!("Could not fetch device details"))?;

    Ok(DeviceConfig {
        manufacturer,
        product_name,
        port_map,
        video_ports,
        has_embedded_screen: has_screen,
        has_embedded_keyboard: has_keyboard,
        has_ethernet_port: has_eth,
        eth_interface,
        has_speaker,
        has_headphone_jack: has_headphone,
        has_microphone: has_mic,
    })
}

pub fn send_log_to_db(logs: &[LogEntry]) -> Result<()> {
    let mut conn = get_connection()?;
    
    let device_serial = get_device_serial()?;

    for entry in logs {
        let approved = entry.result == "APROVADO";
        conn.exec_drop(
            "INSERT INTO logs (device_serial, step, time, approved) VALUES (?, ?, ?, ?)",
            (&device_serial, &entry.step, entry.time, approved),
        )?;
    }

    Ok(())
}

#[cfg(target_os = "linux")]
fn get_device_serial() -> Result<String> {
    use std::fs;
    let serial = fs::read_to_string("/sys/class/dmi/id/product_serial")
        .unwrap_or_else(|_| "unknown".to_string());
    Ok(serial.trim().to_string())
}

#[cfg(not(target_os = "linux"))]
fn get_device_serial() -> Result<String> {
    Ok("unknown".to_string())
}
