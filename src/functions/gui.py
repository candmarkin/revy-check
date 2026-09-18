import sys

import pygame

from src import app_state
from src.functions.system_info import draw_system_info


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
    pygame.display.flip()


def reproved_lock_screen():
    """Tela terminal de reprovacao; devolve True quando o operador pede para
    recomecar os testes.

    Nao chama save_log de proposito: quando a qualidade do GAT nao permite
    reprovacao, o relatorio nao e' gerado nem enviado.
    """
    font_title = pygame.font.SysFont("Arial", 40, bold=True)
    font_body = pygame.font.SysFont("Arial", 20)
    reproved = [e.get("step", "?") for e in app_state.LOG_DATA if e.get("result") == "REPROVADO"]
    restart_btn = pygame.Rect(app_state.WIDTH // 2 - 180, app_state.HEIGHT - 120, 360, 60)

    lines = [
        f"Qualidade no GAT: {app_state.GAT_QUALITY or 'não informada'}",
        "Esta qualidade não permite concluir o checklist com teste reprovado.",
        "O relatório NÃO foi gerado nem enviado.",
        "",
        "Reprovado em: " + (", ".join(reproved[:8]) if reproved else "-"),
    ]

    while True:
        app_state.SCREEN.fill((90, 0, 0))
        draw_system_info(app_state.SYSTEM_INFO)

        title = font_title.render("PRODUTO REPROVADO", True, (255, 255, 255))
        app_state.SCREEN.blit(title, title.get_rect(center=(app_state.WIDTH // 2, app_state.HEIGHT // 4)))

        y = app_state.HEIGHT // 4 + 70
        for line in lines:
            rendered = font_body.render(line, True, (255, 230, 230))
            app_state.SCREEN.blit(rendered, rendered.get_rect(center=(app_state.WIDTH // 2, y)))
            y += 34

        pygame.draw.rect(app_state.SCREEN, (240, 240, 240), restart_btn, border_radius=10)
        pygame.draw.rect(app_state.SCREEN, (0, 0, 0), restart_btn, 2, border_radius=10)
        label = font_body.render("Recomeçar os testes", True, (0, 0, 0))
        app_state.SCREEN.blit(label, label.get_rect(center=restart_btn.center))
        pygame.display.flip()

        for event in pygame.event.get():
            # Sem atalho de teclado: uma tecla morta ou presa - justamente o
            # defeito que o teste procura - reiniciaria a bancada sozinha.
            if event.type == pygame.QUIT and app_state.MODE == "DEV":
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and restart_btn.collidepoint(event.pos):
                return True

        app_state.CLOCK.tick(30)
