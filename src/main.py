import pygame

from functions.fetch_device_info import fetch_device_info
from functions.audio import *
from functions.save_log import save_log
from functions.keyboard import *
from functions.screen import screen_step
from functions.usb import port_has_device
from functions.video_ports import get_video_status, draw_video
from functions.ethernet import ethernet_step, ethernet_connected


import sys
import time
from datetime import datetime



# Cores
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)


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

video_aprovado = {porta["entry"]: False for porta in VIDEO_PORTS}


# Dev / Prod mode
MODE = "PROD"
DEV_PASSWORD = "dev123"

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


# AUDIO

import pulsectl
import sounddevice as sd
import numpy as np
import pygame.sndarray
import time
from datetime import datetime
from functions.gui import draw_text

# CONFIGS
SAMPLE_RATE = 44100
DURATION = 0.8
BIP_FREQ = 4000 #Hz
FREQUENCIES = [2000, 4000]


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
    global log_data


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



pulse = pulsectl.Pulse('headphone-monitor')
def headphone_connected():
    for sink in pulse.sink_list():
        port_name = sink.port_active.name.lower()
        if 'headphone' in port_name or 'analog-output-headphones' in port_name:
            return True
    return False



# ---------------- DEV HOTKEY ---------------- #
DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d, pygame.K_v} # conjunto de teclas

# ---------------- DEV BUTTON ---------------- #
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
    global MODE
    state = "SCREEN_STEP"
    step = 0
    waiting_remove = False

    while True:
        SCREEN.fill((0,0,0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE=="DEV":
                    save_log(log_data)
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if MODE=="DEV":
                        save_log(log_data)
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



