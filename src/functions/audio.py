import time
from datetime import datetime

import numpy as np
import pygame
import sounddevice as sd

from src import app_state
from src.functions.gui import draw_text

SAMPLE_RATE = 44100
DURATION = 0.8
BIP_FREQ = 4000
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


def play_tone(freq, channel="both"):
    snd = generate_tone(freq, DURATION, channel)
    snd.play()
    pygame.time.wait(int(DURATION * 1000 + 50))


def play_headphone_sequence():
    for freq in FREQUENCIES:
        draw_text([f"🔊 {freq} Hz - HEADPHONE ESQUERDA"])
        play_tone(freq, "left")

        draw_text([f"🔊 {freq} Hz - HEADPHONE DIREITA"])
        play_tone(freq, "right")

        draw_text([f"🔊 {freq} Hz - HEADPHONE AMBOS"])
        play_tone(freq, "both")


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
    app_state.add_log({"step": "SPEAKER_TEST", "time": str(datetime.now()), "result": "APROVADO"})
    time.sleep(1)


def test_microphone_bip():
    threshold = 0.01
    duration_record = 1.0
    draw_text(["🎤 Teste do microfone: ouvindo bip 4kHz"])
    time.sleep(0.5)
    sound = generate_tone(BIP_FREQ, DURATION, "both")
    sound.play()
    recording = sd.rec(int(duration_record * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    amplitude = float(np.max(np.abs(recording)))
    draw_text([f"Amplitude detectada: {amplitude:.3f}"])
    time.sleep(1)
    passed = amplitude > threshold
    if passed:
        draw_text(["✅ Microfone detectou o bip!"], (0, 255, 0))
        app_state.add_log({"step": "MICROPHONE_TEST", "time": str(datetime.now()), "result": "APROVADO"})
    else:
        draw_text(["❌ Microfone não detectou o bip!"], (255, 0, 0))
        app_state.add_log({"step": "MICROPHONE_TEST", "time": str(datetime.now()), "result": "REPROVADO"})
    time.sleep(2)


try:
    import pulsectl

    _pulse = pulsectl.Pulse("headphone-monitor")
except Exception:
    _pulse = None


def headphone_connected():
    if not _pulse:
        return False
    for sink in _pulse.sink_list():
        try:
            port_name = sink.port_active.name.lower()
            if "headphone" in port_name or "analog-output-headphones" in port_name:
                return True
        except Exception:
            continue
    return False
