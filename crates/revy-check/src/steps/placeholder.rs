//! Placeholder for the hardware-backed steps (wifi, camera, usb, video, audio,
//! ethernet). Phase 1 shows a confirm screen and logs the operator's verdict so
//! the whole flow is walkable; the real implementations land in Phases 2 and 4
//! and call into the `revy-platform` traits.

use macroquad::prelude::*;

use crate::app::App;
use crate::ui::draw;

/// Show `title`/`subtitle`, wait for ENTER (approve) or N (reject), log `log_step`.
pub async fn confirm(app: &mut App, title: &str, subtitle: &str, log_step: &str) {
    loop {
        app.tick_global().await;

        if is_key_pressed(KeyCode::Enter) || is_key_pressed(KeyCode::KpEnter) {
            app.log.add_now(log_step, "APROVADO");
            return;
        }
        if is_key_pressed(KeyCode::N) {
            app.log.add_now(log_step, "REPROVADO");
            return;
        }

        draw::screen_message(
            &app.system_info,
            &[title, subtitle, "", "ENTER = APROVADO      N = REPROVADO"],
            WHITE,
            app.font(),
        );
        draw::text_centered(
            "(placeholder — teste real na Phase 2/4)",
            screen_width() / 2.0,
            screen_height() - 40.0,
            18,
            draw::rgb(150, 150, 150),
            app.font(),
        );
        next_frame().await;
    }
}
