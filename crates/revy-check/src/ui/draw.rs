//! Shared drawing helpers (mirrors `gui.draw_text` + `system_info.draw_system_info`).

use macroquad::prelude::*;
use revy_platform::SysInfo;

/// Opaque RGB color.
pub fn rgb(r: u8, g: u8, b: u8) -> Color {
    Color::from_rgba(r, g, b, 255)
}

/// Draw left-aligned text with `y` as the baseline.
pub fn text_left(text: &str, x: f32, y: f32, size: u16, color: Color, font: Option<&Font>) {
    draw_text_ex(
        text,
        x,
        y,
        TextParams { font, font_size: size, color, ..Default::default() },
    );
}

/// Draw text centered on `(cx, cy)`.
pub fn text_centered(text: &str, cx: f32, cy: f32, size: u16, color: Color, font: Option<&Font>) {
    let d = measure_text(text, font, size, 1.0);
    draw_text_ex(
        text,
        cx - d.width / 2.0,
        cy + d.height / 2.0,
        TextParams { font, font_size: size, color, ..Default::default() },
    );
}

/// Draw text whose right edge sits at `right_x`, baseline `y`.
pub fn text_right(text: &str, right_x: f32, y: f32, size: u16, color: Color, font: Option<&Font>) {
    let d = measure_text(text, font, size, 1.0);
    draw_text_ex(
        text,
        right_x - d.width,
        y,
        TextParams { font, font_size: size, color, ..Default::default() },
    );
}

/// System-info overlay, top-left, yellow (mirrors `draw_system_info`).
pub fn system_overlay(info: &SysInfo, font: Option<&Font>) {
    let yellow = rgb(255, 255, 0);
    let lines = [
        format!("SERIAL: {}", info.serial),
        format!("CPU: {}", info.cpu),
        format!("RAM: {}", info.ram),
        format!("DISK: {}", info.disk),
        format!("IP: {}", info.ip),
    ];
    let mut y = 24.0;
    for line in &lines {
        text_left(line, 10.0, y, 18, yellow, font);
        y += 20.0;
    }
}

/// Full-screen centered message over black, with the system overlay
/// (mirrors `gui.draw_text`). Caller is responsible for `next_frame().await`.
pub fn screen_message(info: &SysInfo, lines: &[&str], color: Color, font: Option<&Font>) {
    clear_background(BLACK);
    system_overlay(info, font);
    let mut y = screen_height() / 3.0;
    for line in lines {
        text_centered(line, screen_width() / 2.0, y, 22, color, font);
        y += 50.0;
    }
}
