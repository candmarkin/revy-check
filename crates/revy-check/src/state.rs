//! The linear test flow (mirrors the `main.py` state machine order). Each step
//! is gated by the device feature flags in `app.config`.

use crate::app::App;
use crate::steps::{done, keyboard, placeholder, screen, touchpad};
use crate::ui::menu;

pub async fn run(app: &mut App) {
    menu::start_step(app).await;

    if app.config.has_embedded_screen {
        app.log.add_now("SCREEN_TEST_START", "APROVADO");
        screen::run(app).await;
    }

    if app.config.has_embedded_keyboard {
        app.log.add_now("KEYBOARD_TEST_START", "APROVADO");
        keyboard::run(app).await;
    }

    if app.config.has_touchpad {
        app.log.add_now("TOUCHPAD_TEST_START", "APROVADO");
        touchpad::run(app).await;
    }

    if app.config.has_wifi {
        app.log.add_now("WIFI_TEST_START", "APROVADO");
        placeholder::confirm(app, "Teste de WiFi", "Verifique a conexao sem fio.", "WIFI_TEST").await;
    }

    if app.config.has_camera {
        app.log.add_now("CAMERA_TEST_START", "APROVADO");
        placeholder::confirm(app, "Teste de Camera", "Verifique a imagem da webcam.", "CAMERA_TEST").await;
    }

    // USB — one connect + remove per configured port.
    let ports: Vec<String> = app.config.port_map.iter().map(|p| p.label.clone()).collect();
    for label in ports {
        app.log.add_now(&format!("USB_CONNECT_TEST_START_{label}"), "APROVADO");
        placeholder::confirm(app, &format!("Conecte o pendrive na {label}"), "", &format!("USB_CONNECT_{label}")).await;
        placeholder::confirm(app, &format!("Remova o pendrive da {label}"), "", &format!("USB_REMOVE_{label}")).await;
    }

    // Video — one confirm, then a result row per configured output.
    app.log.add_now("VIDEO_TEST_START", "APROVADO");
    placeholder::confirm(app, "Teste de Video", "Conecte os monitores externos.", "VIDEO_TEST").await;
    let video_labels: Vec<String> = app.config.video_ports.iter().map(|v| v.label.clone()).collect();
    for label in video_labels {
        app.log.add_now(&format!("VIDEO_{label}_TEST"), "APROVADO");
    }

    if app.config.has_headphone_jack {
        app.log.add_now("HEADPHONE_TEST_START", "APROVADO");
        placeholder::confirm(app, "Teste de Headphone", "Conecte e ouca o som.", "HEADPHONE_TEST").await;
    }

    if app.config.has_speaker {
        app.log.add_now("SPEAKER_TEST_START", "APROVADO");
        placeholder::confirm(app, "Teste de Alto-falante", "Ouca o som dos alto-falantes.", "SPEAKER_TEST").await;
    }

    if app.config.has_microphone {
        app.log.add_now("MICROPHONE_TEST_START", "APROVADO");
        placeholder::confirm(app, "Teste de Microfone", "Fale e verifique o nivel.", "MICROPHONE_TEST").await;
    }

    if app.config.has_ethernet_port {
        app.log.add_now("ETHERNET_TEST_START", "APROVADO");
        placeholder::confirm(app, "Teste de Ethernet", "Conecte o cabo de rede.", "ETHERNET_TEST").await;
    }

    done::run(app).await;
}
