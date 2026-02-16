pub struct ScreenTestState {
    colors: Vec<egui::Color32>,
    current_color: usize,
    test_complete: bool,
    approved: Option<bool>,
}

impl ScreenTestState {
    pub fn new() -> Self {
        Self {
            colors: vec![
                egui::Color32::BLACK,
                egui::Color32::WHITE,
                egui::Color32::RED,
                egui::Color32::GREEN,
                egui::Color32::BLUE,
                egui::Color32::YELLOW,
            ],
            current_color: 0,
            test_complete: false,
            approved: None,
        }
    }

    pub fn draw(&mut self, ui: &mut egui::Ui, ctx: &egui::Context) {
        let color = self.colors[self.current_color];
        
        // Fill entire window with color
        let painter = ui.painter();
        let rect = ui.max_rect();
        painter.rect_filled(rect, 0.0, color);

        if !self.test_complete {
            // Show instructions at bottom
            let text_color = if self.current_color == 1 {
                egui::Color32::BLACK
            } else {
                egui::Color32::WHITE
            };
            
            painter.text(
                egui::pos2(rect.right() - 400.0, rect.bottom() - 50.0),
                egui::Align2::LEFT_BOTTOM,
                "Pressione ENTER para alternar cores e ESPAÇO para finalizar",
                egui::FontId::proportional(18.0),
                text_color,
            );

            // Handle input
            ctx.input(|i| {
                if i.key_pressed(egui::Key::Enter) {
                    self.current_color = (self.current_color + 1) % self.colors.len();
                } else if i.key_pressed(egui::Key::Space) {
                    self.test_complete = true;
                }
            });
        } else if self.approved.is_none() {
            // Show approval dialog
            ui.vertical_centered(|ui| {
                ui.add_space(ui.available_height() / 3.0);
                ui.heading("Teste concluído!");
                ui.add_space(20.0);
                ui.label("Aperte Y para APROVAR ou N para REPROVAR");
            });

            ctx.input(|i| {
                if i.key_pressed(egui::Key::Y) {
                    self.approved = Some(true);
                } else if i.key_pressed(egui::Key::N) {
                    self.approved = Some(false);
                }
            });
        }
    }

    pub fn is_complete(&self) -> bool {
        self.approved.is_some()
    }

    pub fn is_approved(&self) -> bool {
        self.approved.unwrap_or(false)
    }
}
