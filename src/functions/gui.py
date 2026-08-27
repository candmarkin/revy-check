import sys

import pygame

from src import app_state
from src.functions.system_info import draw_system_info
from src.functions import dev_mode


def ask_operator(lines, options, color=(255, 255, 255)):
    """Mostra `lines` e espera o operador decidir.

    `options` mapeia tecla do pygame -> (rotulo, valor devolvido). Ao contrario
    de um `while True` que so' faz polling de hardware, isso bombeia os eventos,
    entao a tela continua respondendo enquanto espera.
    """
    legend = "   ".join(f"[{label}]" for label, _ in options.values())

    while True:
        draw_text(list(lines) + ["", legend], color)

        for event in pygame.event.get():
            dev_mode.handle(event)
            if event.type == pygame.QUIT and app_state.MODE == "DEV":
                # Importado aqui porque save_log importa este modulo.
                from src.functions.save_log import save_log

                save_log()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key in options:
                return options[event.key][1]

        app_state.CLOCK.tick(30)


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

    # Os passos que desenham a propria tela (USB, video, ethernet, audio)
    # passam por aqui; sem isto a legenda dos atalhos de DEV so' apareceria
    # entre um passo e outro. As telas que pintam a tela inteira de proposito
    # (teste de cor, teclado, touchpad, camera) ficam de fora justamente para
    # nao sujarem o que esta' sendo avaliado.
    dev_mode.draw_legend()
    # Resultado da ultima tentativa de destravar o DEV, inclusive negada. Fora
    # da legenda porque tem de aparecer em PROD tambem.
    dev_mode.draw_aviso()
    pygame.display.flip()
