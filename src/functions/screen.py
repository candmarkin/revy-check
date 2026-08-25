import sys
import time
from datetime import datetime

import pygame

from src import app_state
from src.functions.gui import draw_text
from src.functions.save_log import save_log
from src.functions.system_info import draw_system_info
from src.functions import dev_mode


def screen_step():
    colors = [
        (0, 0, 0),
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
    ]

    color_index = 0
    running = True
    test_done = False
    approved = None

    legend_font = pygame.font.SysFont("Arial", 18)
    legend_text = "Pressione ENTER para alternar cores e ESPAÇO para finalizar o teste"

    while running:
        for event in pygame.event.get():
            dev_mode.handle(event)
            if event.type == pygame.QUIT:
                if app_state.MODE == "DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.KEYDOWN:
                if not test_done:
                    if event.key == pygame.K_RETURN:
                        color_index = (color_index + 1) % len(colors)
                    elif event.key == pygame.K_SPACE:
                        app_state.SCREEN.fill((0, 0, 0))
                        draw_text(["Teste concluído!", "Aperte Y para APROVAR", "ou N para REPROVAR"], (0, 255, 0))
                        pygame.display.flip()
                        test_done = True
                else:
                    if event.key == pygame.K_y:
                        approved = True
                        running = False
                    elif event.key == pygame.K_n:
                        approved = False
                        running = False

        if not test_done:
            app_state.SCREEN.fill(colors[color_index])
            draw_system_info(app_state.SYSTEM_INFO)
            legend_surface = legend_font.render(legend_text, True, (255, 255, 255))
            legend_rect = legend_surface.get_rect()
            legend_rect.topright = (app_state.WIDTH - 30, 20)
            app_state.SCREEN.blit(legend_surface, legend_rect)
            pygame.display.flip()

        app_state.CLOCK.tick(60)

    result = "APROVADO" if approved else "REPROVADO"
    app_state.add_log({"step": "SCREEN_TEST", "time": str(datetime.now()), "result": result})
