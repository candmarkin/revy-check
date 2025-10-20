import platform
import subprocess as sp
import json
import requests

# URL da API para envio do relatório
API_URL = "http://revy.selbetti.com.br:8000/relatoriorevycheck"  # Altere para o endpoint desejado
import pygame
import psutil
import time
import sys
import os
import cv2
import ctypes
import multiprocessing

# Support running from a PyInstaller bundle: use sys._MEIPASS when available
if getattr(sys, 'frozen', False):
    _base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    _base_path = os.path.dirname(__file__)
VIDEO_PATH = os.path.abspath(os.path.join(_base_path, "video_teste.mp4"))
TEMPO_CPU = 300  # segundos
TEMPO_VIDEO = 300  # segundos
BATERIA_MINIMA = 90 # porcentagem mínima para iniciar o teste

# Inicializa pygame
pygame.init()
# seta pra rodar fullscreen na resolucao do monitor principal
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), display=0, flags=pygame.FULLSCREEN)
pygame.display.set_caption("Teste de Bateria Automático")
font = pygame.font.SysFont("Arial", 24)

# Mantém a janela principal sempre no topo (Windows)
if sys.platform == "win32":
    hwnd = pygame.display.get_wm_info()['window']
    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)

clock = pygame.time.Clock()

bat_log_cpu = []
time_log_cpu = []
bat_log_video = []
time_log_video = []
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


# worker implementation is in scripts/worker_cpu.py to keep child imports lightweight
def cpu_worker(stop_event):
    """Simple CPU-bound worker that runs until stop_event is set.
    Keep this module minimal so importing it in child processes doesn't run GUI code.
    """
    rng = range
    while not stop_event.is_set():
        # tight CPU-bound loop
        _ = sum(i * i for i in rng(30000))
        # small sleep can reduce wasteful busyspin if desired
        # time.sleep(0)


def grafico_final():
    import matplotlib.pyplot as plt

    # Obtém serial da máquina
    serial = None
    try:
        if platform.system() == "Windows":
            try:
                ps_cmd = ['powershell', '-NoLogo', '-NoProfile', '-Command',
                          "Get-CimInstance -ClassName Win32_Bios | Select-Object -ExpandProperty SerialNumber"]
                result = sp.check_output(ps_cmd, universal_newlines=True)
                serial = result.strip()
            except Exception:
                try:
                    result = sp.check_output(['wmic', 'bios', 'get', 'serialnumber'], universal_newlines=True)
                    lines = result.strip().split('\n')
                    if len(lines) > 1:
                        serial = lines[1].strip()
                except Exception:
                    serial = None
        else:
            try:
                result = sp.check_output(['cat', '/sys/class/dmi/id/product_serial'], universal_newlines=True)
                serial = result.strip()
            except Exception:
                serial = None
    except Exception:
        serial = None

    # Relatório e dados brutos
    relatorio_json = {}
    relatorio = [f"==== RESULTADOS DO TESTE - {serial} ====", ""]

    # === CPU 100% ===
    if len(bat_log_cpu) > 1:
        dbat_cpu = bat_log_cpu[0] - bat_log_cpu[-1]
        dt_cpu = time_log_cpu[-1] - time_log_cpu[0]
        rate_cpu = dbat_cpu / dt_cpu if dt_cpu > 0 else 0.0001
        consumo_cpu = dbat_cpu
        tempo_cpu = dt_cpu
        tempo_estimado_cpu = (bat_log_cpu[0]) / rate_cpu if rate_cpu > 0 else 0

        relatorio += [
            "--- 100% CPU ---",
            f"Consumo de bateria: {consumo_cpu:.2f}% em {tempo_cpu:.1f}s",
            f"Estimativa de duração: {tempo_estimado_cpu/3600:.2f} horas",
            ""
        ]
        relatorio_json["cpu_stress"] = {
            "consumo_bateria": consumo_cpu,
            "tempo": tempo_cpu,
            "estimativa_horas": tempo_estimado_cpu / 3600
        }

        # Gera gráfico da bateria (CPU)
        plt.figure()
        plt.plot(time_log_cpu, bat_log_cpu, color="red", linewidth=2)
        plt.title("Variação da Bateria - Teste CPU 100%")
        plt.xlabel("Tempo (s)")
        plt.ylabel("Nível da bateria (%)")
        plt.grid(True)
        plt.tight_layout()
        cpu_plot_path = os.path.join(os.getcwd(), f"grafico_cpu_{serial or 'semserial'}.png")
        plt.savefig(cpu_plot_path)
        plt.close()
        print(f"[INFO] Gráfico CPU salvo em {cpu_plot_path}")

    else:
        relatorio += ["--- 100% CPU ---", "Dados insuficientes.", ""]
        relatorio_json["cpu_stress"] = None

    # === Playback de Vídeo ===
    if len(bat_log_video) > 1:
        dbat_vid = bat_log_video[0] - bat_log_video[-1]
        dt_vid = time_log_video[-1] - time_log_video[0]
        rate_vid = dbat_vid / dt_vid if dt_vid > 0 else 0.0001
        consumo_vid = dbat_vid
        tempo_vid = dt_vid
        tempo_estimado_vid = (bat_log_video[0]) / rate_vid if rate_vid > 0 else 0
        cpu_media_video = sum(cpu_log_video_global) / len(cpu_log_video_global) if cpu_log_video_global else 0

        relatorio += [
            "--- Playback de Vídeo ---",
            f"Consumo de bateria: {consumo_vid:.2f}% em {tempo_vid:.1f}s",
            f"Estimativa de duração: {tempo_estimado_vid/3600:.2f} horas",
            f"Consumo médio de CPU no vídeo: {cpu_media_video:.1f}%"
        ]
        relatorio_json["video_playback"] = {
            "consumo_bateria": consumo_vid,
            "tempo": tempo_vid,
            "estimativa_horas": tempo_estimado_vid / 3600,
            "cpu_medio": cpu_media_video
        }

        # Gera gráfico da bateria (vídeo)
        plt.figure()
        plt.plot(time_log_video, bat_log_video, color="blue", linewidth=2)
        plt.title("Variação da Bateria - Playback de Vídeo")
        plt.xlabel("Tempo (s)")
        plt.ylabel("Nível da bateria (%)")
        plt.grid(True)
        plt.tight_layout()
        video_plot_path = os.path.join(os.getcwd(), f"grafico_video_{serial or 'semserial'}.png")
        plt.savefig(video_plot_path)
        plt.close()
        print(f"[INFO] Gráfico Vídeo salvo em {video_plot_path}")

    else:
        relatorio += ["--- Playback de Vídeo ---", "Dados insuficientes."]
        relatorio_json["video_playback"] = None

    # Adiciona serial ao JSON
    relatorio_json["serial"] = serial

    # Envia o relatório
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(API_URL, data=json.dumps(relatorio_json), headers=headers, timeout=5)
        print(f"[API] Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[API] Falha ao enviar relatório: {e}")

    # Mostra resultados no pygame
    screen.fill((0, 0, 0))
    y = 60
    for linha in relatorio:
        t = font.render(linha, True, (255, 255, 255))
        rect = t.get_rect(center=(WIDTH // 2, y))
        screen.blit(t, rect)
        y += 50
    pygame.display.flip()

    # Aguarda o usuário pressionar uma tecla
    esperando = True
    while esperando:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                esperando = False
            elif event.type == pygame.KEYDOWN:
                esperando = False
        time.sleep(0.1)


def cpu_stress():
    texto("Estágio 1: CPU a 100%", center=True)
    pygame.display.flip()
    end = time.time() + TEMPO_CPU
    last_bat_log = time.time()

    stop_event = multiprocessing.Event()
    num_cores = os.cpu_count() or 4

    # Cria um processo por núcleo
    workers = [
        multiprocessing.Process(target=cpu_worker, args=(stop_event,))
        for _ in range(num_cores)
    ]

    # Inicia todos
    for w in workers:
        w.start()

    print(f"[INFO] Estressando CPU com {num_cores} núcleos por {TEMPO_CPU} segundos...")

    # Loop de monitoramento e logging
    while time.time() < end:
        cpu_usage = psutil.cpu_percent(interval=1)
        bateria = get_bateria()

        # Loga tempo e nível de bateria
        bat_log_cpu.append(bateria if bateria is not None else 0)
        time_log_cpu.append(time.time() - start_time)

        # Atualiza tela
        legenda = f"CPU: {cpu_usage:.1f}%  |  Bateria: {bateria if bateria is not None else '-'}%"
        screen.fill((0, 0, 0))
        t = font.render(legenda, True, (255, 255, 0))
        screen.blit(t, (30, 30))
        t2 = font.render("Estágio 1: CPU a 100%", True, (255, 255, 255))
        screen.blit(t2, (30, 70))
        pygame.display.flip()

        # Checa eventos (permite sair com ESC ou fechar)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_event.set()
                for w in workers:
                    w.terminate()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                stop_event.set()
                for w in workers:
                    w.terminate()
                pygame.quit()
                sys.exit()

    # Finaliza os processos de stress
    stop_event.set()
    for w in workers:
        w.join(timeout=2)
        if w.is_alive():
            w.terminate()

    print("[INFO] Estresse de CPU finalizado.")


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

    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_history = [cpu_percent] * 10
    cpu_idx = 0
    cpu_update_interval = 0.2
    last_cpu_update = time.time()

    while time.time() - start_video < TEMPO_VIDEO:
        frame_start = time.time()
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(surf, (0, 0))

        now = time.time()
        if now - last_cpu_update > cpu_update_interval:
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_history[cpu_idx] = cpu_percent
            cpu_idx = (cpu_idx + 1) % len(cpu_history)
            last_cpu_update = now

        cpu_avg = sum(cpu_history) / len(cpu_history)
        cpu_log_video_global.append(cpu_avg)
        bateria = get_bateria()

        # ✅ Coleta de logs corrigida
        bat_log_video.append(bateria if bateria is not None else 0)
        time_log_video.append(time.time() - start_time)

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
    print(f"[DEBUG] Frames processados: {len(time_log_video)}  |  Logs de bateria: {len(bat_log_video)}")




def main():
    # Aguarda até que a bateria esteja acima de 90% e não esteja carregando
    while True:
        bateria = psutil.sensors_battery()
        if bateria is None:
            texto("Não foi possível obter informações da bateria.", center=True)
            pygame.display.flip()
            time.sleep(8)
            pygame.quit()
            sys.exit()
        if not bateria.power_plugged and bateria.percent > BATERIA_MINIMA:
            break
        msg = f"\n\n\n\n"
        screen.fill((0,0,0))
        # Separa o msg em avrios textos menores para caber na tela
        t = font.render("Aguardando requisitos:", True, (255,255,255))
        screen.blit(t, (30, 100))
        t2 = font.render(f"- Bateria acima de {BATERIA_MINIMA}%", True, (255,255,0))
        screen.blit(t2, (30, 150))
        t3 = font.render("- Não estar carregando", True, (255,255,0))
        screen.blit(t3, (30, 200))
        bateriaatual = f"Bateria atual: {bateria.percent:.1f}%"
        t4 = font.render(bateriaatual, True, (255, 255, 255))
        screen.blit(t4, (30, 300))

        pygame.display.flip()

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        time.sleep(5)

    cpu_stress()
    video_playback()
    texto("Teste concluído! Gerando gráfico...", center=True)
    pygame.display.flip()
    grafico_final()
    texto("Teste finalizado! Pressione qualquer tecla para sair.", center=True)
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Necessário para PyInstaller no Windows
    main()

