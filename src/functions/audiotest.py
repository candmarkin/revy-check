# Baseado em audio.py, mas apenas via terminal (sem interface gráfica).
# Opção 1: printa se o headphone está conectado ou não
# Opção 2: toca um som e pede para o usuário confirmar se ouviu ou não
# Opção 3: toca um som e tenta detectar se o microfone captou o som

import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
DURATION = 0.8
BIP_FREQ = 4000
FREQUENCIES = [2000, 4000]

try:
    import pulsectl

    _pulse = pulsectl.Pulse("headphone-monitor")
except Exception:
    _pulse = None


def generate_tone(freq, duration=DURATION, channel="both"):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)

    if channel == "left":
        stereo = np.column_stack((wave, np.zeros_like(wave)))
    elif channel == "right":
        stereo = np.column_stack((np.zeros_like(wave), wave))
    else:
        stereo = np.column_stack((wave, wave))

    return stereo


def play_tone(freq, channel="both", duration=DURATION):
    tone = generate_tone(freq, duration, channel)
    sd.play(tone, samplerate=SAMPLE_RATE)
    sd.wait()


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


def option_check_headphone():
    if _pulse is None:
        print("⚠️  pulsectl não disponível - não foi possível detectar o headphone.")
        return
    if headphone_connected():
        print("✅ Headphone CONECTADO")
    else:
        print("❌ Headphone NÃO conectado")


def option_play_and_confirm():
    print(f"🔊 Tocando bip de {BIP_FREQ} Hz...")
    play_tone(BIP_FREQ, "both")
    resp = input("Você ouviu o som? [s/N]: ").strip().lower()
    if resp == "s":
        print("✅ Áudio APROVADO")
    else:
        print("❌ Áudio REPROVADO")


def option_microphone_test():
    threshold = 0.01
    duration_record = 1.0
    print(f"🎤 Teste do microfone: tocando bip de {BIP_FREQ} Hz e gravando...")
    time.sleep(0.5)

    tone = generate_tone(BIP_FREQ, DURATION, "both")
    sd.play(tone, samplerate=SAMPLE_RATE)
    recording = sd.rec(
        int(duration_record * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()

    amplitude = float(np.max(np.abs(recording)))
    print(f"Amplitude detectada: {amplitude:.3f}")
    if amplitude > threshold:
        print("✅ Microfone detectou o bip!")
    else:
        print("❌ Microfone NÃO detectou o bip!")


def menu():
    while True:
        print("\n=== Teste de Áudio ===")
        print("1) Verificar se o headphone está conectado")
        print("2) Tocar som e confirmar se ouviu")
        print("3) Testar microfone (toca som e detecta captura)")
        print("0) Sair")
        choice = input("Escolha: ").strip()

        if choice == "1":
            option_check_headphone()
        elif choice == "2":
            option_play_and_confirm()
        elif choice == "3":
            option_microphone_test()
        elif choice == "0":
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
