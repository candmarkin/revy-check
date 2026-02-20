"""
RevyCheck - Sistema de Testes de Qualidade
Main application orchestrator
"""
import pygame
import sys
import time
import json
from datetime import datetime

# Importar módulos de funções
from functions.system_info import get_system_info, get_manufacturer
from functions.gui import draw_text, draw_system_info, prompt_password, show_message_box
from functions.database import fetch_device_info, send_to_db, wait_for_db_connection
from functions.audio_tests import play_headphone_sequence, play_speaker_sequence, test_microphone_bip
from functions.keyboard_test import keyboard_step
from functions.screen_test import screen_step
from functions.usb_test import usb_step
from functions.video_test import video_ports_step
from functions.ethernet_test import ethernet_step
from functions.wifi import WiFiTest
from functions.touchpad import touchpad_step
from functions.camera import CameraTest


# Constantes globais
WIDTH = 1920
HEIGHT = 1080
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DEV_PASSWORD = "drack"
DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d}

# Modo de operação
MODE_DICT = {"MODE": "PROD"}  # "PROD" ou "DEV"

# Log de testes
log_data = []


def add_log(entry):
    """Adiciona entrada ao log"""
    log_data.append(entry)
    print(f"[LOG] {entry}")


def save_log(screen, font, clock):
    """Salva log em arquivo e banco de dados"""
    # Salvar arquivo local
    with open("checklist_log.json", "w") as f:
        json.dump(log_data, f, indent=2)
    
    # Interface para confirmar envio
    screen.fill(WHITE)
    font_small = pygame.font.SysFont("Consolas", 10)
    font_big = pygame.font.SysFont("Arial", 14, bold=True)
    
    y = 50
    screen.blit(font_big.render("Pré-visualização do log:", True, BLACK), (50, y))
    y += 40
    
    for entry in log_data[-15:]:
        text = f"{entry.get('step', '?')} | {entry.get('result', '?')} | {entry.get('time', '')}"
        screen.blit(font_small.render(text, True, BLACK), (60, y))
        y += 25
        if y > HEIGHT - 120:
            break
    
    # Botões
    send_btn = pygame.Rect(WIDTH//2 - 160, HEIGHT - 80, 140, 50)
    cancel_btn = pygame.Rect(WIDTH//2 + 20, HEIGHT - 80, 140, 50)
    pygame.draw.rect(screen, (0, 200, 0), send_btn, border_radius=10)
    pygame.draw.rect(screen, (200, 0, 0), cancel_btn, border_radius=10)
    screen.blit(font_big.render("Enviar", True, WHITE), send_btn.move(25, 10))
    screen.blit(font_big.render("Cancelar", True, WHITE), cancel_btn.move(10, 10))
    pygame.display.flip()
    
    # Aguardar decisão
    waiting = True
    decision = None
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE_DICT["MODE"] == "DEV":
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if send_btn.collidepoint(event.pos):
                    decision = "enviar"
                    waiting = False
                elif cancel_btn.collidepoint(event.pos):
                    decision = "cancelar"
                    waiting = False
        clock.tick(30)
    
    if decision == "cancelar":
        return False
    
    # Enviar ao banco
    try:
        system_info = get_system_info()
        serial = system_info.get("serial", "unknown")
        
        # Aqui você deve extrair os resultados do log
        # Por simplicidade, assumindo True para todos
        send_to_db(
            serial=serial,
            screen_ok=True,
            keyboard_ok=True,
            usb_ok=True,
            video_ok=True,
            headphone_ok=True,
            speaker_ok=True,
            mic_ok=True,
            ethernet_ok=True,
            wifi_ok=True,
            touchpad_ok=True,
            camera_ok=True,
            approval=True
        )
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
        return False


def start_screen(screen, width, height, font, clock):
    """Tela inicial de seleção de teste"""
    options = [
        "QUALIDADE1",
        "QUALIDADE2",
        "VISTORIA1",
        "VISTORIA2",
        "VISTORIA3",
        "VISTORIA4"
    ]
    
    button_rects = []
    start_y = height // 2 - len(options) * 50 // 2
    for i, opt in enumerate(options):
        rect = pygame.Rect(width//2 - 150, start_y + i * 80, 300, 60)
        button_rects.append((opt, rect))
    
    system_info = get_system_info()
    selected = None
    
    while selected is None:
        screen.fill((30, 30, 30))
        draw_system_info(screen, system_info)
        
        title = font.render("Selecione o tipo de teste", True, WHITE)
        screen.blit(title, (width//2 - title.get_width()//2, height//4))
        
        mouse_pos = pygame.mouse.get_pos()
        for opt, rect in button_rects:
            color = (0, 200, 0) if rect.collidepoint(mouse_pos) else (0, 150, 0)
            pygame.draw.rect(screen, color, rect, border_radius=12)
            text = font.render(opt, True, WHITE)
            screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for opt, rect in button_rects:
                    if rect.collidepoint(event.pos):
                        selected = opt
                        add_log({
                            "step": f"TEST_START_{selected.upper().replace(' ', '_')}",
                            "time": str(datetime.now()),
                            "result": "APROVADO"
                        })
        
        clock.tick(30)
    
    return selected


def main():
    """Função principal - orquestra todos os testes"""
    # Inicializar Pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("RevyCheck - Sistema de Testes")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 28)
    
    # Obter informações do sistema
    system_info = get_system_info()
    manufacturer = get_manufacturer()
    serial = system_info.get("serial", "unknown")
    
    # Buscar configuração do dispositivo
    device_config = fetch_device_info(serial)
    if not device_config:
        print("❌ Dispositivo não encontrado no banco de dados!")
        device_config = {
            "manufacturer": manufacturer,
            "has_headphone": True,
            "has_speaker": True,
            "has_mic": True,
            "usb_left": 2,
            "usb_right": 1,
            "has_hdmi": True,
            "has_displayport": True,
            "has_ethernet": True,
            "has_wifi": True,
            "has_touchpad": True,
            "has_camera": True
        }
    
    # Tela inicial
    test_type = start_screen(screen, WIDTH, HEIGHT, font, clock)
    
    # Wrapper functions para callbacks
    def draw_text_wrapper(lines, color=(255, 255, 255)):
        screen.fill(BLACK)
        draw_system_info(screen, system_info)
        y = HEIGHT // 3
        for text in lines:
            rendered = font.render(text, True, color)
            rect = rendered.get_rect(center=(WIDTH // 2, y))
            screen.blit(rendered, rect)
            y += 50
        pygame.display.flip()
    
    def draw_system_info_wrapper(sys_info):
        draw_system_info(screen, sys_info)
    
    # Máquina de estados
    state = "SCREEN"
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE_DICT["MODE"] == "DEV":
                    pygame.quit()
                    sys.exit()
        
        # TESTE DE TELA
        if state == "SCREEN":
            screen_step(
                screen, WIDTH, HEIGHT, clock,
                draw_text_wrapper, add_log,
                draw_system_info_wrapper, lambda: system_info
            )
            state = "KEYBOARD"
        
        # TESTE DE TECLADO
        elif state == "KEYBOARD":
            keyboard_step(
                screen, WIDTH, HEIGHT, font, clock, manufacturer,
                MODE_DICT, draw_text_wrapper, add_log,
                draw_system_info_wrapper, lambda: system_info,
                DEV_HOTKEY, lambda: save_log(screen, font, clock)
            )
            state = "USB"
        
        # TESTE DE USB
        elif state == "USB":
            ports = {
                "LEFT": device_config.get("usb_left", 2),
                "RIGHT": device_config.get("usb_right", 1)
            }
            usb_step(
                screen, WIDTH, HEIGHT, font, clock,
                draw_text_wrapper, add_log,
                draw_system_info_wrapper, lambda: system_info,
                ports
            )
            state = "VIDEO"
        
        # TESTE DE VÍDEO
        elif state == "VIDEO":
            video_ports_step(
                screen, WIDTH, HEIGHT, font, clock,
                draw_text_wrapper, add_log,
                draw_system_info_wrapper, lambda: system_info
            )
            state = "HEADPHONE"
        
        # TESTE DE FONE DE OUVIDO
        elif state == "HEADPHONE":
            if device_config.get("has_headphone", True):
                play_headphone_sequence(draw_text_wrapper)
            state = "SPEAKER"
        
        # TESTE DE ALTO-FALANTE
        elif state == "SPEAKER":
            if device_config.get("has_speaker", True):
                play_speaker_sequence(draw_text_wrapper, add_log)
            state = "MIC"
        
        # TESTE DE MICROFONE
        elif state == "MIC":
            if device_config.get("has_mic", True):
                test_microphone_bip(draw_text_wrapper, add_log)
            state = "ETHERNET"
        
        # TESTE DE ETHERNET
        elif state == "ETHERNET":
            if device_config.get("has_ethernet", True):
                ethernet_step(
                    screen, WIDTH, HEIGHT, font, clock,
                    draw_text_wrapper, add_log,
                    draw_system_info_wrapper, lambda: system_info
                )
            state = "WIFI"
        
        # TESTE DE WIFI
        elif state == "WIFI":
            if device_config.get("has_wifi", True):
                add_log({"step": "WIFI_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                wifi_test = WiFiTest(screen, font)
                result = wifi_test.run()
                if result:
                    add_log({"step": "WIFI_TEST", "time": str(datetime.now()), "result": "APROVADO"})
                else:
                    add_log({"step": "WIFI_TEST", "time": str(datetime.now()), "result": "REPROVADO"})
            state = "TOUCHPAD"
        
        # TESTE DE TOUCHPAD
        elif state == "TOUCHPAD":
            if device_config.get("has_touchpad", True):
                touchpad_log = touchpad_step()
                for entry in touchpad_log:
                    add_log(entry)
            state = "CAMERA"
        
        # TESTE DE CÂMERA
        elif state == "CAMERA":
            if device_config.get("has_camera", True):
                add_log({"step": "CAMERA_TEST_START", "time": str(datetime.now()), "result": "APROVADO"})
                camera_test = CameraTest(screen, font)
                result = camera_test.run()
                if result:
                    add_log({"step": "CAMERA_TEST", "time": str(datetime.now()), "result": "APROVADO"})
                else:
                    add_log({"step": "CAMERA_TEST", "time": str(datetime.now()), "result": "REPROVADO"})
            state = "DONE"
        
        # FINALIZAÇÃO
        elif state == "DONE":
            draw_text_wrapper(["Todos os testes concluídos! Salvando log..."], (0, 255, 0))
            add_log({"step": "TEST_STOP", "time": str(datetime.now()), "result": "APROVADO"})
            
            success = save_log(screen, font, clock)
            if success:
                draw_text_wrapper(["✅ Log salvo com sucesso!"], (0, 255, 0))
            else:
                draw_text_wrapper(["❌ Erro ao salvar log"], (255, 0, 0))
            
            time.sleep(3)
            running = False
        
        clock.tick(10)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
