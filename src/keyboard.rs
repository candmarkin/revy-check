use std::collections::HashSet;

pub struct KeyboardState {
    pressed_keys: HashSet<egui::Key>,
    all_keys: Vec<egui::Key>,
}

impl KeyboardState {
    pub fn new() -> Self {
        let all_keys = vec![
            // Function keys
            egui::Key::Escape,
            egui::Key::F1, egui::Key::F2, egui::Key::F3, egui::Key::F4,
            egui::Key::F5, egui::Key::F6, egui::Key::F7, egui::Key::F8,
            egui::Key::F9, egui::Key::F10, egui::Key::F11, egui::Key::F12,
            egui::Key::Insert, egui::Key::Delete,
            // Number row
            egui::Key::Num1, egui::Key::Num2, egui::Key::Num3, egui::Key::Num4,
            egui::Key::Num5, egui::Key::Num6, egui::Key::Num7, egui::Key::Num8,
            egui::Key::Num9, egui::Key::Num0,
            egui::Key::Minus, egui::Key::Equals, egui::Key::Backspace,
            // QWERTY row
            egui::Key::Tab,
            egui::Key::Q, egui::Key::W, egui::Key::E, egui::Key::R, egui::Key::T,
            egui::Key::Y, egui::Key::U, egui::Key::I, egui::Key::O, egui::Key::P,
            egui::Key::Enter,
            // ASDF row
            egui::Key::A, egui::Key::S, egui::Key::D, egui::Key::F, egui::Key::G,
            egui::Key::H, egui::Key::J, egui::Key::K, egui::Key::L,
            // ZXCV row
            egui::Key::Z, egui::Key::X, egui::Key::C, egui::Key::V, egui::Key::B,
            egui::Key::N, egui::Key::M,
            egui::Key::Comma, egui::Key::Period,
            // Bottom row
            egui::Key::Space,
            // Arrow keys
            egui::Key::ArrowLeft, egui::Key::ArrowUp, egui::Key::ArrowDown, egui::Key::ArrowRight,
            egui::Key::PageUp, egui::Key::PageDown,
        ];

        Self {
            pressed_keys: HashSet::new(),
            all_keys,
        }
    }

    pub fn all_keys_pressed(&self) -> bool {
        self.all_keys.iter().all(|k| self.pressed_keys.contains(k))
    }
}

pub fn draw_keyboard(ui: &mut egui::Ui, ctx: &egui::Context, state: &mut KeyboardState) {
    ui.vertical_centered(|ui| {
        ui.add_space(20.0);
        ui.heading("Teste de Teclado");
        ui.label("Pressione todas as teclas");
        ui.add_space(20.0);

        // Check for key presses
        ctx.input(|i| {
            for event in &i.events {
                if let egui::Event::Key { key, pressed, .. } = event {
                    if *pressed {
                        state.pressed_keys.insert(*key);
                    }
                }
            }
        });

        // Draw keyboard layout
        egui::Grid::new("keyboard_grid")
            .spacing([5.0, 5.0])
            .show(ui, |ui| {
                // Function keys row
                draw_key_row(ui, &[
                    (egui::Key::Escape, "Esc"),
                    (egui::Key::F1, "F1"),
                    (egui::Key::F2, "F2"),
                    (egui::Key::F3, "F3"),
                    (egui::Key::F4, "F4"),
                    (egui::Key::F5, "F5"),
                    (egui::Key::F6, "F6"),
                    (egui::Key::F7, "F7"),
                    (egui::Key::F8, "F8"),
                    (egui::Key::F9, "F9"),
                    (egui::Key::F10, "F10"),
                    (egui::Key::F11, "F11"),
                    (egui::Key::F12, "F12"),
                    (egui::Key::Insert, "Ins"),
                    (egui::Key::Delete, "Del"),
                ], &state.pressed_keys);
                ui.end_row();

                // Number row
                draw_key_row(ui, &[
                    (egui::Key::Num1, "1"),
                    (egui::Key::Num2, "2"),
                    (egui::Key::Num3, "3"),
                    (egui::Key::Num4, "4"),
                    (egui::Key::Num5, "5"),
                    (egui::Key::Num6, "6"),
                    (egui::Key::Num7, "7"),
                    (egui::Key::Num8, "8"),
                    (egui::Key::Num9, "9"),
                    (egui::Key::Num0, "0"),
                    (egui::Key::Minus, "-"),
                    (egui::Key::Equals, "="),
                    (egui::Key::Backspace, "Back"),
                ], &state.pressed_keys);
                ui.end_row();

                // QWERTY row
                draw_key_row(ui, &[
                    (egui::Key::Tab, "Tab"),
                    (egui::Key::Q, "Q"),
                    (egui::Key::W, "W"),
                    (egui::Key::E, "E"),
                    (egui::Key::R, "R"),
                    (egui::Key::T, "T"),
                    (egui::Key::Y, "Y"),
                    (egui::Key::U, "U"),
                    (egui::Key::I, "I"),
                    (egui::Key::O, "O"),
                    (egui::Key::P, "P"),
                    (egui::Key::Enter, "Enter"),
                ], &state.pressed_keys);
                ui.end_row();

                // ASDF row
                draw_key_row(ui, &[
                    (egui::Key::A, "A"),
                    (egui::Key::S, "S"),
                    (egui::Key::D, "D"),
                    (egui::Key::F, "F"),
                    (egui::Key::G, "G"),
                    (egui::Key::H, "H"),
                    (egui::Key::J, "J"),
                    (egui::Key::K, "K"),
                    (egui::Key::L, "L"),
                ], &state.pressed_keys);
                ui.end_row();

                // ZXCV row
                draw_key_row(ui, &[
                    (egui::Key::Z, "Z"),
                    (egui::Key::X, "X"),
                    (egui::Key::C, "C"),
                    (egui::Key::V, "V"),
                    (egui::Key::B, "B"),
                    (egui::Key::N, "N"),
                    (egui::Key::M, "M"),
                    (egui::Key::Comma, ","),
                    (egui::Key::Period, "."),
                ], &state.pressed_keys);
                ui.end_row();

                // Space row
                draw_key_row(ui, &[
                    (egui::Key::Space, "Space"),
                ], &state.pressed_keys);
                ui.end_row();

                // Arrow keys
                draw_key_row(ui, &[
                    (egui::Key::ArrowLeft, "←"),
                    (egui::Key::ArrowUp, "↑"),
                    (egui::Key::ArrowDown, "↓"),
                    (egui::Key::ArrowRight, "→"),
                    (egui::Key::PageUp, "PgUp"),
                    (egui::Key::PageDown, "PgDn"),
                ], &state.pressed_keys);
                ui.end_row();
            });

        ui.add_space(20.0);
        let pressed_count = state.pressed_keys.len();
        let total_keys = state.all_keys.len();
        ui.label(format!("Teclas pressionadas: {}/{}", pressed_count, total_keys));
    });
}

fn draw_key_row(ui: &mut egui::Ui, keys: &[(egui::Key, &str)], pressed: &HashSet<egui::Key>) {
    for (key, label) in keys {
        let color = if pressed.contains(key) {
            egui::Color32::GREEN
        } else {
            egui::Color32::LIGHT_GRAY
        };
        
        let button = egui::Button::new(*label).fill(color);
        ui.add_sized([50.0, 40.0], button);
    }
}
