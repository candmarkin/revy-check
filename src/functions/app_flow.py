import sys

import pygame

from src import api_client, app_state
from src.functions.system_info import draw_system_info

def start_step():
    waiting = True
    selected_option = None

    options = [
        "QUALIDADE1",
        "QUALIDADE2",
        "VISTORIA1",
        "VISTORIA2",
        "VISTORIA3",
        "VISTORIA4",
    ]

    button_rects = []
    start_y = app_state.HEIGHT // 2 - len(options) * 50 // 2
    for i, opt in enumerate(options):
        rect = pygame.Rect(app_state.WIDTH // 2 - 150, start_y + i * 80, 300, 60)
        button_rects.append((opt, rect))

    while waiting:
        app_state.SCREEN.fill((30, 30, 30))
        draw_system_info(app_state.SYSTEM_INFO)

        title = app_state.FONT.render("Selecione o tipo de teste", True, (255, 255, 255))
        app_state.SCREEN.blit(title, (app_state.WIDTH // 2 - title.get_width() // 2, app_state.HEIGHT // 4))

        mouse_pos = pygame.mouse.get_pos()
        for opt, rect in button_rects:
            color = (0, 200, 0) if rect.collidepoint(mouse_pos) else (0, 150, 0)
            pygame.draw.rect(app_state.SCREEN, color, rect, border_radius=12)
            text = app_state.FONT.render(opt, True, (255, 255, 255))
            app_state.SCREEN.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for opt, rect in button_rects:
                    if rect.collidepoint(event.pos):
                        selected_option = opt
                        app_state.add_log({
                            "step": f"TEST_START_{selected_option.upper().replace(' ', '_')}",
                            "time": app_state.now_iso(),
                            "result": "APROVADO",
                        })
                        waiting = False

        app_state.CLOCK.tick(30)


def wait_for_db_connection():
    """Espera a API responder antes de comecar o fluxo.

    Antes isto abria conexao MySQL direto com credencial no codigo. Agora so'
    confirma que /revy-check responde e aceita a chave -- se a bancada estiver
    sem rede, a tela pisca ate' o cabo voltar.
    """
    if api_client.disponivel():
        return

    rgb_val = 0
    while not api_client.disponivel():
        app_state.SCREEN.fill((rgb_val, rgb_val, rgb_val))
        text = app_state.FONT.render(
            "Conecte-se a rede corporativa (Desconecte e reconecte o cabo)",
            True, (255, 255, 255),
        )
        app_state.SCREEN.blit(
            text,
            ((app_state.WIDTH - text.get_width()) // 2,
             (app_state.HEIGHT - text.get_height()) // 2),
        )
        pygame.display.flip()
        # O `rgb_val` antes era zerado dentro do laco, entao o fundo nunca
        # mudava de cor e a tela parecia congelada.
        rgb_val = (rgb_val + 5) % 256
        app_state.CLOCK.tick(30)


def prompt_password():
    input_text = ""
    active = True
    while active:
        app_state.SCREEN.fill((50, 50, 50))
        prompt = app_state.FONT.render("Digite senha DEV:", True, (255, 255, 0))
        app_state.SCREEN.blit(prompt, (50, 200))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT and app_state.MODE == "DEV":
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
    return input_text