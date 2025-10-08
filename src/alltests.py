import pygame
import subprocess
import sys
import time
import numpy as np
import pulsectl
import sounddevice as sd
import os
import json
from datetime import datetime
import mysql.connector
from ..scripts.cadastro_portas2 import *



# Cores
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)


import mysql.connector

def fetch_device_info():
    conn = mysql.connector.connect(
        host="revy.selbetti.com.br",
        user="drack",
        password="jdVg2dF2@",
        database="revycheck"
    )

    try:
        manufacturer = subprocess.check_output("cat /sys/class/dmi/id/sys_vendor", shell=True).strip().decode("utf-8")
    except Exception:
        manufacturer = ""
    try:
        if "LENOVO" in str(manufacturer).upper():
            productname = subprocess.check_output("cat /sys/class/dmi/id/product_version", shell=True).strip().decode("utf-8")
        else:
            productname = subprocess.check_output("cat /sys/class/dmi/id/product_name", shell=True).strip().decode("utf-8")
    except Exception:
        productname = "UnknownDevice"

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("select id from devices where name=%s", (productname,))
        device = cursor.fetchone()
        if not device:
            print(f"Device '{productname}' not found in database.")
            cadastro_portas()
            fetch_device_info()

        device_id = device['id']
        print(f"Device ID for '{productname}': {device_id}")

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("SELECT bus, port, label FROM device_usb_ports WHERE device_id=%s", (device_id,))
        port_map = [(row['bus'], row['port'], row['label']) for row in cursor.fetchall()]

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("SELECT label, entry FROM device_video_ports WHERE device_id=%s", (device_id,))
        video_ports = [{"label": row['label'], "entry": row['entry']} for row in cursor.fetchall()]

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("SELECT * FROM devices WHERE id=%s", (device_id,))
        device = cursor.fetchone()

    
    return {
        "PORT_MAP": port_map,
        "VIDEO_PORTS": video_ports,
        "HAS_EMBEDDED_SCREEN": device.get("has_embedded_screen", False),
        "HAS_EMBEDDED_KEYBOARD": device.get("has_embedded_keyboard", False),
        "HAS_ETHERNET_PORT": device.get("has_ethernet_port", False),
        "ETH_INTERFACE": device.get("eth_interface", "eth0"),
        "HAS_SPEAKER": device.get("has_speaker", False),
        "HAS_HEADPHONE_JACK": device.get("has_headphone_jack", False),
        "HAS_MICROPHONE": device.get("has_microphone", False)
    }


config = fetch_device_info()

PORT_MAP = config["PORT_MAP"]
VIDEO_PORTS = config["VIDEO_PORTS"]
HAS_EMBEDDED_SCREEN = config["HAS_EMBEDDED_SCREEN"]
HAS_EMBEDDED_KEYBOARD = config["HAS_EMBEDDED_KEYBOARD"]
HAS_ETHERNET_PORT = config["HAS_ETHERNET_PORT"]
ETH_INTERFACE = config["ETH_INTERFACE"]
HAS_SPEAKER = config["HAS_SPEAKER"]
HAS_HEADPHONE_JACK = config["HAS_HEADPHONE_JACK"]
HAS_MICROPHONE = config["HAS_MICROPHONE"]


print(VIDEO_PORTS)


# Dev / Prod mode
MODE = "PROD"
DEV_PASSWORD = "dev123"

# Audio
SAMPLE_RATE = 44100
DURATION = 0.8
BIP_FREQ = 4000  # Hz
FREQUENCIES = [2000, 4000]

# Log
log_data = []

# ---------------- INIT PYGAME ---------------- #
pygame.init()
WIDTH, HEIGHT = 1920, 1080
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), display=0)
pygame.display.set_caption("Checklist Técnico Completo")
FONT = pygame.font.SysFont("Arial", 20)
CLOCK = pygame.time.Clock()
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)


if MODE == "PROD":
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)


# ---------------- DEV HOTKEY ---------------- #
DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d, pygame.K_v} # conjunto de teclas




# DESATIVANDO ALT TAB
import subprocess

def disable_alt_tab():
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.wm.keybindings",
        "switch-applications", "[]"
    ])
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.wm.keybindings",
        "switch-windows", "[]"
    ])

def restore_alt_tab():
    subprocess.run([
        "gsettings", "reset",
        "org.gnome.desktop.wm.keybindings",
        "switch-applications"
    ])
    subprocess.run([
        "gsettings", "reset",
        "org.gnome.desktop.wm.keybindings",
        "switch-windows"
    ])



# ---------------- AUDIO FUNCTIONS ---------------- #
def generate_tone(freq, duration=DURATION, channel="both"):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    if channel == "left":
        stereo_wave = np.column_stack((wave, np.zeros_like(wave)))
    elif channel == "right":
        stereo_wave = np.column_stack((np.zeros_like(wave), wave))
    else:
        stereo_wave = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo_wave)

def play_headphone_sequence():
    for freq in FREQUENCIES:
        draw_text([f"🔊 {freq} Hz - HEADPHONE ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.2)
        draw_text([f"🔊 {freq} Hz - HEADPHONE DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.2)
        draw_text([f"🔊 {freq} Hz - HEADPHONE AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.5)

def play_speaker_sequence():
    draw_text(["🔊 Teste de alto-falantes - sem headphone"])
    time.sleep(1)
    for freq in FREQUENCIES:
        draw_text([f"🔊 {freq} Hz - SPEAKER DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.3)
        draw_text([f"🔊 {freq} Hz - SPEAKER ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.3)
        draw_text([f"🔊 {freq} Hz - SPEAKER AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.3)
    draw_text(["✅ Teste de alto-falantes concluído!"], (0, 255, 0))
    log_data.append({"step":"SPEAKER_TEST","time":str(datetime.now())})
    time.sleep(1)

def test_microphone_bip():
    threshold = 0.01
    duration_record = 1.0
    draw_text(["🎤 Teste do microfone: ouvindo bip 4kHz"])
    time.sleep(0.5)
    sound = generate_tone(BIP_FREQ, DURATION, "both")
    sound.play()
    recording = sd.rec(int(duration_record * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    amplitude = float(np.max(np.abs(recording)))
    draw_text([f"Amplitude detectada: {amplitude:.3f}"])
    time.sleep(1)
    passed = amplitude > threshold
    if passed:
        draw_text(["✅ Microfone detectou o bip!"], (0, 255, 0))
    else:
        draw_text(["❌ Microfone não detectou o bip!"], (255, 0, 0))
    log_data.append({"step":"MICROPHONE_TEST","passed":passed,"amplitude":amplitude,"time":str(datetime.now())})
    time.sleep(2)

# ---------------- PULSEAUDIO ---------------- #
pulse = pulsectl.Pulse('headphone-monitor')
def headphone_connected():
    for sink in pulse.sink_list():
        port_name = sink.port_active.name.lower()
        if 'headphone' in port_name or 'analog-output-headphones' in port_name:
            return True
    return False


# ---------------- KEYBOARD ---------------- #
KEY_LAYOUT = [
    # Linha de funções
    [("Esc", pygame.K_ESCAPE, 58.5, 40), ("F1", pygame.K_F1, 58.5, 40), ("F2", pygame.K_F2, 58.5, 40), ("F3", pygame.K_F3, 58.5, 40),
     ("F4", pygame.K_F4, 58.5, 40), ("F5", pygame.K_F5, 58.5, 40), ("F6", pygame.K_F6, 58.5, 40), ("F7", pygame.K_F7, 58.5, 40),
     ("F8", pygame.K_F8, 58.5, 40), ("F9", pygame.K_F9, 58.5, 40), ("F10", pygame.K_F10, 58.5, 40), ("F11", pygame.K_F11, 58.5, 40),
     ("F12", pygame.K_F12, 58.5, 40), ("Insert", pygame.K_INSERT, 58.5, 40), ("Delete", pygame.K_DELETE, 58.5, 40)],
    
    # Números
    [("'", pygame.K_QUOTE, 60), ("1", pygame.K_1, 60), ("2", pygame.K_2, 60), ("3", pygame.K_3, 60),
     ("4", pygame.K_4, 60), ("5", pygame.K_5, 60), ("6", pygame.K_6, 60), ("7", pygame.K_7, 60),
     ("8", pygame.K_8, 60), ("9", pygame.K_9, 60), ("0", pygame.K_0, 60),
     ("-", pygame.K_MINUS, 60), ("=", pygame.K_EQUALS, 60), ("Backspace", pygame.K_BACKSPACE, 100)],

    # Linha QWERTY
    [("Tab", pygame.K_TAB, 100), ("Q", pygame.K_q, 60), ("W", pygame.K_w, 60), ("E", pygame.K_e, 60),
     ("R", pygame.K_r, 60), ("T", pygame.K_t, 60), ("Y", pygame.K_y, 60), ("U", pygame.K_u, 60),
     ("I", pygame.K_i, 60), ("O", pygame.K_o, 60), ("P", pygame.K_p, 60),
     ("´", 1073741824, 60), ("[", pygame.K_LEFTBRACKET, 60), ("Enter", pygame.K_RETURN, 60, 130)],

    # Linha ASDF
    [("Caps", pygame.K_CAPSLOCK, 110), ("A", pygame.K_a, 60), ("S", pygame.K_s, 60), ("D", pygame.K_d, 60),
     ("F", pygame.K_f, 60), ("G", pygame.K_g, 60), ("H", pygame.K_h, 60), ("J", pygame.K_j, 60),
     ("K", pygame.K_k, 60), ("L", pygame.K_l, 60), ("Ç", 231, 60),
     ("~", 1073741824, 60), ("]", pygame.K_RIGHTBRACKET, 60)],

    # Linha ZXCV
    [("Shift", pygame.K_LSHIFT, 80), (r"\\", pygame.K_BACKSLASH, 60), ("Z", pygame.K_z, 60), ("X", pygame.K_x, 60), ("C", pygame.K_c, 60),
     ("V", pygame.K_v, 60), ("B", pygame.K_b, 60), ("N", pygame.K_n, 60), ("M", pygame.K_m, 60),
     (",", pygame.K_COMMA, 60), (".", pygame.K_PERIOD, 60), (";", pygame.K_SEMICOLON, 60),
     ("Shift", pygame.K_RSHIFT, 145)],

    # Linha espaço
    [("Ctrl", pygame.K_LCTRL, 80), ("Fn", 1073741951, 60), ("Win", pygame.K_LSUPER, 60), ("Alt", pygame.K_LALT, 60),
     ("Espaço", pygame.K_SPACE, 320), ("AltGr", pygame.K_RALT, 60), ("/", pygame.K_SLASH, 60)],

     # Linha de navegação / setas
    [("←", pygame.K_LEFT, 60), 
    ("↑", pygame.K_UP, 80),
    ("↓", pygame.K_DOWN, 80), 
    ("→", pygame.K_RIGHT, 60),
    ("Pg Up", pygame.K_PAGEUP, 60),
    ("Pg Down", pygame.K_PAGEDOWN, 60),
    ]

] 

pressed_keys = set()
already_pressed = []
all_keys = []
for row in KEY_LAYOUT:
    for key in row:
        all_keys.append(key[1])

kb_button_rect = pygame.Rect(20, HEIGHT - 60, 200, 50)

def draw_keyboard():
    SCREEN.fill(WHITE)
    y=80
    for row in KEY_LAYOUT:
        x = 20

        if KEY_LAYOUT.index(row) == len(KEY_LAYOUT) - 1: # LAYOUT DAS SETAS
            x += 735
            y-= 70

            # PAGEUP
            rect = pygame.Rect(x, y, row[4][2], 28)
            if row[4][1] in pressed_keys:
                color = GREEN
            elif row[4][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[4][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # SETA ESQUERDA
            rect = pygame.Rect(x, y + 32 , row[0][2], 28)
            if row[0][1] in pressed_keys:
                color = GREEN
            elif row[0][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[0][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            x+= 65

            # SETA CIMA
            rect = pygame.Rect(x, y , row[1][2], 28)
            if row[1][1] in pressed_keys:
                color = GREEN
            elif row[1][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[1][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # SETA BAIXO
            rect = pygame.Rect(x, y + 32 , row[2][2], 28)
            if row[2][1] in pressed_keys:
                color = GREEN
            elif row[2][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[2][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            x += 85

             # SETA DIREITA
            rect = pygame.Rect(x, y + 32, row[3][2], 28)
            if row[3][1] in pressed_keys:
                color = GREEN
            elif row[3][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[3][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # PAGEDOWN
            rect = pygame.Rect(x, y, row[5][2], 28)
            if row[5][1] in pressed_keys:
                color = GREEN
            elif row[5][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[5][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)


            continue


        for key_def in row:

            if len(key_def) == 4:
                label, key, w, h = key_def
            else:
                label, key, w = key_def
                h = 60

            rect = pygame.Rect(x, y , w, h)

            if key in pressed_keys:
                color = GREEN
            elif key in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
                
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(label, True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)
            x += w + 5

        if KEY_LAYOUT.index(row) == 0:
            y += 50
            continue
        y += 70



def draw_kb_unlock_button():
    unlocked = set(all_keys).issubset(set(already_pressed))
    color = (50, 255, 50) if unlocked else (200, 200, 200)
    bordercolor = (0, 0, 0) if unlocked else (100, 100, 100)
    pygame.draw.rect(SCREEN, color, kb_button_rect, border_radius=5)
    pygame.draw.rect(SCREEN, bordercolor, kb_button_rect, 2, border_radius=5)
    text = FONT.render("Aprovar", True, bordercolor)
    SCREEN.blit(text, text.get_rect(center=kb_button_rect.center))
    return unlocked

def keyboard_step():
    global MODE
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE=="DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                pressed_keys.add(event.key)
                already_pressed.append(event.key)
                print(event.key)
                # Verifica se todas as teclas do hotkey estão pressionadas
                if DEV_HOTKEY.issubset(pressed_keys) and MODE=="PROD":
                    print("DEV MODE UNLOCKED via hotkey!")
                    MODE = "DEV"
            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)

        SCREEN.fill((240, 240, 240))
        draw_keyboard()
        unlocked = draw_kb_unlock_button()
        pygame.display.flip()
        CLOCK.tick(60)

        if unlocked:
            draw_text(["✅ Teste de teclado concluído!"], (0, 255, 0))
            log_data.append({"step":"KEYBOARD_TEST","time":str(datetime.now())})
            time.sleep(1)
            running = False


def screen_step():
    colors = [
        (0, 0, 0),       # PRETO
        (255, 255, 255), # BRANCO
        (255, 0, 0),     # VERMELHO
        (0, 255, 0),     # VERDE
        (0, 0, 255),     # AZUL
        (255, 255, 0),   # AMARELO
    ]
    global MODE
    color_index = 0

    running = True
    test_done = False
    approved = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE == "DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.KEYDOWN:
                if not test_done:
                    if event.key == pygame.K_RETURN:
                        color_index = (color_index + 1) % len(colors)
                    elif event.key == pygame.K_SPACE:
                        SCREEN.fill((0, 0, 0))
                        draw_text(["Teste concluído!",
                                   "Aperte Y para APROVAR",
                                   "ou N para REPROVAR"], (0, 255, 0))
                        pygame.display.flip()
                        test_done = True
                else:
                    if event.key == pygame.K_y:
                        approved = True
                        running = False
                    elif event.key == pygame.K_n:
                        approved = False
                        running = False

        if not test_done:
            SCREEN.fill(colors[color_index])
            pygame.display.flip()

        CLOCK.tick(60)

    # Grava resultado no log
    result = "APROVADO" if approved else "REPROVADO"
    log_data.append({"step": "SCREEN_TEST", "time": str(datetime.now()), "result": result})
    save_log()


# ---------------- USB ---------------- #
def port_has_device(bus, port_id):
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        for bus_string in output.split("/:"):
            for line in bus_string.splitlines():
                if port_id in line and "Class=Mass Storage" in line and bus in bus_string:
                    return True
    except Exception as e:
        print("Erro ao executar lsusb:", e)
    return False

# ---------------- VIDEO ---------------- #
video_aprovado = {porta["entry"]: False for porta in VIDEO_PORTS}
def get_video_status():
    drm_path = "/sys/class/drm"
    status_list = []
    all_approved = True
    for porta in VIDEO_PORTS:
        status_file = os.path.join(drm_path, porta["entry"], "status")
        status = "unknown"
        if os.path.isfile(status_file):
            with open(status_file, "r") as f:
                status = f.read().strip()
        if status == "connected":
            video_aprovado[porta["entry"]] = True
        status_list.append({"name": porta["label"], "status": status, "aprovado": video_aprovado[porta["entry"]]})
        if not video_aprovado[porta["entry"]]:
            all_approved = False
    return status_list, all_approved

def draw_video(outputs):
    SCREEN.fill((30, 30, 30))
    y = 50
    all_approved = True
    for o in outputs:
        if o['aprovado']:
            color = (0, 255, 0)
        elif o['status'] == 'connected':
            color = (0, 200, 0)
        else:
            color = (200, 0, 0)
            all_approved = False
        text = FONT.render(f"{o['name']}: {o['status']} {'(aprovado)' if o['aprovado'] else ''}", True, color)
        SCREEN.blit(text, (50, y))
        y += 50
    if all_approved:
        msg = FONT.render("Todas as portas conectadas! Pressione ESC para continuar.", True, (255, 255, 0))
    else:
        msg = FONT.render("Conecte os monitores desconectados...", True, (255, 255, 0))
    SCREEN.blit(msg, (50, y + 20))
    pygame.display.flip()
    return all_approved

# ---------------- ETHERNET ---------------- #
def ethernet_connected():
    carrier_file = f"/sys/class/net/{ETH_INTERFACE}/carrier"
    if os.path.isfile(carrier_file):
        with open(carrier_file, "r") as f:
            status = f.read().strip()
        return status == "1"
    return False

def ethernet_step():
    waiting_remove = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT and MODE=="DEV":
                return
        if not waiting_remove:
            draw_text([f"Conecte o cabo Ethernet ({ETH_INTERFACE})..."])
            if ethernet_connected():
                waiting_remove = True
                time.sleep(0.5)
        else:
            draw_text([f"Remova o cabo Ethernet ({ETH_INTERFACE})..."])
            if not ethernet_connected():
                draw_text(["✅ Teste Ethernet concluído!"], (0, 255, 0))
                log_data.append({"step":"ETHERNET_TEST","time":str(datetime.now())})
                time.sleep(1)
                break
        CLOCK.tick(5)

# ---------------- GUI ---------------- #
def draw_text(lines, color=(255, 255, 255)):
    SCREEN.fill((0, 0, 0))
    y = HEIGHT // 3
    for text in lines:
        rendered = FONT.render(text, True, color)
        rect = rendered.get_rect(center=(WIDTH // 2, y))
        SCREEN.blit(rendered, rect)
        y += 50
    pygame.display.flip()

# ---------------- DEV BUTTON ---------------- #
button_rect = pygame.Rect(WIDTH - 180, 20, 200, 200)
button_color = (200, 0, 0)
button_text = FONT.render("DEV MODE", True, (255, 255, 255))


def prompt_password():
    input_text = ""
    active = True
    while active:
        SCREEN.fill((50, 50, 50))
        prompt = FONT.render("Digite senha DEV:", True, (255, 255, 0))
        SCREEN.blit(prompt, (50, 200))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT and MODE=="DEV":
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
    return input_text

# ---------------- MAIN ---------------- #
def main():
    global MODE  # Declare no início
    clock = pygame.time.Clock()
    state = "SCREEN_STEP"
    step = 0
    waiting_remove = False

    while True:
        SCREEN.fill((0,0,0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE=="DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if MODE=="DEV":
                        save_log()
                        pygame.quit()
                        sys.exit()

                pressed_keys.add(event.key)
                print(event.key)
                # Verifica se todas as teclas do hotkey estão pressionadas
                if DEV_HOTKEY.issubset(pressed_keys) and MODE=="PROD":
                    pswd = prompt_password()
                    if pswd == DEV_PASSWORD:
                        print("DEV MODE UNLOCKED via hotkey!")
                        MODE = "DEV"
                    else:
                        print("Senha incorreta!")
                        pressed_keys.clear()

            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)


        # ---------------- TELA ---------------- #
        if state == "SCREEN_STEP":
            if HAS_EMBEDDED_SCREEN:
                screen_step()
            state = "KEYBOARD_STEP"
        # ---------------- TECLADO ---------------- #
        if state == "KEYBOARD_STEP":
            if HAS_EMBEDDED_KEYBOARD:
                keyboard_step()
            state = "USB_STEP"
        # ---------------- USB ---------------- #
        elif state == "USB_STEP" and step < len(PORT_MAP):
            bus, port_id, port_name = PORT_MAP[step]
            if not waiting_remove:
                draw_text([f"Conecte o pendrive na {port_name}..."])
                if port_has_device(bus, port_id):
                    waiting_remove = True
                    log_data.append({"step":f"USB_CONNECT_{port_name}","time":str(datetime.now())})
                    time.sleep(0.5)
            else:
                draw_text([f"Remova o pendrive da {port_name}..."])
                if not port_has_device(bus, port_id):
                    step += 1
                    waiting_remove = False
                    log_data.append({"step":f"USB_REMOVE_{port_name}","time":str(datetime.now())})
                    time.sleep(0.5)
            if step >= len(PORT_MAP):
                state = "VIDEO_STEP"

        # ---------------- VIDEO ---------------- #
        elif state == "VIDEO_STEP":
            outputs, all_done = get_video_status()
            draw_video(outputs)
            if all_done:
                draw_text(["✅ Video test ok! Pressione ESC para continuar"], (0, 255, 0))
                state = "HEADPHONE_STEP" if HAS_HEADPHONE_JACK else "SPEAKER_STEP"

        # ---------------- HEADPHONE ---------------- #
        elif state == "HEADPHONE_STEP":
            draw_text(["👉 Conecte o headphone..."])
            if headphone_connected():
                log_data.append({"step":"HEADPHONE_CONNECT","time":str(datetime.now())})
                state = "HEADPHONE_TESTING"
                time.sleep(0.5)

        elif state == "HEADPHONE_TESTING":
            play_headphone_sequence()
            state = "HEADPHONE_REMOVE"

        elif state == "HEADPHONE_REMOVE":
            draw_text(["👉 Remova o headphone..."])
            if not headphone_connected():
                log_data.append({"step":"HEADPHONE_REMOVE","time":str(datetime.now())})
                state = "SPEAKER_STEP"
                time.sleep(0.5)

        # ---------------- SPEAKER ---------------- #
        elif state == "SPEAKER_STEP":
            if HAS_SPEAKER:
                play_speaker_sequence()
            state = "MIC_STEP"

        # ---------------- MICROFONE ---------------- #
        elif state == "MIC_STEP":
            if HAS_MICROPHONE:
                test_microphone_bip()
            state = "ETHERNET_STEP"

        # ---------------- ETHERNET ---------------- #
        elif state == "ETHERNET_STEP":
            if HAS_ETHERNET_PORT:
                ethernet_step()
            state = "DONE"

        # ---------------- DONE ---------------- #
        elif state == "DONE":
            draw_text(["✅ Todos os testes concluídos!"], (0, 255, 0))

        CLOCK.tick(10)

def save_log():
    with open("checklist_log.json","w") as f:
        json.dump(log_data,f,indent=2)

