mod app;
mod audio;
mod config;
mod database;
mod device_info;
mod ethernet;
mod keyboard;
mod log_manager;
mod screen;
mod system_utils;
mod usb;
mod video;

use app::RevyCheckApp;
use eframe::NativeOptions;
use tracing_subscriber;

fn main() -> Result<(), eframe::Error> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Disable Alt+Tab on GNOME (Linux)
    #[cfg(target_os = "linux")]
    system_utils::disable_alt_tab();

    let options = NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_fullscreen(true)
            .with_decorations(false)
            .with_always_on_top()
            .with_resizable(false),
        ..Default::default()
    };

    let result = eframe::run_native(
        "RevyCheck - Sistema de Testes",
        options,
        Box::new(|cc| {
            // Setup egui style
            let mut style = (*cc.egui_ctx.style()).clone();
            style.text_styles.insert(
                egui::TextStyle::Body,
                egui::FontId::new(20.0, egui::FontFamily::Proportional),
            );
            style.text_styles.insert(
                egui::TextStyle::Button,
                egui::FontId::new(18.0, egui::FontFamily::Proportional),
            );
            style.text_styles.insert(
                egui::TextStyle::Heading,
                egui::FontId::new(28.0, egui::FontFamily::Proportional),
            );
            cc.egui_ctx.set_style(style);

            Ok(Box::new(RevyCheckApp::new(cc)))
        }),
    );

    // Restore Alt+Tab on exit (Linux)
    #[cfg(target_os = "linux")]
    system_utils::restore_alt_tab();

    result
}
