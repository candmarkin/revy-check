import subprocess

import pygame

from src import app_state


def get_system_info():
    """Obtém informações do sistema: serial, CPU, RAM, disco."""
    info = {}

    try:
        info["serial"] = subprocess.check_output(
            "cat /sys/class/dmi/id/product_serial", shell=True
        ).strip().decode("utf-8")
    except Exception:
        info["serial"] = "N/A"

    try:
        cpu_info = subprocess.check_output(
            "cat /proc/cpuinfo | grep 'model name' | head -1", shell=True
        ).decode("utf-8")
        info["cpu"] = cpu_info.split(":")[1].strip() if ":" in cpu_info else "N/A"
    except Exception:
        info["cpu"] = "N/A"

    try:
        mem_info = subprocess.check_output(
            "cat /proc/meminfo | grep MemTotal", shell=True
        ).decode("utf-8")
        mem_kb = int(mem_info.split()[1])
        mem_gb = round(mem_kb / (1024 ** 2), 1)
        info["ram"] = f"{mem_gb} GB"
    except Exception:
        info["ram"] = "N/A"

    try:
        disk_info = subprocess.check_output(
            "df -h / | tail -1", shell=True
        ).decode("utf-8").split()
        if len(disk_info) >= 2:
            info["disk"] = disk_info[1]
        else:
            info["disk"] = "N/A"
    except Exception:
        info["disk"] = "N/A"

    return info


def draw_system_info(system_info):
    """Desenha informações do sistema no canto superior esquerdo."""
    if app_state.SCREEN is None:
        return

    info_font = pygame.font.SysFont("Consolas", 14)
    y = 10
    lines = [
        f"SERIAL: {system_info.get('serial', 'N/A')}",
        f"CPU: {system_info.get('cpu', 'N/A')}",
        f"RAM: {system_info.get('ram', 'N/A')}",
        f"DISK: {system_info.get('disk', 'N/A')}",
    ]

    for line in lines:
        text_surf = info_font.render(line, True, (255, 255, 0))
        app_state.SCREEN.blit(text_surf, (10, y))
        y += 18
