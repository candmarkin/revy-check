import pygame

from src import app_state
from src.functions.system_info import draw_system_info


def draw_text(lines, color=(255, 255, 255)):
    if app_state.SCREEN is None:
        return

    app_state.SCREEN.fill((0, 0, 0))

    # Informacoes do sistema
    draw_system_info(app_state.SYSTEM_INFO)

    y = app_state.HEIGHT // 3
    for text in lines:
        rendered = app_state.FONT.render(text, True, color)
        rect = rendered.get_rect(center=(app_state.WIDTH // 2, y))
        app_state.SCREEN.blit(rendered, rect)
        y += 50
    pygame.display.flip()
