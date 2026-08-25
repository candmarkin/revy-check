import time
from datetime import datetime

import numpy as np
import pygame
import sounddevice as sd

from src import app_state, hal
from src.functions.gui import ask_operator, draw_text

# Y aprova, N reprova, R repete - mesmo contrato do screen_step.
_VERDICT_OPTIONS = {
    pygame.K_y: ("Y = aprovar", "aprovado"),
    pygame.K_n: ("N = reprovar", "reprovado"),
    pygame.K_r: ("R = repetir", "repetir"),
}

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
    while True:
        for freq in FREQUENCIES:
            draw_text([f"🔊 {freq} Hz - HEADPHONE ESQUERDA"])
            play_tone(freq, "left")

            draw_text([f"🔊 {freq} Hz - HEADPHONE DIREITA"])
            play_tone(freq, "right")

            draw_text([f"🔊 {freq} Hz - HEADPHONE AMBOS"])
            play_tone(freq, "both")

        # Antes o passo so' registrava que os tons tocaram; se o headphone
        # estivesse mudo nada aparecia no log.
        verdict = ask_operator(
            ["Ouviu os tons nos dois lados do headphone?"], _VERDICT_OPTIONS
        )
        if verdict == "repetir":
            continue

        result = "APROVADO" if verdict == "aprovado" else "REPROVADO"
        app_state.add_log({"step": "HEADPHONE_TEST", "time": str(datetime.now()), "result": result})
        return result


def play_speaker_sequence():
    while True:
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

        # O passo tocava os tons e ja' gravava APROVADO sozinho: alto-falante
        # mudo passava no teste. Quem aprova e' o operador que ouviu.
        verdict = ask_operator(
            ["Ouviu os tons nos dois alto-falantes?"], _VERDICT_OPTIONS
        )
        if verdict == "repetir":
            continue

        result = "APROVADO" if verdict == "aprovado" else "REPROVADO"
        if result == "APROVADO":
            draw_text(["✅ Teste de alto-falantes concluído!"], (0, 255, 0))
        else:
            draw_text(["❌ Alto-falantes reprovados!"], (255, 0, 0))
        app_state.add_log({"step": "SPEAKER_TEST", "time": str(datetime.now()), "result": result})
        time.sleep(1)
        return result


def test_microphone_bip():
    threshold = 0.01
    duration_record = 1.0

    while True:
        draw_text(["🎤 Teste do microfone: ouvindo bip 4kHz"])
        time.sleep(0.5)
        sound = generate_tone(BIP_FREQ, DURATION, "both")
        sound.play()
        try:
            recording = sd.rec(int(duration_record * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()
            amplitude = float(np.max(np.abs(recording)))
            detected = amplitude > threshold
            status = f"Amplitude detectada: {amplitude:.3f}"
        except Exception as exc:
            # Sem placa/permissao de captura o passo inteiro estourava.
            detected = False
            status = f"Falha ao gravar: {type(exc).__name__}"

        if detected:
            lines = [status, "✅ Microfone detectou o bip!"]
        else:
            lines = [status, "❌ Microfone não detectou o bip!"]

        verdict = ask_operator(lines, _VERDICT_OPTIONS)
        if verdict == "repetir":
            continue

        result = "APROVADO" if verdict == "aprovado" else "REPROVADO"
        app_state.add_log({"step": "MICROPHONE_TEST", "time": str(datetime.now()), "result": result})
        time.sleep(1)
        return result


def jack_detection_available():
    """False quando o SO nao sabe dizer se ha' algo no jack.

    Sem isso quem chama nao distingue "nenhum headphone plugado" de "nao da'
    para detectar headphone nenhum", e o passo espera para sempre um evento
    que nunca vai chegar.
    """
    return hal.jack_detection_available()


def jack_detection_error():
    return hal.jack_detection_error()


def headphone_connected():
    return hal.headphone_connected()
