import pygame
import psutil
import requests
import threading
import time
import os
import subprocess
import matplotlib.pyplot as plt

# Configurações
VIDEO_URL = "https://file-examples.com/storage/fe5e7ae17568e94fb953bd4/2017/04/file_example_MP4_1280_10MG.mp4"
VIDEO_PATH = "video_teste.mp4"
TEMPO_CPU = 300  # segundos
TEMPO_VIDEO = 300  # segundos

# Inicializa pygame
pygame.init()
# seta pra rodar fullscreen na resolucao do monitor principal
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Teste de Bateria Automático")
font = pygame.font.SysFont("Arial", 24)

clock = pygame.time.Clock()

bateria_log = []
tempo_log = []
start_time = time.time()

def baixar_video():
    if not os.path.exists(VIDEO_PATH):
        texto("Baixando vídeo de teste...", center=True)
        pygame.display.flip()
        r = requests.get(VIDEO_URL, stream=True)
        with open(VIDEO_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def texto(msg, y=200, center=False):
    screen.fill((0, 0, 0))
    t = font.render(msg, True, (255, 255, 255))
    if center:
        rect = t.get_rect(center=(400, 240))
    else:
        rect = t.get_rect(topleft=(50, y))
    screen.blit(t, rect)

def get_bateria():
    try:
        return psutil.sensors_battery().percent
    except:
        return None

def grafico_final():
    plt.figure(figsize=(8,4))
    plt.plot(tempo_log, bateria_log, label="Bateria (%)")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Nível da Bateria (%)")
    plt.title("Teste de Consumo de Bateria")
    plt.legend()
    plt.grid(True)
    plt.savefig("grafico_bateria.png")
    plt.show()

def cpu_stress():
    texto("Estágio 1: CPU a 100%", center=True)
    pygame.display.flip()
    end = time.time() + TEMPO_CPU
    def worker():
        while time.time() < end:
            pass
    threads = []
    for _ in range(os.cpu_count()):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def video_playback():
    texto("Estágio 2: Reprodução de vídeo", center=True)
    pygame.display.flip()
    subprocess.Popen(["mpv", VIDEO_PATH, "--really-quiet", "--no-terminal"])
    time.sleep(TEMPO_VIDEO)
    os.system("pkill mpv")

def monitor_bateria():
    while True:
        tempo = time.time() - start_time
        bateria = get_bateria()
        if bateria is not None:
            bateria_log.append(bateria)
            tempo_log.append(round(tempo, 1))
        time.sleep(2)
        texto(f"Bateria: {bateria}%")
        pygame.display.flip()

monitor_thread = threading.Thread(target=monitor_bateria, daemon=True)
monitor_thread.start()

# Fluxo principal
baixar_video()
cpu_stress()
video_playback()

texto("Teste concluído! Gerando gráfico...", center=True)
pygame.display.flip()
grafico_final()

texto("Gráfico salvo como grafico_bateria.png", center=True)
pygame.display.flip()
time.sleep(5)
pygame.quit()
