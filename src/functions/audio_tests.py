"""
Funções de teste de áudio: headphone, speaker, microfone
"""
import pygame
import numpy as np
import sounddevice as sd
import time
from datetime import datetime


# Configurações de áudio
SAMPLE_RATE = 44100
DURATION = 0.8
BIP_FREQ = 4000  # Hz
FREQUENCIES = [2000, 4000]


def generate_tone(freq, duration=DURATION, channel="both"):
    """Gera um tom de áudio para teste"""
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
    """Toca um tom de áudio"""
    snd = generate_tone(freq, DURATION, channel)
    snd.play()
    pygame.time.wait(int(DURATION * 1000 + 50))


def play_headphone_sequence(draw_text_func):
    """
    Executa sequência de teste de headphone
    
    Args:
        draw_text_func: Função para desenhar texto na tela
    """
    for freq in FREQUENCIES:
        draw_text_func([f"🔊 {freq} Hz - HEADPHONE ESQUERDA"])
        play_tone(freq, "left")

        draw_text_func([f"🔊 {freq} Hz - HEADPHONE DIREITA"])
        play_tone(freq, "right")

        draw_text_func([f"🔊 {freq} Hz - HEADPHONE AMBOS"])
        play_tone(freq, "both")


def play_speaker_sequence(draw_text_func, add_log_func):
    """
    Executa sequência de teste de alto-falantes
    
    Args:
        draw_text_func: Função para desenhar texto na tela
        add_log_func: Função para adicionar log
    """
    draw_text_func(["🔊 Teste de alto-falantes - sem headphone"])
    time.sleep(1)
    
    for freq in FREQUENCIES:
        draw_text_func([f"🔊 {freq} Hz - SPEAKER DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.3)
        
        draw_text_func([f"🔊 {freq} Hz - SPEAKER ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.3)
        
        draw_text_func([f"🔊 {freq} Hz - SPEAKER AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.3)
    
    draw_text_func(["✅ Teste de alto-falantes concluído!"], (0, 255, 0))
    add_log_func({"step": "SPEAKER_TEST", "time": str(datetime.now()), "result": "APROVADO"})
    time.sleep(1)


def test_microphone_bip(draw_text_func, add_log_func):
    """
    Testa o microfone tocando um bip e gravando
    
    Args:
        draw_text_func: Função para desenhar texto na tela
        add_log_func: Função para adicionar log
    """
    threshold = 0.01
    duration_record = 1.0
    
    draw_text_func(["🎤 Teste do microfone: ouvindo bip 4kHz"])
    time.sleep(0.5)
    
    sound = generate_tone(BIP_FREQ, DURATION, "both")
    sound.play()
    
    recording = sd.rec(int(duration_record * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    
    amplitude = float(np.max(np.abs(recording)))
    draw_text_func([f"Amplitude detectada: {amplitude:.3f}"])
    time.sleep(1)
    
    passed = amplitude > threshold
    if passed:
        draw_text_func(["✅ Microfone detectou o bip!"], (0, 255, 0))
        add_log_func({"step": "MICROPHONE_TEST", "time": str(datetime.now()), "result": "APROVADO"})
    else:
        draw_text_func(["❌ Microfone não detectou o bip!"], (255, 0, 0))
        add_log_func({"step": "MICROPHONE_TEST", "time": str(datetime.now()), "result": "REPROVADO"})
    
    time.sleep(2)
