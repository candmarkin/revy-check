//! revy-check — cross-platform (Linux + Windows) Rust rewrite of the Python
//! Pygame kiosk QA station. Entry point + window config (mirrors `main.py`).

use macroquad::prelude::*;

mod app;
mod config;
// `log.rs` is the test-log module; aliased so it doesn't shadow the `log` crate.
#[path = "log.rs"]
mod testlog;
mod state;
mod steps;
mod ui;

use app::App;
use revy_platform::SystemInfo; // brings `system_info()` into scope for the trait object

fn window_conf() -> Conf {
    Conf {
        window_title: "Checklist Tecnico Completo".to_owned(),
        window_width: 1280,
        window_height: 720,
        fullscreen: true,
        high_dpi: true,
        ..Default::default()
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    env_logger::init();

    // Kiosk task-switch lock; restored on drop (Phase 2/3 make it real).
    let _kiosk = revy_platform::engage_kiosk_lock();

    show_mouse(true);

    let font = load_ttf_font("assets/DejaVuSans.ttf").await.ok();
    let platform = revy_platform::active_platform();
    let mut app = App::new(platform, font);

    // Phase 5: wait_for_db_connection() + fetch_device_info() populate this from
    // MySQL. Phase 1 uses the mock config + real platform system info.
    app.config = config::mock_config();
    app.system_info = app.platform.system_info();

    state::run(&mut app).await;
}
