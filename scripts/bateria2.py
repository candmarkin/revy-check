import pygame
import psutil
import time
import sys
import subprocess
import os
import cv2
import matplotlib.pyplot as plt


VIDEO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "video_teste.mp4"))
TEMPO_CPU = 300  # segundos
TEMPO_VIDEO = 300  # segundos

# Inicializa pygame
pygame.init()
# seta pra rodar fullscreen na resolucao do monitor principal
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), display=0)
pygame.display.set_caption("Teste de Bateria Automático")
font = pygame.font.SysFont("Arial", 24)

clock = pygame.time.Clock()

bateria_log = []
tempo_log = []
cpu_log_video_global = []
start_time = time.time()

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
    plt.figure(figsize=(10,5))
    plt.plot(tempo_log, bateria_log, label="Bateria (%)", color='blue')
    plt.xlabel("Tempo (s)")
    plt.ylabel("Nível da Bateria (%)")
    plt.title("Teste de Consumo de Bateria")
    plt.xlim(0, 7200)  # 2 horas em segundos
    plt.grid(True)

    # Estimar duração total da bateria para cada fase
    # Fase 1: CPU 100% (primeiros TEMPO_CPU segundos)
    # Fase 2: Playback de vídeo (restante)
    if len(tempo_log) < 2:
        plt.legend()
        # Encontrar índices de transição entre as fases
        cpu_fim_idx = 0
        for i, t in enumerate(tempo_log):
            if t >= TEMPO_CPU:
                cpu_fim_idx = i
                break
        else:
            cpu_fim_idx = len(tempo_log)-1

        # CPU 100%
        if cpu_fim_idx > 1:
            dbat_cpu = bateria_log[0] - bateria_log[cpu_fim_idx]
            dt_cpu = tempo_log[cpu_fim_idx] - tempo_log[0]
            rate_cpu = dbat_cpu / dt_cpu if dt_cpu > 0 else 0.0001
            consumo_cpu = dbat_cpu
            tempo_cpu = dt_cpu
            if rate_cpu > 0:
                tempo_estimado_cpu = (bateria_log[0]) / rate_cpu
            else:
                tempo_estimado_cpu = 0
        else:
            consumo_cpu = 0
            tempo_cpu = 0
            tempo_estimado_cpu = 0

        # Playback vídeo
        if len(tempo_log) - cpu_fim_idx > 2:
            dbat_vid = bateria_log[cpu_fim_idx] - bateria_log[-1]
            dt_vid = tempo_log[-1] - tempo_log[cpu_fim_idx]
            rate_vid = dbat_vid / dt_vid if dt_vid > 0 else 0.0001
            consumo_vid = dbat_vid
            tempo_vid = dt_vid
            if rate_vid > 0:
                tempo_estimado_vid = (bateria_log[cpu_fim_idx]) / rate_vid
            else:
                tempo_estimado_vid = 0
            cpu_media_video = sum(cpu_log_video_global) / len(cpu_log_video_global) if cpu_log_video_global else 0
        else:
            consumo_vid = 0
            tempo_vid = 0
            tempo_estimado_vid = 0
            cpu_media_video = 0

        print("\n==== RESULTADOS DO TESTE ====")
        print(f"\n--- 100% CPU ---")
        print(f"Consumo de bateria: {consumo_cpu:.2f}% em {tempo_cpu:.1f}s")
        print(f"Estimativa de duração: {tempo_estimado_cpu/3600:.2f} horas")
        print(f"--- Playback de Vídeo ---")
        print(f"Consumo de bateria: {consumo_vid:.2f}% em {tempo_vid:.1f}s")
        print(f"Estimativa de duração: {tempo_estimado_vid/3600:.2f} horas")
        print(f"Consumo médio de CPU no vídeo: {cpu_media_video:.1f}%")
        # start a tiny Python worker that spins in an infinite loop



def cpu_stress():
    texto("Estágio 1: CPU a 100%", center=True)
    pygame.display.flip()
    end = time.time() + TEMPO_CPU
    last_bat_log = time.time()
    # Spawn subprocess workers to utilize other CPU cores (avoids multiprocessing spawn issues)
    cpu_count = os.cpu_count() or 1
    workers = max(0, cpu_count - 1)
    procs = []
    for _ in range(workers):
        p = subprocess.Popen([sys.executable, "-c", "while True:\n    pass"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)

    try:
        # Main process will also perform CPU work so overall usage approximates 100%
        while time.time() < end:
            # Busy work to use CPU in main process
            _ = sum(i*i for i in range(20000))
            # Atualiza tela e log de bateria a cada 0.5s
            now = time.time()
            if now - last_bat_log > 0.5:
                tempo = now - start_time
                bateria = get_bateria()
                if bateria is not None:
                    bateria_log.append(bateria)
                    tempo_log.append(round(tempo, 1))
                # use a short interval to get a recent cpu percent
                cpu = psutil.cpu_percent(interval=0.1)
                legenda = f"CPU: {cpu:.1f}%  |  Bateria: {bateria if bateria is not None else '-'}%"
                screen.fill((0,0,0))
                t = font.render("Estágio 1: CPU a 100%", True, (255,255,255))
                screen.blit(t, (30, 100))
                t2 = font.render(legenda, True, (255, 255, 0))
                screen.blit(t2, (30, 30))
                pygame.display.flip()
                last_bat_log = now
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    finally:
        # terminate worker subprocesses
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                p.wait(timeout=1)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

def video_playback():
    texto("Estágio 2: Reprodução de vídeo", center=True)
    pygame.display.flip()
    print(f"[DEBUG] Caminho do vídeo: {VIDEO_PATH}")
    cap = cv2.VideoCapture(VIDEO_PATH)
    time.sleep(1)  # Pausa antes de iniciar o vídeo
    if not cap.isOpened():
        print(f"[DEBUG] Falha ao abrir o vídeo: {VIDEO_PATH}")
        texto(f"Erro ao abrir o vídeo:\n{VIDEO_PATH}", center=True)
        pygame.display.flip()
        time.sleep(5)
        return
    start_video = time.time()
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 30  # fallback se não conseguir detectar
    frame_duration = 1.0 / fps
    print(f"[DEBUG] FPS detectado: {fps}")
    # Inicializa leitura do uso de CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_history = [cpu_percent] * 10  # média móvel simples
    cpu_idx = 0
    cpu_update_interval = 0.2  # segundos
    last_cpu_update = time.time()
    while time.time() - start_video < TEMPO_VIDEO:
        frame_start = time.time()
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop o vídeo
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(surf, (0, 0))
        # Atualiza CPU a cada cpu_update_interval
        now = time.time()
        if now - last_cpu_update > cpu_update_interval:
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_history[cpu_idx] = cpu_percent
            cpu_idx = (cpu_idx + 1) % len(cpu_history)
            last_cpu_update = now
        cpu_avg = sum(cpu_history) / len(cpu_history)
        cpu_log_video_global.append(cpu_avg)
        bateria = get_bateria()
        legenda = f"CPU: {cpu_avg:.1f}%  |  Bateria: {bateria if bateria is not None else '-'}%"
        t = font.render(legenda, True, (255, 255, 0))
        screen.blit(t, (30, 30))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                exit()
        elapsed = time.time() - frame_start
        if elapsed < frame_duration:
            time.sleep(frame_duration - elapsed)
    cap.release()



# Fluxo principal
cpu_stress()
video_playback()

texto("Teste concluído! Gerando gráfico...", center=True)
pygame.display.flip()
grafico_final()

texto("Gráfico salvo como grafico_bateria.png", center=True)
pygame.display.flip()
time.sleep(5)
pygame.quit()
