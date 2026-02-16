use crate::audio::{play_headphone_sequence, play_speaker_sequence, test_microphone};
use crate::config::DeviceConfig;
use crate::database::{check_db_connection, fetch_device_info, send_log_to_db};
use crate::device_info::get_device_info;
use crate::ethernet::check_ethernet_connection;
use crate::keyboard::{draw_keyboard, KeyboardState};
use crate::log_manager::LogEntry;
use crate::screen::ScreenTestState;
use crate::system_utils::sync_ntp_time;
use crate::usb::check_usb_device;
use crate::video::check_video_ports;
use chrono::Local;
use std::collections::HashSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AppState {
    WaitingForNetwork,
    SelectTestType,
    ScreenTest,
    KeyboardTest,
    UsbTest,
    VideoTest,
    HeadphoneTest,
    SpeakerTest,
    MicrophoneTest,
    EthernetTest,
    Done,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TestType {
    Qualidade1,
    Qualidade2,
    Vistoria1,
    Vistoria2,
    Vistoria3,
    Vistoria4,
}

pub struct RevyCheckApp {
    state: AppState,
    config: Option<DeviceConfig>,
    logs: Vec<LogEntry>,
    test_type: Option<TestType>,
    
    // Test-specific state
    keyboard_state: KeyboardState,
    screen_test_state: ScreenTestState,
    usb_current_port: usize,
    usb_waiting_remove: bool,
    video_ports_approved: HashSet<String>,
    headphone_connected: bool,
    ethernet_connected: bool,
    ethernet_remove_step: bool,
    
    // Dev mode
    dev_mode: bool,
    dev_keys_pressed: HashSet<egui::Key>,
    
    // UI state
    error_message: Option<String>,
    info_message: Option<String>,
}

impl RevyCheckApp {
    pub fn new(_cc: &eframe::CreationContext<'_>) -> Self {
        Self {
            state: AppState::WaitingForNetwork,
            config: None,
            logs: Vec::new(),
            test_type: None,
            keyboard_state: KeyboardState::new(),
            screen_test_state: ScreenTestState::new(),
            usb_current_port: 0,
            usb_waiting_remove: false,
            video_ports_approved: HashSet::new(),
            headphone_connected: false,
            ethernet_connected: false,
            ethernet_remove_step: false,
            dev_mode: false,
            dev_keys_pressed: HashSet::new(),
            error_message: None,
            info_message: None,
        }
    }

    fn add_log(&mut self, step: &str, result: &str) {
        self.logs.push(LogEntry {
            step: step.to_string(),
            time: Local::now(),
            result: result.to_string(),
        });
    }

    fn check_dev_hotkey(&mut self, ctx: &egui::Context) {
        // Check for Ctrl+Shift+D+V hotkey
        let ctrl = ctx.input(|i| i.modifiers.ctrl);
        let shift = ctx.input(|i| i.modifiers.shift);
        let d_pressed = ctx.input(|i| i.key_pressed(egui::Key::D));
        let v_pressed = ctx.input(|i| i.key_pressed(egui::Key::V));

        if ctrl && shift && d_pressed && v_pressed && !self.dev_mode {
            self.dev_mode = true;
            self.info_message = Some("DEV MODE ATIVADO".to_string());
        }
    }
}

impl eframe::App for RevyCheckApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.check_dev_hotkey(ctx);

        egui::CentralPanel::default().show(ctx, |ui| {
            match self.state {
                AppState::WaitingForNetwork => {
                    ui.vertical_centered(|ui| {
                        ui.add_space(ui.available_height() / 3.0);
                        ui.heading("Conectando ao banco de dados...");
                        ui.add_space(20.0);
                        
                        if check_db_connection() {
                            // Try to fetch device config
                            match fetch_device_info() {
                                Ok(config) => {
                                    self.config = Some(config);
                                    sync_ntp_time();
                                    self.state = AppState::SelectTestType;
                                }
                                Err(e) => {
                                    self.error_message = Some(format!("Erro ao buscar configuração: {}", e));
                                }
                            }
                        } else {
                            ui.label("Conecte-se à rede corporativa");
                            ui.spinner();
                        }
                    });
                }

                AppState::SelectTestType => {
                    ui.vertical_centered(|ui| {
                        ui.add_space(50.0);
                        ui.heading("Selecione o tipo de teste");
                        ui.add_space(50.0);

                        let test_types = [
                            TestType::Qualidade1,
                            TestType::Qualidade2,
                            TestType::Vistoria1,
                            TestType::Vistoria2,
                            TestType::Vistoria3,
                            TestType::Vistoria4,
                        ];

                        for test_type in &test_types {
                            let label = format!("{:?}", test_type).to_uppercase();
                            if ui.add_sized([300.0, 60.0], egui::Button::new(label)).clicked() {
                                self.test_type = Some(test_type.clone());
                                self.add_log(&format!("TEST_START_{:?}", test_type), "APROVADO");
                                self.state = AppState::ScreenTest;
                            }
                            ui.add_space(10.0);
                        }
                    });
                }

                AppState::ScreenTest => {
                    if let Some(config) = &self.config {
                        if config.has_embedded_screen {
                            self.screen_test_state.draw(ui, ctx);
                            
                            if self.screen_test_state.is_complete() {
                                let result = if self.screen_test_state.is_approved() {
                                    "APROVADO"
                                } else {
                                    "REPROVADO"
                                };
                                self.add_log("SCREEN_TEST", result);
                                self.state = AppState::KeyboardTest;
                            }
                        } else {
                            self.state = AppState::KeyboardTest;
                        }
                    }
                }

                AppState::KeyboardTest => {
                    if let Some(config) = &self.config {
                        if config.has_embedded_keyboard {
                            draw_keyboard(ui, ctx, &mut self.keyboard_state);
                            
                            if self.keyboard_state.all_keys_pressed() {
                                if ui.add_sized([200.0, 50.0], egui::Button::new("Aprovar")).clicked() {
                                    self.add_log("KEYBOARD_TEST", "APROVADO");
                                    self.state = AppState::UsbTest;
                                }
                            }
                        } else {
                            self.state = AppState::UsbTest;
                        }
                    }
                }

                AppState::UsbTest => {
                    if let Some(config) = &self.config {
                        if self.usb_current_port < config.port_map.len() {
                            let (bus, port, label) = &config.port_map[self.usb_current_port];
                            
                            ui.vertical_centered(|ui| {
                                ui.add_space(ui.available_height() / 3.0);
                                
                                if !self.usb_waiting_remove {
                                    ui.heading(format!("Conecte o pendrive na {}", label));
                                    
                                    if check_usb_device(bus, port) {
                                        self.add_log(&format!("USB_CONNECT_{}", label), "APROVADO");
                                        self.usb_waiting_remove = true;
                                    }
                                } else {
                                    ui.heading(format!("Remova o pendrive da {}", label));
                                    
                                    if !check_usb_device(bus, port) {
                                        self.add_log(&format!("USB_REMOVE_{}", label), "APROVADO");
                                        self.usb_current_port += 1;
                                        self.usb_waiting_remove = false;
                                    }
                                }
                            });
                        } else {
                            self.state = AppState::VideoTest;
                        }
                    }
                }

                AppState::VideoTest => {
                    if let Some(config) = &self.config {
                        ui.vertical_centered(|ui| {
                            ui.add_space(50.0);
                            ui.heading("Conecte os monitores nas portas de vídeo");
                            ui.add_space(30.0);

                            let status_list = check_video_ports(&config.video_ports);
                            let mut all_approved = true;

                            for status in &status_list {
                                let color = if self.video_ports_approved.contains(&status.entry) {
                                    egui::Color32::GREEN
                                } else if status.connected {
                                    egui::Color32::YELLOW
                                } else {
                                    egui::Color32::RED
                                };

                                ui.colored_label(
                                    color,
                                    format!(
                                        "{}: {}{}",
                                        status.label,
                                        if status.connected { "conectado" } else { "desconectado" },
                                        if self.video_ports_approved.contains(&status.entry) {
                                            " (aprovado)"
                                        } else {
                                            ""
                                        }
                                    ),
                                );

                                if status.connected {
                                    self.video_ports_approved.insert(status.entry.clone());
                                }

                                if !self.video_ports_approved.contains(&status.entry) {
                                    all_approved = false;
                                }
                            }

                            ui.add_space(20.0);
                            
                            if all_approved {
                                ui.colored_label(egui::Color32::GREEN, "Todas as portas conectadas!");
                                if ui.button("Continuar").clicked() {
                                    for status in status_list {
                                        self.add_log(&format!("VIDEO_{}", status.label), "APROVADO");
                                    }
                                    self.state = AppState::HeadphoneTest;
                                }
                            }
                        });
                    }
                }

                AppState::HeadphoneTest => {
                    if let Some(config) = &self.config {
                        if config.has_headphone_jack {
                            ui.vertical_centered(|ui| {
                                ui.add_space(ui.available_height() / 3.0);
                                
                                if !self.headphone_connected {
                                    ui.heading("Conecte o fone de ouvido...");
                                    // Check if headphone is connected
                                    // This would require PulseAudio/PipeWire bindings on Linux
                                    // For now, simplified with a button
                                    if ui.button("Fone conectado").clicked() {
                                        self.headphone_connected = true;
                                        self.add_log("HEADPHONE_CONNECT", "APROVADO");
                                    }
                                } else {
                                    ui.heading("Testando fone de ouvido...");
                                    ui.label("Ouvindo sons em ambos os canais");
                                    
                                    if ui.button("Reproduzir teste").clicked() {
                                        play_headphone_sequence();
                                    }
                                    
                                    ui.add_space(20.0);
                                    ui.heading("Remova o fone de ouvido");
                                    
                                    if ui.button("Fone removido").clicked() {
                                        self.add_log("HEADPHONE_REMOVE", "APROVADO");
                                        self.state = AppState::SpeakerTest;
                                    }
                                }
                            });
                        } else {
                            self.state = AppState::SpeakerTest;
                        }
                    }
                }

                AppState::SpeakerTest => {
                    if let Some(config) = &self.config {
                        if config.has_speaker {
                            ui.vertical_centered(|ui| {
                                ui.add_space(ui.available_height() / 3.0);
                                ui.heading("Teste de alto-falantes");
                                ui.label("Certifique-se de que o fone está desconectado");
                                
                                if ui.button("Reproduzir teste").clicked() {
                                    play_speaker_sequence();
                                    self.add_log("SPEAKER_TEST", "APROVADO");
                                }
                                
                                ui.add_space(20.0);
                                if ui.button("Continuar").clicked() {
                                    self.state = AppState::MicrophoneTest;
                                }
                            });
                        } else {
                            self.state = AppState::MicrophoneTest;
                        }
                    }
                }

                AppState::MicrophoneTest => {
                    if let Some(config) = &self.config {
                        if config.has_microphone {
                            ui.vertical_centered(|ui| {
                                ui.add_space(ui.available_height() / 3.0);
                                ui.heading("Teste do microfone");
                                
                                if ui.button("Testar microfone").clicked() {
                                    match test_microphone() {
                                        Ok(amplitude) => {
                                            let result = if amplitude > 0.01 { "APROVADO" } else { "REPROVADO" };
                                            self.add_log("MICROPHONE_TEST", result);
                                            self.info_message = Some(format!("Amplitude: {:.3}", amplitude));
                                        }
                                        Err(e) => {
                                            self.error_message = Some(format!("Erro: {}", e));
                                        }
                                    }
                                }
                                
                                if let Some(msg) = &self.info_message {
                                    ui.label(msg);
                                }
                                
                                ui.add_space(20.0);
                                if ui.button("Continuar").clicked() {
                                    self.state = AppState::EthernetTest;
                                }
                            });
                        } else {
                            self.state = AppState::EthernetTest;
                        }
                    }
                }

                AppState::EthernetTest => {
                    if let Some(config) = &self.config {
                        if config.has_ethernet_port {
                            ui.vertical_centered(|ui| {
                                ui.add_space(ui.available_height() / 3.0);
                                
                                if !self.ethernet_remove_step {
                                    ui.heading(format!("Conecte o cabo Ethernet ({})", config.eth_interface));
                                    
                                    if check_ethernet_connection(&config.eth_interface) {
                                        self.ethernet_connected = true;
                                        self.ethernet_remove_step = true;
                                        self.add_log("ETHERNET_CONNECT", "APROVADO");
                                    }
                                } else {
                                    ui.heading(format!("Remova o cabo Ethernet ({})", config.eth_interface));
                                    
                                    if !check_ethernet_connection(&config.eth_interface) && self.ethernet_connected {
                                        self.add_log("ETHERNET_REMOVE", "APROVADO");
                                        self.state = AppState::Done;
                                    }
                                }
                            });
                        } else {
                            self.state = AppState::Done;
                        }
                    }
                }

                AppState::Done => {
                    ui.vertical_centered(|ui| {
                        ui.add_space(100.0);
                        ui.heading("Todos os testes concluídos!");
                        ui.add_space(50.0);
                        
                        // Show log preview
                        egui::ScrollArea::vertical().max_height(400.0).show(ui, |ui| {
                            for entry in &self.logs {
                                let color = if entry.result == "APROVADO" {
                                    egui::Color32::GREEN
                                } else {
                                    egui::Color32::RED
                                };
                                ui.colored_label(
                                    color,
                                    format!("{} | {} | {}", entry.step, entry.result, entry.time.format("%H:%M:%S"))
                                );
                            }
                        });
                        
                        ui.add_space(20.0);
                        
                        if ui.add_sized([200.0, 50.0], egui::Button::new("Enviar Log")).clicked() {
                            match send_log_to_db(&self.logs) {
                                Ok(_) => {
                                    self.info_message = Some("Log enviado com sucesso!".to_string());
                                }
                                Err(e) => {
                                    self.error_message = Some(format!("Erro ao enviar: {}", e));
                                }
                            }
                        }
                        
                        ui.add_space(10.0);
                        
                        if ui.add_sized([200.0, 50.0], egui::Button::new("Sair")).clicked() {
                            std::process::exit(0);
                        }
                    });
                }
            }

            // Show error/info messages
            if let Some(msg) = &self.error_message {
                ui.label(egui::RichText::new(msg).color(egui::Color32::RED));
            }

            // Show dev mode indicator
            if self.dev_mode {
                ui.ctx().debug_painter().text(
                    egui::pos2(10.0, 10.0),
                    egui::Align2::LEFT_TOP,
                    "DEV MODE",
                    egui::FontId::default(),
                    egui::Color32::YELLOW,
                );
            }
        });

        ctx.request_repaint_after(std::time::Duration::from_millis(100));
    }
}
