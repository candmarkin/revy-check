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

# USB
PORT_MAP = [
    ("Port 001:", "USB-C Esquerdo 1"),
    ("Port 003:", "USB-A Esquerdo 1"),
    ("Port 002:", "USB-A Direito 1"),
    ("Port 004:", "USB-A Direito 1")
]

# Teclado
HAS_EMBEDDED_KEYBOARD = True

# Video
VIDEO_PORTS = ["card1-eDP-1", "card1-HDMI-A-1"]

# Ethernet
HAS_ETHERNET_PORT = True
ETH_INTERFACE = "eno2"

# Headphone / Microphone
HAS_SPEAKER = True
HAS_HEADPHONE_JACK = True
HAS_MICROPHONE = True

# Dev / Prod mode
MODE = "PROD"
DEV_PASSWORD = os.getenv("dev_mode_pswd")

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
FONT = pygame.font.SysFont("Arial", 28)
CLOCK = pygame.time.Clock()
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)


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

# ---------------- USB ---------------- #
def port_has_device(port_id):
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        for line in output.splitlines():
            if port_id in line and "Dev " and "Class=Mass Storage" in line:
                return True
    except Exception as e:
        print("Erro ao executar lsusb:", e)
    return False

# ---------------- VIDEO ---------------- #
video_aprovado = {porta: False for porta in VIDEO_PORTS}
def get_video_status():
    drm_path = "/sys/class/drm"
    status_list = []
    all_approved = True
    for porta in VIDEO_PORTS:
        status_file = os.path.join(drm_path, porta, "status")
        status = "unknown"
        if os.path.isfile(status_file):
            with open(status_file, "r") as f:
                status = f.read().strip()
        if status == "connected":
            video_aprovado[porta] = True
        status_list.append({"name": porta, "status": status, "aprovado": video_aprovado[porta]})
        if not video_aprovado[porta]:
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

def draw_dev_button():
    pygame.draw.rect(SCREEN, button_color, button_rect)
    SCREEN.blit(button_text, (button_rect.x + 10, button_rect.y + 10))

def prompt_password():
    input_text = ""
    active = True
    while active:
        SCREEN.fill((50, 50, 50))
        prompt = FONT.render("Digite senha DEV:", True, (255, 255, 0))
        text_surface = FONT.render(input_text, True, (255, 255, 255))
        SCREEN.blit(prompt, (50, 200))
        SCREEN.blit(text_surface, (50, 250))
        draw_dev_button()
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
    state = "USB_STEP"
    step = 0
    waiting_remove = False
    # ---------------- DEV HOTKEY ---------------- #
    keys_pressed = set()  # armazena teclas atualmente pressionadas
    DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d, pygame.K_v}  # conjunto de teclas

    while True:
        SCREEN.fill((0,0,0))
        if MODE=="PROD":
            draw_dev_button()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE=="DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.KEYDOWN:
                keys_pressed.add(event.key)
                # Verifica se todas as teclas do hotkey estão pressionadas
                if DEV_HOTKEY.issubset(keys_pressed) and MODE=="PROD":
                    print("DEV MODE UNLOCKED via hotkey!")
                    MODE = "DEV"
            elif event.type == pygame.KEYUP:
                if event.key in keys_pressed:
                    keys_pressed.remove(event.key)

        # ---------------- USB ---------------- #
        if state == "USB_STEP" and step < len(PORT_MAP):
            port_id, port_name = PORT_MAP[step]
            if not waiting_remove:
                draw_text([f"Conecte o pendrive na {port_name}..."])
                if port_has_device(port_id):
                    waiting_remove = True
                    log_data.append({"step":f"USB_CONNECT_{port_name}","time":str(datetime.now())})
                    time.sleep(0.5)
            else:
                draw_text([f"Remova o pendrive da {port_name}..."])
                if not port_has_device(port_id):
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
                state = "HEADPHONE_STEP"

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
            play_speaker_sequence()
            state = "MIC_STEP" if TEST_MICROPHONE else "ETHERNET_STEP" if HAS_ETHERNET_PORT else "DONE"

        # ---------------- MICROFONE ---------------- #
        elif state == "MIC_STEP":
            test_microphone_bip()
            state = "ETHERNET_STEP" if HAS_ETHERNET_PORT else "DONE"

        # ---------------- ETHERNET ---------------- #
        elif state == "ETHERNET_STEP":
            ethernet_step()
            state = "DONE"

        # ---------------- DONE ---------------- #
        elif state == "DONE":
            draw_text(["✅ Todos os testes concluídos!"], (0, 255, 0))

        CLOCK.tick(10)

def save_log():
    with open("checklist_log.json","w") as f:
        json.dump(log_data,f,indent=2)

if __name__ == "__main__":
    main()
