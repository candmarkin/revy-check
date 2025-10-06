import pygame


def draw_text(lines, color=(255, 255, 255)):

    from ..main import SCREEN, WIDTH, HEIGHT, FONT

    SCREEN.fill((0, 0, 0))
    y = HEIGHT // 3
    for text in lines:
        rendered = FONT.render(text, True, color)
        rect = rendered.get_rect(center=(WIDTH // 2, y))
        SCREEN.blit(rendered, rect)
        y += 50
    pygame.display.flip()