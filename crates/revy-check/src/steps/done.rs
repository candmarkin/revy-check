//! Final state: log preview + save (mirrors `main.DONE` + `save_log.save_log`).
//! Phase 1 writes the JSON and mocks the "Enviar" DB push (real MySQL is Phase 5).

use macroquad::prelude::*;

use crate::app::App;
use crate::ui::draw;

enum Decision {
    Send,
    Cancel,
}

pub async fn run(app: &mut App) {
    app.log.add_now("TEST_STOP", "APROVADO");

    let decision = preview(app).await;
    let _ = app.log.save_json("checklist_log.json");

    match decision {
        Decision::Send => {
            // Phase 5: push each entry into the MySQL `logs` table with retry UI.
            message(app, &["Log salvo (JSON).", "Envio ao banco: Phase 5."], draw::rgb(0, 180, 0), 2.0).await;
        }
        Decision::Cancel => {
            message(app, &["Envio cancelado pelo usuario."], draw::rgb(200, 0, 0), 2.0).await;
        }
    }

    // Final confirmation screen (white, ~5s), matching the Python ending.
    let t0 = get_time();
    while get_time() - t0 < 5.0 {
        app.tick_global().await;
        clear_background(WHITE);
        draw::text_centered(
            "Todos os testes concluidos!",
            screen_width() / 2.0,
            screen_height() / 2.0,
            26,
            BLACK,
            app.font(),
        );
        next_frame().await;
    }
}

async fn preview(app: &mut App) -> Decision {
    loop {
        app.tick_global().await;

        let w = screen_width();
        let h = screen_height();
        let (mx, my) = mouse_position();
        let mouse = vec2(mx, my);
        let send_btn = Rect::new(w / 2.0 - 160.0, h - 80.0, 140.0, 50.0);
        let cancel_btn = Rect::new(w / 2.0 + 20.0, h - 80.0, 140.0, 50.0);

        if is_mouse_button_pressed(MouseButton::Left) {
            if send_btn.contains(mouse) {
                return Decision::Send;
            }
            if cancel_btn.contains(mouse) {
                return Decision::Cancel;
            }
        }

        clear_background(WHITE);
        draw::text_left("Pre-visualizacao do log:", 50.0, 60.0, 20, BLACK, app.font());

        let mut y = 100.0;
        for entry in app.log.tail(15) {
            let line = format!("{} | {} | {}", entry.step, entry.result, entry.time);
            draw::text_left(&line, 60.0, y, 14, BLACK, app.font());
            y += 25.0;
            if y > h - 120.0 {
                draw::text_left("... (log truncado) ...", 60.0, y, 14, draw::rgb(150, 0, 0), app.font());
                break;
            }
        }

        draw_rectangle(send_btn.x, send_btn.y, send_btn.w, send_btn.h, draw::rgb(0, 200, 0));
        draw_rectangle(cancel_btn.x, cancel_btn.y, cancel_btn.w, cancel_btn.h, draw::rgb(200, 0, 0));
        draw::text_centered("Enviar", send_btn.x + send_btn.w / 2.0, send_btn.y + send_btn.h / 2.0, 18, WHITE, app.font());
        draw::text_centered("Cancelar", cancel_btn.x + cancel_btn.w / 2.0, cancel_btn.y + cancel_btn.h / 2.0, 18, WHITE, app.font());

        next_frame().await;
    }
}

/// Show a centered message for `secs` seconds.
async fn message(app: &mut App, lines: &[&str], color: Color, secs: f64) {
    let t0 = get_time();
    while get_time() - t0 < secs {
        app.tick_global().await;
        draw::screen_message(&app.system_info, lines, color, app.font());
        next_frame().await;
    }
}
