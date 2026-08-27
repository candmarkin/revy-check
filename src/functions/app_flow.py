import sys

import pygame

from src import api_client, app_state, config
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

    Roda antes do login: nao exige sessao, so' um sinal de vida da API. Se a
    bancada estiver sem rede, a tela pisca ate' o cabo voltar.

    Mostra a URL que esta' tentando: quando o problema e' `revycheck.env`
    apontando para o lugar errado, "conecte o cabo" manda o tecnico procurar
    defeito onde nao tem.
    """
    if api_client.disponivel():
        return

    rgb_val = 0
    fonte_url = pygame.font.SysFont("Arial", 16)
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
        alvo = fonte_url.render(f"tentando {config.api_url()}", True, (170, 170, 170))
        app_state.SCREEN.blit(
            alvo,
            ((app_state.WIDTH - alvo.get_width()) // 2,
             (app_state.HEIGHT - text.get_height()) // 2 + 50),
        )
        pygame.display.flip()
        # O `rgb_val` antes era zerado dentro do laco, entao o fundo nunca
        # mudava de cor e a tela parecia congelada.
        rgb_val = (rgb_val + 5) % 256
        app_state.CLOCK.tick(30)