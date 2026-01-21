
# import pulsectl
import sounddevice as sd
import numpy as np
import pygame.sndarray
import time
from datetime import datetime
from functions.gui import print
from ..main import log_data

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
        print([f"🔊 {freq} Hz - HEADPHONE ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.2)
        print([f"🔊 {freq} Hz - HEADPHONE DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.2)
        print([f"🔊 {freq} Hz - HEADPHONE AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.5)

def play_speaker_sequence():
    
    print(["🔊 Teste de alto-falantes - sem headphone"])
    time.sleep(1)
    for freq in FREQUENCIES:
        print([f"🔊 {freq} Hz - SPEAKER DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.3)
        print([f"🔊 {freq} Hz - SPEAKER ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.3)
        print([f"🔊 {freq} Hz - SPEAKER AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.3)
    print(["✅ Teste de alto-falantes concluído!"], (0, 255, 0))
    log_data.append({"step":"SPEAKER_TEST","time":str(datetime.now())})
    time.sleep(1)

def test_microphone_bip():

    threshold = 0.01
    duration_record = 1.0
    print(["🎤 Teste do microfone: ouvindo bip 4kHz"])
    time.sleep(0.5)
    sound = generate_tone(BIP_FREQ, DURATION, "both")
    sound.play()
    recording = sd.rec(int(duration_record * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    amplitude = float(np.max(np.abs(recording)))
    print([f"Amplitude detectada: {amplitude:.3f}"])
    time.sleep(1)
    passed = amplitude > threshold
    if passed:
        print(["✅ Microfone detectou o bip!"], (0, 255, 0))
    else:
        print(["❌ Microfone não detectou o bip!"], (255, 0, 0))
    log_data.append({"step":"MICROPHONE_TEST","passed":passed,"amplitude":amplitude,"time":str(datetime.now())})
    time.sleep(2)



# pulse = pulsectl.Pulse('headphone-monitor')
def headphone_connected():
    """
    Detecta se um fone de ouvido está conectado via PulseAudio.
    NOTA: Em alguns sistemas (ex: Lenovo Thinkpad), pode haver detecção falsa.
    Use a função com confirmação manual em alltests.py para melhor confiabilidade.
    """
    try:
        pulse = pulsectl.Pulse('headphone-monitor')
        for sink in pulse.sink_list():
            try:
                port_name = sink.port_active.name.lower()
                if 'headphone' in port_name or 'analog-output-headphones' in port_name:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def showConnectedHeadphoneStatus():
    if headphone_connected():
        # mostra sinklist para debug
        pulse = pulsectl.Pulse('headphone-monitor')
        for sink in pulse.sink_list():
            print(f"Sink: {sink.name}, Active Port: {sink.port_active.name}")
        print(["🎧 Fone de ouvido conectado"], (0, 255, 0))
    else:
        print(["❌ Fone de ouvido não detectado"], (255, 0, 0))
        pulse = pulsectl.Pulse('headphone-monitor')
        for sink in pulse.sink_list():
            print(f"Sink: {sink.name}, Active Port: {sink.port_active.name}")


if __name__ == "__main__":
     showConnectedHeadphoneStatus()