import pygame

from src import app_state, hal


def get_system_info():
    """Informações do sistema: serial, CPU, RAM, disco, IP."""
    return hal.system_info()


def draw_system_info(system_info):
    """Desenha informações do sistema no canto superior esquerdo."""
    if app_state.SCREEN is None:
        return

    info_font = pygame.font.SysFont("Consolas", 20)
    y = 10
    lines = [
        f"SERIAL: {system_info.get('serial', 'N/A')}",
        f"CPU: {system_info.get('cpu', 'N/A')}",
        f"RAM: {system_info.get('ram', 'N/A')}",
        f"DISK: {system_info.get('disk', 'N/A')}",
        f"IP: {system_info.get('ip', 'N/A')}",
    ]

    for line in lines:
        text_surf = info_font.render(line, True, (255, 255, 0))
        app_state.SCREEN.blit(text_surf, (10, y))
        y += 18
