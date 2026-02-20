"""
Funções de teste de tela
"""
import pygame
from datetime import datetime


def screen_step(screen, width, height, clock, draw_text_func, add_log_func, draw_system_info_func, get_system_info_func):
    """
    Executa o teste de tela exibindo cores RGB
    
    Returns:
        bool: True se aprovado
    """
    colors = [
        ((255, 0, 0), "Vermelho"),
        ((0, 255, 0), "Verde"),
        ((0, 0, 255), "Azul")
    ]
    
    color_idx = 0
    running = True
    system_info = get_system_info_func()
    
    while running and color_idx < len(colors):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    color_idx += 1

        if color_idx < len(colors):
            color, name = colors[color_idx]
            screen.fill(color)
            
            # Desenhar informações do sistema
            draw_system_info_func(system_info)
            
            text = pygame.font.SysFont("Arial", 40).render(
                f"Pressione ENTER para próxima cor ({name})",
                True, (255, 255, 255) if color != (255, 255, 255) else (0, 0, 0)
            )
            text_rect = text.get_rect(center=(width // 2, height // 2))
            screen.blit(text, text_rect)
            
            pygame.display.flip()
            clock.tick(60)

    draw_text_func(["✅ Teste de tela concluído!"], (0, 255, 0))
    add_log_func({"step": "SCREEN_TEST", "time": str(datetime.now()), "result": "APROVADO"})
    return True
