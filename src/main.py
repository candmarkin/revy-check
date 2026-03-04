import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pygame

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src import app_state
from src.functions.app_flow import prompt_password, start_step, wait_for_db_connection
from src.functions.audio import play_headphone_sequence, play_speaker_sequence, test_microphone_bip
from src.functions.camera import camera_test_step
from src.functions.device_info import fetch_device_info
from src.functions.ethernet import ethernet_step
from src.functions.gui import draw_text
from src.functions.keyboard import keyboard_step
from src.functions.ntp import consulta_ntp
from src.functions.save_log import save_log
from src.functions.screen import screen_step
from src.functions.system_info import get_system_info
from src.functions.tab_lock import disable_alt_tab, restore_alt_tab
from src.functions.touchpad import touchpad_step
from src.functions.usb import port_has_device
from src.functions.video_ports import draw_video, get_video_status, init_video_state
from src.functions.wifi import WiFiTest


def init_app_state():
    app_state.MODE = "PROD"
    app_state.DEV_PASSWORD = "dev123"
    # Initialize pygame subsystems with defensive fallbacks and logging
    print("[init] Inicializando pygame...")
    try:
        pygame.init()
        print("[init] pygame.init() OK")
    except Exception as e:
        print(f"[init][ERROR] pygame.init() falhou: {e}")

    # Try to create a display; if fullscreen fails, fall back to windowed mode
    try:
        info = pygame.display.Info()
        app_state.WIDTH, app_state.HEIGHT = info.current_w or 1024, info.current_h or 768
        try:
            app_state.SCREEN = pygame.display.set_mode((app_state.WIDTH, app_state.HEIGHT), pygame.FULLSCREEN)
            print(f"[init] display modo FULLSCREEN {app_state.WIDTH}x{app_state.HEIGHT}")
        except Exception as e:
            print(f"[init][WARN] Falha ao setar FULLSCREEN: {e}. Tentando modo janela...")
            app_state.WIDTH, app_state.HEIGHT = 1024, 768
            app_state.SCREEN = pygame.display.set_mode((app_state.WIDTH, app_state.HEIGHT))
            print(f"[init] display modo WINDOW {app_state.WIDTH}x{app_state.HEIGHT}")
    except Exception as e:
        print(f"[init][ERROR] Falha ao inicializar display: {e}")
        # Provide reasonable defaults to avoid None errors later
        app_state.WIDTH, app_state.HEIGHT = 1024, 768
        app_state.SCREEN = None

    try:
        pygame.display.set_caption("Checklist Técnico Completo")
    except Exception:
        pass

    try:
        pygame.mouse.set_visible(True)
    except Exception:
        pass

    try:
        app_state.FONT = pygame.font.SysFont("Arial", 20)
    except Exception:
        app_state.FONT = None

    try:
        app_state.CLOCK = pygame.time.Clock()
    except Exception:
        app_state.CLOCK = None

    app_state.COLORS = {
        "WHITE": (240, 240, 240),
        "BLACK": (0, 0, 0),
        "GRAY": (180, 180, 180),
        "GREEN": (0, 200, 0),
    }

    # audio subsystem - non-fatal on failure
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        print("[init] mixer OK")
    except Exception as e:
        print(f"[init][WARN] pygame.mixer.init() falhou: {e} - continuar sem áudio")

    app_state.DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d, pygame.K_v}


def manual_approve(steps_to_override):
    """Show an on-screen 'Aprovar' button and, when clicked or ENTER pressed,
    add APROVADO logs for the given step names and return True.
    This is used in non-DEV mode to force-approve failed tests and continue.
    """
    btn_w, btn_h = 220, 50
    btn_rect = pygame.Rect(app_state.WIDTH - btn_w - 20, app_state.HEIGHT - btn_h - 20, btn_w, btn_h)
    font = pygame.font.SysFont("Arial", 20)

    waiting = True
    while waiting:
        
        # Draw overlay and button
        overlay = pygame.Surface((app_state.WIDTH, app_state.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        app_state.SCREEN.blit(overlay, (0, 0))

        info_text = font.render("Teste falhou. Você pode aprovar manualmente e seguir adiante", True, (255, 255, 255))
        app_state.SCREEN.blit(info_text, (50, app_state.HEIGHT - 80))

        pygame.draw.rect(app_state.SCREEN, (0, 150, 0), btn_rect, border_radius=8)
        txt = font.render("Aprovar e continuar", True, (255, 255, 255))
        app_state.SCREEN.blit(txt, txt.get_rect(center=btn_rect.center))

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                if app_state.MODE == "DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    for step_name in steps_to_override:
                        app_state.add_log({"step": step_name + "_MANUAL_APPROVE", "time": str(datetime.now()), "result": "APROVADO"})
                    return True
                elif ev.key == pygame.K_ESCAPE:
                    # Do not approve, just return False
                    return False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1 and btn_rect.collidepoint(ev.pos):
                    for step_name in steps_to_override:
                        app_state.add_log({"step": step_name + "_MANUAL_APPROVE", "time": str(datetime.now()), "result": "APROVADO"})
                    return True

        app_state.CLOCK.tick(30)


def main():
    init_app_state()
    wait_for_db_connection()

    app_state.CONFIG = fetch_device_info()
    consulta_ntp()

    app_state.SYSTEM_INFO = get_system_info()

    has_screen = app_state.CONFIG["HAS_EMBEDDED_SCREEN"]
    has_keyboard = app_state.CONFIG["HAS_EMBEDDED_KEYBOARD"]
    has_ethernet = app_state.CONFIG["HAS_ETHERNET_PORT"]
    eth_interface = app_state.CONFIG["ETH_INTERFACE"]
    has_speaker = app_state.CONFIG["HAS_SPEAKER"]
    has_headphone = app_state.CONFIG["HAS_HEADPHONE_JACK"]
    has_microphone = app_state.CONFIG["HAS_MICROPHONE"]
    has_wifi = app_state.CONFIG["HAS_WIFI"]
    has_touchpad = app_state.CONFIG["HAS_TOUCHPAD"]
    has_camera = app_state.CONFIG["HAS_CAMERA"]
    port_map = app_state.CONFIG["PORT_MAP"]
    video_ports = app_state.CONFIG["VIDEO_PORTS"]

    init_video_state(video_ports)

    pressed_keys = set()
    state = "START_STEP"
    step = 0
    waiting_remove = False

    running = True
    while running:
        app_state.SCREEN.fill((0, 0, 0))

        legend_font = pygame.font.SysFont("Arial", 8)
        legend_surface = legend_font.render(state, True, (255, 255, 255))
        legend_rect = legend_surface.get_rect()
        legend_rect.topright = (app_state.WIDTH - 30, 20)
        app_state.SCREEN.blit(legend_surface, legend_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if app_state.MODE == "DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if app_state.MODE == "DEV":
                        save_log()
                        pygame.quit()
                        sys.exit()

                pressed_keys.add(event.key)

                if app_state.DEV_HOTKEY.issubset(pressed_keys) and app_state.MODE == "PROD":
                    pswd = prompt_password()
                    if pswd == app_state.DEV_PASSWORD:
                        print("DEV MODE UNLOCKED via hotkey!")
                        app_state.MODE = "DEV"
                    else:
                        print("Senha incorreta!")
                        pressed_keys.clear()

            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)

        if state == "START_STEP":
            start_step()
            state = "SCREEN_STEP"
            continue

        if state == "SCREEN_STEP":
            if has_screen:
                app_state.add_log({"step": "SCREEN_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                screen_step()
            state = "DONE"

        if state == "KEYBOARD_STEP":
            if has_keyboard:
                app_state.add_log({"step": "KEYBOARD_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                keyboard_step()
            state = "TOUCHPAD_STEP"

        elif state == "TOUCHPAD_STEP":
            if has_touchpad:
                app_state.add_log({"step": "TOUCHPAD_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                results = touchpad_step()
                failed = []
                for entry in results:
                    is_failed = entry.get("step") == "TOUCHPAD_REPROVED" or entry.get("result") == "REPROVADO"
                    result = "REPROVADO" if is_failed else "APROVADO"
                    app_state.add_log({"step": entry.get("step"), "time": entry.get("time"), "result": result})
                    if is_failed:
                        failed.append(entry.get("step"))
                # Allow manual override in non-DEV mode
                if failed and app_state.MODE != "DEV":
                    manual_approve(failed)
            state = "WIFI_STEP"

        elif state == "WIFI_STEP":
            if has_wifi:
                app_state.add_log({"step": "WIFI_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                wifi_test = WiFiTest(app_state.SCREEN, app_state.FONT)
                result = wifi_test.run()
                wifi_result = "APROVADO" if result.get("success") else "REPROVADO"
                app_state.add_log({"step": "WIFI_TEST", "time": str(datetime.now()), "result": wifi_result})
                if wifi_result == "REPROVADO" and app_state.MODE != "DEV":
                    manual_approve(["WIFI_TEST"])
            state = "CAMERA_STEP"

        elif state == "CAMERA_STEP":
            if has_camera:
                app_state.add_log({"step": "CAMERA_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                cam_result = camera_test_step(app_state.SCREEN, app_state.FONT, device_serial=app_state.SYSTEM_INFO.get("serial"))
                cam_status = "APROVADO" if cam_result.get("success") else "REPROVADO"
                app_state.add_log({"step": "CAMERA_TEST", "time": str(datetime.now()), "result": cam_status})
            state = "USB_STEP"

        elif state == "USB_STEP" and step < len(port_map):
            bus, port_id, port_name = port_map[step]
            if not waiting_remove:
                app_state.add_log({"step": f"USB_CONNECT_TEST_START_{port_name}", "time": str(datetime.now()), "result": "APROVADO"})
                draw_text([f"Conecte o pendrive na {port_name}..."])
                if app_state.MODE == "DEV":
                    lsusb_output = subprocess.check_output(["lsusb", "-t"], text=True)
                    dev_font = pygame.font.SysFont("Consolas", 12)
                    y = app_state.HEIGHT // 2 + 50
                    for line in lsusb_output.splitlines():
                        text_surf = dev_font.render(line, True, (0, 255, 0))
                        app_state.SCREEN.blit(text_surf, (50, y))
                        y += 20
                    pygame.display.flip()

                if port_has_device(bus, port_id):
                    waiting_remove = True
                    app_state.add_log({"step": f"USB_CONNECT_{port_name}", "time": str(datetime.now()), "result": "APROVADO"})
                    time.sleep(0.5)
            else:
                draw_text([f"Remova o pendrive da {port_name}..."])
                app_state.add_log({"step": f"USB_REMOVE_TEST_START{port_name}", "time": str(datetime.now()), "result": "APROVADO"})
                if not port_has_device(bus, port_id):
                    step += 1
                    waiting_remove = False
                    app_state.add_log({"step": f"USB_REMOVE_{port_name}", "time": str(datetime.now()), "result": "APROVADO"})
                    time.sleep(0.5)
            if step >= len(port_map):
                state = "VIDEO_STEP"

        elif state == "VIDEO_STEP":
            app_state.add_log({"step": "VIDEO_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
            outputs, all_done = get_video_status(video_ports)
            draw_video(outputs)
            if all_done:
                for output in outputs:
                    result = "APROVADO" if output["aprovado"] else "REPROVADO"
                    app_state.add_log({"step": f"VIDEO_{output['name']}_TEST", "time": str(datetime.now()), "result": result})
                # If any output failed, allow manual approval in non-DEV mode
                failed_outputs = [output['name'] for output in outputs if not output.get('aprovado')]
                if failed_outputs and app_state.MODE != "DEV":
                    manual_approve([f"VIDEO_{name}_TEST" for name in failed_outputs])
                draw_text(["Video test ok!"], (0, 255, 0))
                time.sleep(1)
                state = "HEADPHONE_STEP" if has_headphone else "SPEAKER_STEP"

        elif state == "HEADPHONE_STEP":
            app_state.add_log({"step": "HEADPHONE_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
            draw_text(["Conecte o headphone..."])
            from src.functions.audio import headphone_connected
            if app_state.MODE == "DEV":
                dev_font = pygame.font.SysFont("Consolas", 12)
                y = app_state.HEIGHT // 2 + 50
                # Mostra o sinklist
                try:
                    import pulsectl
                    pulse = pulsectl.Pulse("headphone-monitor-dev")
                    sinks = pulse.sink_list()
                    for sink in sinks:
                        port_name = sink.port_active.name if sink.port_active else "No active port"
                        text_surf = dev_font.render(f"Sink: {sink.name}, Port: {port_name}", True, (0, 255, 0))
                        app_state.SCREEN.blit(text_surf, (50, y))
                        y += 20
                    pygame.display.flip()
                except Exception as e:
                    error_surf = dev_font.render(f"Error accessing PulseAudio: {e}", True, (255, 0, 0))
                    app_state.SCREEN.blit(error_surf, (50, y))
                    pygame.display.flip()

            if headphone_connected():
                app_state.add_log({"step": "HEADPHONE_CONNECT", "time": str(datetime.now()), "result": "APROVADO"})
                state = "HEADPHONE_TESTING"
                time.sleep(0.5)

        elif state == "HEADPHONE_TESTING":
            app_state.add_log({"step": "HEADPHONE_TESTING", "time": str(datetime.now()), "result": "APROVADO"})
            play_headphone_sequence()
            state = "HEADPHONE_REMOVE"

        elif state == "HEADPHONE_REMOVE":
            draw_text(["Remova o headphone..."])
            from src.functions.audio import headphone_connected

            if not headphone_connected():
                app_state.add_log({"step": "HEADPHONE_REMOVE", "time": str(datetime.now()), "result": "APROVADO"})
                state = "SPEAKER_STEP"
                time.sleep(0.5)

        elif state == "SPEAKER_STEP":
            if has_speaker:
                app_state.add_log({"step": "SPEAKER_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                play_speaker_sequence()
            state = "MIC_STEP"

        elif state == "MIC_STEP":
            if has_microphone:
                app_state.add_log({"step": "MICROPHONE_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                test_microphone_bip()
            state = "ETHERNET_STEP"

        elif state == "ETHERNET_STEP":
            if has_ethernet:
                app_state.add_log({"step": "ETHERNET_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                ethernet_step(eth_interface)
            state = "DONE"

        elif state == "DONE":
            draw_text(["Todos os testes concluídos! Salvando log..."], (0, 255, 0))
            app_state.add_log({"step": "TEST_STOP", "time": str(datetime.now()), "result": "APROVADO"})
            save_log()
            app_state.SCREEN.fill(app_state.COLORS["WHITE"])
            draw_text(["Todos os testes concluídos!"], (0, 0, 0))
            pygame.display.flip()
            time.sleep(5)
            running = False

        app_state.CLOCK.tick(10)


if __name__ == "__main__":
    disable_alt_tab()
    try:
        main()
    finally:
        restore_alt_tab()
        pygame.quit()
        sys.exit()
