//! Touchpad / mouse test (mirrors `touchpad.touchpad_step`): drag to each box +
//! click, scroll up/down twice, optional middle click, then Y/N.

use macroquad::prelude::*;

use crate::app::App;
use crate::ui::draw;

fn clamp(v: f32, lo: f32, hi: f32) -> f32 {
    v.max(lo).min(hi)
}

#[derive(Default)]
struct Done {
    drag_left: bool,
    left_click: bool,
    drag_right: bool,
    right_click: bool,
    scroll_up: bool,
    scroll_down: bool,
    middle_click: bool,
}

impl Done {
    fn required_done(&self) -> bool {
        self.drag_left
            && self.left_click
            && self.drag_right
            && self.right_click
            && self.scroll_up
            && self.scroll_down
    }
}

pub async fn run(app: &mut App) {
    let mut done = Done::default();
    let mut drag_start: Option<Vec2> = None;
    let mut scroll_up_count = 0;
    let mut scroll_down_count = 0;

    loop {
        app.tick_global().await;

        let w = screen_width();
        let h = screen_height();
        let box_w = clamp(w / 3.0, 200.0, 420.0);
        let box_h = clamp(h / 4.0, 120.0, 260.0);
        let box_y = h / 2.0 - box_h / 2.0;
        let left_rect = Rect::new(w / 4.0 - box_w / 2.0, box_y, box_w, box_h);
        let right_rect = Rect::new(w * 3.0 / 4.0 - box_w / 2.0, box_y, box_w, box_h);

        let (mx, my) = mouse_position();
        let mouse = vec2(mx, my);

        // Drag detection: accumulate distance from a fixed start until a box is reached.
        match drag_start {
            None => drag_start = Some(mouse),
            Some(start) => {
                let dist = mouse.distance(start);
                if dist >= 100.0 && left_rect.contains(mouse) {
                    if !done.drag_left {
                        done.drag_left = true;
                        app.log.add_now("TOUCHPAD_DRAG_TO_LEFT_BOX", "APROVADO");
                    }
                    drag_start = None;
                } else if dist >= 100.0 && right_rect.contains(mouse) {
                    if !done.drag_right {
                        done.drag_right = true;
                        app.log.add_now("TOUCHPAD_DRAG_TO_RIGHT_BOX", "APROVADO");
                    }
                    drag_start = None;
                }
            }
        }

        // Clicks.
        if is_mouse_button_pressed(MouseButton::Left) && left_rect.contains(mouse) && !done.left_click {
            done.left_click = true;
            app.log.add_now("TOUCHPAD_LEFT_CLICK", "APROVADO");
        }
        if is_mouse_button_pressed(MouseButton::Right) && right_rect.contains(mouse) && !done.right_click {
            done.right_click = true;
            app.log.add_now("TOUCHPAD_RIGHT_CLICK", "APROVADO");
        }
        if is_mouse_button_pressed(MouseButton::Middle) && !done.middle_click {
            done.middle_click = true;
            app.log.add_now("TOUCHPAD_MIDDLE_CLICK", "APROVADO");
        }

        // Scroll (need two notches each way).
        let (_, wheel_y) = mouse_wheel();
        if wheel_y > 0.0 && !done.scroll_up {
            scroll_up_count += 1;
            if scroll_up_count >= 2 {
                done.scroll_up = true;
                app.log.add_now("TOUCHPAD_SCROLL_UP", "APROVADO");
            }
        } else if wheel_y < 0.0 && !done.scroll_down {
            scroll_down_count += 1;
            if scroll_down_count >= 2 {
                done.scroll_down = true;
                app.log.add_now("TOUCHPAD_SCROLL_DOWN", "APROVADO");
            }
        }

        // Approve / reject.
        if is_key_pressed(KeyCode::Y) && done.required_done() {
            app.log.add_now("TOUCHPAD_APPROVED", "APROVADO");
            return;
        }
        if is_key_pressed(KeyCode::N) {
            app.log.add_now("TOUCHPAD_REPROVED", "REPROVADO");
            return;
        }

        draw_ui(app, &done, left_rect, right_rect, scroll_up_count, scroll_down_count);
        next_frame().await;
    }
}

fn draw_ui(
    app: &App,
    done: &Done,
    left_rect: Rect,
    right_rect: Rect,
    scroll_up_count: i32,
    scroll_down_count: i32,
) {
    let w = screen_width();
    let h = screen_height();
    let font = app.font();

    clear_background(BLACK);
    draw::text_centered("Teste de Touchpad", w / 2.0, clamp(h / 8.0, 60.0, 140.0), 22, WHITE, font);

    let left_color = if done.drag_left && done.left_click { draw::rgb(0, 200, 0) } else { draw::rgb(100, 100, 100) };
    draw_rectangle_lines(left_rect.x, left_rect.y, left_rect.w, left_rect.h, 3.0, left_color);
    draw::text_centered("Clique ESQUERDO", left_rect.x + left_rect.w / 2.0, left_rect.y + left_rect.h / 2.0, 22, WHITE, font);

    let right_color = if done.drag_right && done.right_click { draw::rgb(0, 200, 0) } else { draw::rgb(100, 100, 100) };
    draw_rectangle_lines(right_rect.x, right_rect.y, right_rect.w, right_rect.h, 3.0, right_color);
    draw::text_centered("Clique DIREITO", right_rect.x + right_rect.w / 2.0, right_rect.y + right_rect.h / 2.0, 22, WHITE, font);

    let items = [
        ("Arraste ate a caixa da esquerda".to_string(), done.drag_left, false),
        ("Clique ESQUERDO na caixa".to_string(), done.left_click, false),
        ("Arraste ate a caixa da direita".to_string(), done.drag_right, false),
        ("Clique DIREITO na caixa".to_string(), done.right_click, false),
        (format!("Scroll PARA CIMA (2x) {}/2", scroll_up_count), done.scroll_up, false),
        (format!("Scroll PARA BAIXO (2x) {}/2", scroll_down_count), done.scroll_down, false),
        ("Botao do meio".to_string(), done.middle_click, true),
    ];

    let mut y = clamp(h / 3.0, 180.0, h / 2.0);
    for (text, ok, optional) in &items {
        let prefix = if *ok { "[OK] " } else { "[ ] " };
        let suffix = if *optional { " (opcional)" } else { "" };
        let color = if *ok { draw::rgb(0, 255, 0) } else { draw::rgb(200, 200, 200) };
        draw::text_centered(&format!("{prefix}{text}{suffix}"), w / 2.0, y, 22, color, font);
        y += clamp(h / 30.0, 22.0, 36.0);
    }

    let approve = done.required_done();
    let status = if approve { "Y = aprovar, N = reprovar" } else { "Complete os passos obrigatorios" };
    let status_color = if approve { draw::rgb(0, 200, 0) } else { draw::rgb(200, 200, 200) };
    draw::text_centered(status, w / 2.0, h * 5.0 / 6.0, 22, status_color, font);
}
