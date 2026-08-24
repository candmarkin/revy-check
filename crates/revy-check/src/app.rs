//! Runtime state + shared behavior. Replaces the Python `app_state` globals with
//! a single owned `App` struct threaded through the steps.

use macroquad::prelude::*;
use revy_platform::{Platform, SysInfo};

use crate::config::{mock_config, DeviceConfig};
use crate::testlog::Log;
use crate::ui::draw;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Prod,
    Dev,
}

pub struct App {
    pub platform: Box<dyn Platform>,
    pub font: Option<Font>,
    pub mode: Mode,
    pub dev_password: String,
    pub log: Log,
    pub config: DeviceConfig,
    pub system_info: SysInfo,
}

impl App {
    pub fn new(platform: Box<dyn Platform>, font: Option<Font>) -> Self {
        App {
            platform,
            font,
            mode: Mode::Prod,
            dev_password: "dev123".into(), // Phase 5: load from config/env, not source.
            log: Log::new(),
            config: mock_config(),
            system_info: SysInfo::default(),
        }
    }

    /// Borrow the loaded font, if any (else macroquad's built-in font is used).
    pub fn font(&self) -> Option<&Font> {
        self.font.as_ref()
    }

    /// Per-frame global input: ESC-to-exit in DEV and the DEV-unlock hotkey
    /// (LCtrl+LShift+D+V). Call once at the top of every step's frame.
    pub async fn tick_global(&mut self) {
        if self.mode == Mode::Dev && is_key_pressed(KeyCode::Escape) {
            self.save_and_exit();
        }

        if self.mode == Mode::Prod
            && is_key_down(KeyCode::LeftControl)
            && is_key_down(KeyCode::LeftShift)
            && is_key_down(KeyCode::D)
            && is_key_down(KeyCode::V)
        {
            let pw = self.prompt_password().await;
            if pw == self.dev_password {
                log::info!("DEV MODE UNLOCKED via hotkey");
                self.mode = Mode::Dev;
            } else {
                log::info!("senha incorreta");
            }
        }
    }

    /// Write the JSON log and terminate (DEV ESC / window close).
    /// Phase 5 will run the full `save_log` preview/DB flow here instead.
    pub fn save_and_exit(&self) -> ! {
        let _ = self.log.save_json("checklist_log.json");
        std::process::exit(0);
    }

    /// Blocking DEV-password prompt (mirrors `app_flow.prompt_password`).
    pub async fn prompt_password(&mut self) -> String {
        let mut input = String::new();
        loop {
            while let Some(c) = get_char_pressed() {
                if !c.is_control() {
                    input.push(c);
                }
            }
            if is_key_pressed(KeyCode::Enter) || is_key_pressed(KeyCode::KpEnter) {
                return input;
            }
            if is_key_pressed(KeyCode::Backspace) {
                input.pop();
            }

            clear_background(draw::rgb(50, 50, 50));
            draw::text_left("Digite senha DEV:", 50.0, 200.0, 28, draw::rgb(255, 255, 0), self.font());
            draw::text_left(&"*".repeat(input.len()), 50.0, 240.0, 28, WHITE, self.font());
            next_frame().await;
        }
    }
}
