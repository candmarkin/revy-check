//! On-screen keyboard test (mirrors `keyboard.keyboard_step`): every mapped key
//! must be pressed once, then the test auto-approves.
//!
//! Note: macroquad's `KeyCode` can't distinguish the BR-ABNT2 dead keys
//! (`´`, `~`, `Ç`) the Python layout special-cased, so those are drawn but not
//! required. `keycodes.json` (already collected) + a bundled font are the Phase 6
//! path to full fidelity per OS.

use std::collections::HashSet;

use macroquad::prelude::*;

use crate::app::App;
use crate::ui::draw;

struct Key {
    label: &'static str,
    code: Option<KeyCode>,
    w: f32,
}

const fn k(label: &'static str, code: KeyCode, w: f32) -> Key {
    Key { label, code: Some(code), w }
}

/// A drawn-only key with no reliable macroquad mapping.
const fn dead(label: &'static str, w: f32) -> Key {
    Key { label, code: None, w }
}

fn layout() -> Vec<Vec<Key>> {
    use KeyCode::*;
    vec![
        vec![
            k("Esc", Escape, 58.0), k("F1", F1, 58.0), k("F2", F2, 58.0), k("F3", F3, 58.0),
            k("F4", F4, 58.0), k("F5", F5, 58.0), k("F6", F6, 58.0), k("F7", F7, 58.0),
            k("F8", F8, 58.0), k("F9", F9, 58.0), k("F10", F10, 58.0), k("F11", F11, 58.0),
            k("F12", F12, 58.0), k("Ins", Insert, 58.0), k("Del", Delete, 58.0),
        ],
        vec![
            k("'", Apostrophe, 60.0), k("1", Key1, 60.0), k("2", Key2, 60.0), k("3", Key3, 60.0),
            k("4", Key4, 60.0), k("5", Key5, 60.0), k("6", Key6, 60.0), k("7", Key7, 60.0),
            k("8", Key8, 60.0), k("9", Key9, 60.0), k("0", Key0, 60.0),
            k("-", Minus, 60.0), k("=", Equal, 60.0), k("Backspace", Backspace, 100.0),
        ],
        vec![
            k("Tab", Tab, 100.0), k("Q", Q, 60.0), k("W", W, 60.0), k("E", E, 60.0),
            k("R", R, 60.0), k("T", T, 60.0), k("Y", Y, 60.0), k("U", U, 60.0),
            k("I", I, 60.0), k("O", O, 60.0), k("P", P, 60.0),
            dead("Acento", 60.0), k("[", LeftBracket, 60.0), k("Enter", Enter, 130.0),
        ],
        vec![
            k("Caps", CapsLock, 110.0), k("A", A, 60.0), k("S", S, 60.0), k("D", D, 60.0),
            k("F", F, 60.0), k("G", G, 60.0), k("H", H, 60.0), k("J", J, 60.0),
            k("K", K, 60.0), k("L", L, 60.0), dead("Cedilha", 60.0),
            dead("Til", 60.0), k("]", RightBracket, 60.0),
        ],
        vec![
            k("Shift", LeftShift, 80.0), k("\\", Backslash, 60.0), k("Z", Z, 60.0), k("X", X, 60.0),
            k("C", C, 60.0), k("V", V, 60.0), k("B", B, 60.0), k("N", N, 60.0), k("M", M, 60.0),
            k(",", Comma, 60.0), k(".", Period, 60.0), k(";", Semicolon, 60.0),
            k("Shift", RightShift, 145.0),
        ],
        vec![
            k("Ctrl", LeftControl, 80.0), dead("Fn", 60.0), k("Win", LeftSuper, 60.0),
            k("Alt", LeftAlt, 60.0), k("Espaco", Space, 320.0), k("AltGr", RightAlt, 60.0),
            k("/", Slash, 60.0),
        ],
        vec![
            k("Esq", Left, 60.0), k("Cima", Up, 80.0), k("Baixo", Down, 80.0),
            k("Dir", Right, 60.0), k("PgUp", PageUp, 60.0), k("PgDn", PageDown, 60.0),
        ],
    ]
}

pub async fn run(app: &mut App) {
    let rows = layout();
    let required: HashSet<KeyCode> = rows.iter().flatten().filter_map(|key| key.code).collect();
    let mut pressed: HashSet<KeyCode> = HashSet::new();

    loop {
        app.tick_global().await;

        for key in rows.iter().flatten() {
            if let Some(code) = key.code {
                if is_key_pressed(code) {
                    pressed.insert(code);
                }
            }
        }

        clear_background(WHITE);
        draw_keyboard(&rows, &pressed, app.font());
        draw::system_overlay(&app.system_info, app.font());
        draw::text_left(
            &format!("Teclas: {}/{}", pressed.len(), required.len()),
            20.0,
            screen_height() - 30.0,
            22,
            draw::rgb(0, 100, 255),
            app.font(),
        );

        if pressed.len() >= required.len() {
            app.log.add_now("KEYBOARD_TEST", "APROVADO");
            draw::screen_message(&app.system_info, &["Teste de teclado concluido!"], GREEN, app.font());
            next_frame().await;
            hold(app, 1.0).await;
            return;
        }

        next_frame().await;
    }
}

fn draw_keyboard(rows: &[Vec<Key>], pressed: &HashSet<KeyCode>, font: Option<&Font>) {
    let mut y = 90.0;
    for (row_idx, row) in rows.iter().enumerate() {
        let total: f32 = row.iter().map(|key| key.w + 5.0).sum::<f32>() - 5.0;
        let mut x = (screen_width() - total) / 2.0;
        let kh = if row_idx == 0 { 40.0 } else { 60.0 };

        for key in row {
            let down = key.code.is_some_and(is_key_down);
            let ever = key.code.is_some_and(|c| pressed.contains(&c));
            let color = if down {
                GREEN
            } else if ever {
                draw::rgb(100, 255, 100)
            } else {
                WHITE
            };
            draw_rectangle(x, y, key.w, kh, color);
            draw_rectangle_lines(x, y, key.w, kh, 2.0, BLACK);
            draw::text_centered(key.label, x + key.w / 2.0, y + kh / 2.0, 16, BLACK, font);
            x += key.w + 5.0;
        }

        y += if row_idx == 0 { 50.0 } else { 70.0 };
    }
}

/// Hold the current frame for `secs`, still pumping global input.
async fn hold(app: &mut App, secs: f64) {
    let t0 = get_time();
    while get_time() - t0 < secs {
        app.tick_global().await;
        next_frame().await;
    }
}
