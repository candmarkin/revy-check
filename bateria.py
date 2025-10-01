import pygame
import multiprocessing as mp
import math
import time
import sys
import io

import psutil
import numpy as np
import matplotlib.pyplot as plt


# ---------- STRESS FUNCTION ----------
def cpu_worker(target_usage=0.5, cycle_time=0.1):
    """
    target_usage = fração de uso (0.0 a 1.0)
    cycle_time   = duração de cada ciclo em segundos
    """
    work_time = target_usage * cycle_time
    sleep_time = cycle_time - work_time

    x = 0.0001
    while True:
        start = time.time()
        # Trabalhar até work_time
        while (time.time() - start) < work_time:
            x = x + math.sin(x) * math.cos(x) + 0.0000001

        if sleep_time > 0:
            time.sleep(sleep_time)


# ---------- BATTERY INFO ----------
def get_battery_info():
    bat = psutil.sensors_battery()
    if bat is None:
        return None, None
    return bat.percent, bat.power_plugged


# ---------- GRAPH GENERATION + ESTIMATIVA ----------
def generate_graph(times, percents):
    # fundo igual ao pygame: (30,30,30) → convertido para 0-1
    bg_color = (30/255, 30/255, 30/255)

    fig, ax = plt.subplots(figsize=(8, 4), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    ax.plot(times, percents, marker="o", linestyle="-", color="deepskyblue", label="Bateria (%)")
    ax.set_xlabel("Tempo (s)", color="white")
    ax.set_ylabel("Bateria (%)", color="white")
    ax.set_title("Descarga da bateria", color="white")

    # cores dos ticks e da grade
    ax.tick_params(colors="white")
    ax.grid(True, color="gray", alpha=0.3)
    ax.legend(facecolor=bg_color, edgecolor="white", labelcolor="white")

    est_minutes = None
    if len(times) >= 2:
        x = np.array(times) / 60.0
        y = np.array(percents)

        if np.ptp(y) > 0.1 and np.ptp(x) > 0:
            try:
                m, b = np.polyfit(x, y, 1)
                if m < 0:
                    x_pred = np.linspace(x[0], x[-1] + 30, 200)
                    y_pred = m * x_pred + b
                    ax.plot(x_pred * 60.0, y_pred, "--", color="orange", label="Projeção")

                    est_time = -b / m
                    est_minutes = est_time - x[-1]
                    if est_minutes > 0:
                        ax.axvline(
                            est_time * 60.0, color="red", linestyle=":", 
                            label=f"Fim ~ {int(est_minutes)} min"
                        )
            except Exception as e:
                print("⚠️ Erro no polyfit:", e)

    buf = io.BytesIO()
    plt.savefig(buf, format="PNG", facecolor=bg_color)  # garante cor no export
    plt.close(fig)
    buf.seek(0)
    return pygame.image.load(buf), est_minutes


def main():
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT), display=0)
    pygame.display.set_caption("Stress CPU + Gráfico Bateria")

    font = pygame.font.SysFont("Arial", 28)

    workers = mp.cpu_count()
    procs = []  # só vamos iniciar quando for hora do teste

    clock = pygame.time.Clock()
    t0 = None
    times, percents = [], []
    graph_surface = None
    update_interval = 2  # segundos

    estimativas = []  # histórico de estimativas (minutos)
    status_msg = "Desconecte o carregador para iniciar o teste"
    statuscolor= (0, 255, 255)

    teste_iniciado = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                running = False

        percent, plugged = get_battery_info()
        elapsed = 0 if t0 is None else time.time() - t0

        if not teste_iniciado:
            elapsed = 0
            if percent is not None and percent < 95:
                status_msg = "Carregue a bateria até 95%..."
                statuscolor = (0, 255, 255)
            elif percent is not None and percent >= 95 and plugged:
                status_msg = "Desconecte o carregador para iniciar o teste"
                statuscolor = (0, 255, 255)
            elif percent is not None and percent >= 95 and not plugged:
                # ✅ iniciar teste aqui
                status_msg = "Teste iniciado!"
                statuscolor = (255, 255, 255)
                t0 = time.time()
                times, percents = [], []
                estimativas = []
                # iniciar stress da CPU
                procs = [mp.Process(target=cpu_worker, args=(0.5,), daemon=True) for _ in range(workers)]
                for p in procs:
                    p.start()
                teste_iniciado = True
        else:
            # teste em andamento
            if percent is not None:
                times.append(int(elapsed))
                percents.append(percent)

            if len(times) > 1 and int(elapsed) % update_interval == 0:
                status_msg = "Coletando dados..."
                statuscolor = (255, 255, 255)
                graph_surface, est_minutes = generate_graph(times, percents)
                if est_minutes is not None:
                    estimativas.append(est_minutes)
                    if len(estimativas) > 5:
                        estimativas = estimativas[-5:]
                        if max(estimativas) - min(estimativas) < (0.05 * np.mean(estimativas)):
                            if np.mean(estimativas) >= 60:
                                status_msg = f"✅ Aprovado! Estimativa: {np.mean(estimativas):.1f} min"
                                statuscolor = (250, 255, 0)
                            else:
                                status_msg = f"❌ Reprovado! Estimativa: {np.mean(estimativas):.1f} min"
                                statuscolor = (255, 0, 0)
                        else:
                            status_msg = f"Estimando... {est_minutes:.1f} min"

        # desenhar tela
        screen.fill((30, 30, 30))
        text1 = font.render(f"Tempo percorrido: {int(elapsed)}s", True, (255, 255, 255))
        text2 = font.render(f"Bateria: {percent if percent else 'N/A'}%", True, (255, 255, 255))
        text3 = font.render(f"{'Conectado' if plugged else 'Na bateria'}", True, (255, 255, 255))
        text4 = font.render(status_msg, True, statuscolor)

        screen.blit(text1, (20, 20))
        screen.blit(text2, (20, 60))
        screen.blit(text3, (20, 100))

        rectstatus = text4.get_rect(center=(WIDTH // 2, 160))
        screen.blit(text4, rectstatus)

        if graph_surface:
            rect = graph_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen.blit(graph_surface, rect)

        pygame.display.flip()
        clock.tick(1)

    for p in procs:
        p.terminate()
    pygame.quit()


if __name__ == "__main__":
    main()
