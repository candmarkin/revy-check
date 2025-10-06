import pygame
import sys
from functions.save_log import save_log
from main import SCREEN, CLOCK, MODE, log_data, draw_text
from datetime import datetime


def screen_step():
    colors = [
        (0, 0, 0),       # PRETO
        (255, 255, 255), # BRANCO
        (255, 0, 0),     # VERMELHO
        (0, 255, 0),     # VERDE
        (0, 0, 255),     # AZUL
        (255, 255, 0),   # AMARELO
    ]
    global MODE
    color_index = 0

    running = True
    test_done = False
    approved = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE == "DEV":
                    save_log(log_data)
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.KEYDOWN:
                if not test_done:
                    if event.key == pygame.K_RETURN:
                        color_index = (color_index + 1) % len(colors)
                    elif event.key == pygame.K_SPACE:
                        SCREEN.fill((0, 0, 0))
                        draw_text(["Teste concluído!",
                                   "Aperte Y para APROVAR",
                                   "ou N para REPROVAR"], (0, 255, 0))
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
            SCREEN.fill(colors[color_index])
            pygame.display.flip()

        CLOCK.tick(60)

    # Grava resultado no log
    result = "APROVADO" if approved else "REPROVADO"
    log_data.append({"step": "SCREEN_TEST", "time": str(datetime.now()), "result": result})
    save_log(log_data)
