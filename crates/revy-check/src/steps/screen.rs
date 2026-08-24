//! Display color-cycle test (mirrors `screen.screen_step`).
//! ENTER cycles colors, SPACE finishes, then Y/N approve/reject.

use macroquad::prelude::*;

use crate::app::App;
use crate::ui::draw;

pub async fn run(app: &mut App) {
    let colors = [
        BLACK,
        WHITE,
        RED,
        GREEN,
        BLUE,
        YELLOW,
    ];
    let mut idx = 0usize;
    let mut test_done = false;

    loop {
        app.tick_global().await;

        if !test_done {
            if is_key_pressed(KeyCode::Enter) {
                idx = (idx + 1) % colors.len();
            }
            if is_key_pressed(KeyCode::Space) {
                test_done = true;
            }

            clear_background(colors[idx]);
            draw::system_overlay(&app.system_info, app.font());
            draw::text_right(
                "ENTER alterna cores, ESPACO finaliza o teste",
                screen_width() - 30.0,
                30.0,
                18,
                WHITE,
                app.font(),
            );
        } else {
            draw::screen_message(
                &app.system_info,
                &["Teste concluido!", "Aperte Y para APROVAR", "ou N para REPROVAR"],
                GREEN,
                app.font(),
            );

            if is_key_pressed(KeyCode::Y) {
                app.log.add_now("SCREEN_TEST", "APROVADO");
                return;
            }
            if is_key_pressed(KeyCode::N) {
                app.log.add_now("SCREEN_TEST", "REPROVADO");
                return;
            }
        }

        next_frame().await;
    }
}
