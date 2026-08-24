//! Test-type selection menu (mirrors `app_flow.start_step`).

use macroquad::prelude::*;

use crate::app::App;
use crate::testlog::now_string;
use crate::testlog::LogEntry;
use crate::ui::draw;

const OPTIONS: [&str; 6] = [
    "QUALIDADE1",
    "QUALIDADE2",
    "VISTORIA1",
    "VISTORIA2",
    "VISTORIA3",
    "VISTORIA4",
];

pub async fn start_step(app: &mut App) {
    loop {
        app.tick_global().await;

        // ESC exits the whole app here (matches the Python menu).
        if is_key_pressed(KeyCode::Escape) {
            app.save_and_exit();
        }

        let w = screen_width();
        let h = screen_height();
        let start_y = h / 2.0 - OPTIONS.len() as f32 * 50.0 / 2.0;
        let (mx, my) = mouse_position();
        let mouse = vec2(mx, my);

        clear_background(draw::rgb(30, 30, 30));
        draw::system_overlay(&app.system_info, app.font());
        draw::text_centered("Selecione o tipo de teste", w / 2.0, h / 4.0, 24, WHITE, app.font());

        let clicked = is_mouse_button_pressed(MouseButton::Left);

        for (i, opt) in OPTIONS.iter().enumerate() {
            let rect = Rect::new(w / 2.0 - 150.0, start_y + i as f32 * 80.0, 300.0, 60.0);
            let hover = rect.contains(mouse);
            let color = if hover { draw::rgb(0, 200, 0) } else { draw::rgb(0, 150, 0) };
            draw_rectangle(rect.x, rect.y, rect.w, rect.h, color);
            draw::text_centered(opt, rect.x + rect.w / 2.0, rect.y + rect.h / 2.0, 22, WHITE, app.font());

            if clicked && hover {
                app.log.add(LogEntry {
                    step: format!("TEST_START_{}", opt.to_uppercase().replace(' ', "_")),
                    time: now_string(),
                    result: "APROVADO".into(),
                });
                return;
            }
        }

        next_frame().await;
    }
}
