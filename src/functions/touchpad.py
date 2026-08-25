import pygame
import time
import sys
from datetime import datetime

from src import app_state
from src.functions import dev_mode


def draw_text(lines, color=(255, 255, 255)):
    """Desenha texto centralizado na tela seguindo o padrão do main.py"""
    if app_state.SCREEN is None:
        return

    app_state.SCREEN.fill((0, 0, 0))
    y = app_state.HEIGHT // 3
    for text in lines:
        rendered = app_state.FONT.render(text, True, color)
        rect = rendered.get_rect(center=(app_state.WIDTH // 2, y))
        app_state.SCREEN.blit(rendered, rect)
        y += 50
    pygame.display.flip()


def touchpad_step():
    """
    Testa o touchpad/mouse em uma tela unica:
    - Arraste ate a caixa da esquerda e clique com o botao esquerdo
    - Arraste ate a caixa da direita e clique com o botao direito
    - Botao do meio (opcional)
    - Scroll para cima e para baixo
    """
    SCREEN = app_state.SCREEN
    WIDTH = app_state.WIDTH
    HEIGHT = app_state.HEIGHT
    FONT = app_state.FONT
    CLOCK = app_state.CLOCK
    
    
    drag_start = None
    scroll_up_count = 0
    scroll_down_count = 0

    # Log de testes realizados
    log_data = []

    completed = {
        "drag_left": False,
        "left_click": False,
        "drag_right": False,
        "right_click": False,
        "scroll_up": False,
        "scroll_down": False,
        "middle_click": False,
    }

    required_steps = [
        "drag_left",
        "left_click",
        "drag_right",
        "right_click",
        "scroll_up",
        "scroll_down",
    ]

    # Layout responsivo
    def clamp(value, min_value, max_value):
        return max(min_value, min(value, max_value))

    box_w = clamp(WIDTH // 3, 200, 420)
    box_h = clamp(HEIGHT // 4, 120, 260)
    box_y = HEIGHT // 2 - box_h // 2
    left_rect = pygame.Rect(WIDTH // 4 - box_w // 2, box_y, box_w, box_h)
    right_rect = pygame.Rect(WIDTH * 3 // 4 - box_w // 2, box_y, box_w, box_h)

    def mark_done(key, log_step):
        if not completed[key]:
            completed[key] = True
            log_data.append({"step": log_step, "time": str(datetime.now())})

    def all_required_done():
        return all(completed[key] for key in required_steps)

    def draw_ui():
        SCREEN.fill((0, 0, 0))

        # Titulos
        title = FONT.render("Teste de Touchpad", True, (255, 255, 255))
        SCREEN.blit(title, title.get_rect(center=(WIDTH // 2, clamp(HEIGHT // 8, 60, 140))))

        # Caixa esquerda (botao esquerdo)
        left_color = (0, 200, 0) if completed["drag_left"] and completed["left_click"] else (100, 100, 100)
        pygame.draw.rect(SCREEN, left_color, left_rect, 3)
        left_label = FONT.render("Clique ESQUERDO", True, (255, 255, 255))
        SCREEN.blit(left_label, left_label.get_rect(center=left_rect.center))

        # Caixa direita (botao direito)
        right_color = (0, 200, 0) if completed["drag_right"] and completed["right_click"] else (100, 100, 100)
        pygame.draw.rect(SCREEN, right_color, right_rect, 3)
        right_label = FONT.render("Clique DIREITO", True, (255, 255, 255))
        SCREEN.blit(right_label, right_label.get_rect(center=right_rect.center))

        # Checklist
        items = [
            ("Arraste ate a caixa da esquerda", completed["drag_left"], False),
            ("Clique ESQUERDO na caixa", completed["left_click"], False),
            ("Arraste ate a caixa da direita", completed["drag_right"], False),
            ("Clique DIREITO na caixa", completed["right_click"], False),
            (f"Scroll PARA CIMA (2x) {scroll_up_count}/2", completed["scroll_up"], False),
            (f"Scroll PARA BAIXO (2x) {scroll_down_count}/2", completed["scroll_down"], False),
            ("Botao do meio", completed["middle_click"], True),
        ]

        y = clamp(HEIGHT // 3, 180, HEIGHT // 2)
        for text, done, optional in items:
            prefix = "[OK] " if done else "[ ] "
            suffix = " (opcional)" if optional else ""
            color = (0, 255, 0) if done else (200, 200, 200)
            rendered = FONT.render(prefix + text + suffix, True, color)
            SCREEN.blit(rendered, rendered.get_rect(center=(WIDTH // 2, y)))
            y += clamp(HEIGHT // 30, 22, 36)

        # Aprovacao/Reprovacao
        approve_enabled = all_required_done()
        status_text = "Y = aprovar, N = reprovar" if approve_enabled else "Complete os passos obrigatorios"
        status_color = (0, 200, 0) if approve_enabled else (200, 200, 200)
        status_render = FONT.render(status_text, True, status_color)
        SCREEN.blit(status_render, status_render.get_rect(center=(WIDTH // 2, HEIGHT * 5 // 6)))

        pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            dev_mode.handle(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return log_data

                if event.key == pygame.K_y and all_required_done():
                    log_data.append({"step": "TOUCHPAD_APPROVED", "time": str(datetime.now())})
                    return log_data

                if event.key == pygame.K_n:
                    log_data.append({"step": "TOUCHPAD_REPROVED", "time": str(datetime.now())})
                    return log_data
            
            # Detecção de movimento do mouse
            elif event.type == pygame.MOUSEMOTION:
                if drag_start is None:
                    drag_start = event.pos
                else:
                    dx = event.pos[0] - drag_start[0]
                    dy = event.pos[1] - drag_start[1]
                    drag_distance = (dx * dx + dy * dy) ** 0.5

                    if drag_distance >= 100 and left_rect.collidepoint(event.pos):
                        mark_done("drag_left", "TOUCHPAD_DRAG_TO_LEFT_BOX")
                        drag_start = None

                    elif drag_distance >= 100 and right_rect.collidepoint(event.pos):
                        mark_done("drag_right", "TOUCHPAD_DRAG_TO_RIGHT_BOX")
                        drag_start = None
            
            # Cliques do mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Botao esquerdo
                if event.button == 1 and left_rect.collidepoint(event.pos):
                    mark_done("left_click", "TOUCHPAD_LEFT_CLICK")

                # Botao direito
                elif event.button == 3 and right_rect.collidepoint(event.pos):
                    mark_done("right_click", "TOUCHPAD_RIGHT_CLICK")

                # Botao do meio (opcional)
                elif event.button == 2:
                    mark_done("middle_click", "TOUCHPAD_MIDDLE_CLICK")

                # Scroll para cima
                elif event.button == 4:
                    if not completed["scroll_up"]:
                        scroll_up_count += 1
                        if scroll_up_count >= 2:
                            mark_done("scroll_up", "TOUCHPAD_SCROLL_UP")

                # Scroll para baixo
                elif event.button == 5:
                    if not completed["scroll_down"]:
                        scroll_down_count += 1
                        if scroll_down_count >= 2:
                            mark_done("scroll_down", "TOUCHPAD_SCROLL_DOWN")

        draw_ui()
        CLOCK.tick(10)



if __name__ == "__main__":
    import sys
    import os
    
    # Adiciona o diretório raiz ao path para permitir imports absolutos
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    sys.path.insert(0, root_dir)
    
    # Simular ambiente de app_state para teste standalone
    pygame.init()
    app_state.WIDTH, app_state.HEIGHT = 1920, 1080
    app_state.SCREEN = pygame.display.set_mode((app_state.WIDTH, app_state.HEIGHT))
    pygame.display.set_caption("Teste de Touchpad")
    app_state.FONT = pygame.font.SysFont("Arial", 20)
    app_state.CLOCK = pygame.time.Clock()
    
    print("Iniciando teste de touchpad...")
    results = touchpad_step()
    
    print("\n" + "="*50)
    print("RESULTADOS DO TESTE DE TOUCHPAD")
    print("="*50)
    
    for log in results:
        print(f"{log['step']}: {log['time']}")
    
    print("="*50)
    print(f"\n✓ {len(results)} testes concluídos com sucesso!")
    
    pygame.quit()
    sys.exit(0)

