import pygame
import time
import sys
from datetime import datetime


def draw_text(lines, color=(255, 255, 255)):
    """Desenha texto centralizado na tela seguindo o padrão do main.py"""
    try:
        from src.alltests import SCREEN, WIDTH, HEIGHT, FONT
    except ImportError:
        # Para quando é importado como módulo
        from ..alltests import SCREEN, WIDTH, HEIGHT, FONT
    
    SCREEN.fill((0, 0, 0))
    y = HEIGHT // 3
    for text in lines:
        rendered = FONT.render(text, True, color)
        rect = rendered.get_rect(center=(WIDTH // 2, y))
        SCREEN.blit(rendered, rect)
        y += 50
    pygame.display.flip()


def touchpad_step():
    """
    Testa o touchpad/mouse seguindo o padrão de UI do main.py
    - Arraste para a esquerda
    - Clique com o botão esquerdo
    - Clique com o botão do meio
    - Arraste para a direita  
    - Clique com o botão direito
    - Use o scroll para cima e para baixo
    """
    try:
        from src.alltests import SCREEN, WIDTH, HEIGHT, FONT, CLOCK
    except ImportError:
        from ..alltests import SCREEN, WIDTH, HEIGHT, FONT, CLOCK
    
    
    # Estados do teste
    state = "DRAG_LEFT"
    start_pos = None
    scroll_count = 0
    
    # Log de testes realizados
    log_data = []
    
    while True:
        SCREEN.fill((0, 0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return log_data
            
            # Detecção de movimento do mouse
            elif event.type == pygame.MOUSEMOTION:
                if start_pos is None:
                    start_pos = event.pos
                else:
                    dx = event.pos[0] - start_pos[0]
                    
                    # Arrasto para a esquerda
                    if state == "DRAG_LEFT" and dx < -100:
                        log_data.append({"step": "TOUCHPAD_DRAG_LEFT", "time": str(datetime.now())})
                        state = "CLICK_LEFT"
                        start_pos = None
                        time.sleep(0.3)
                    
                    # Arrasto para a direita
                    elif state == "DRAG_RIGHT" and dx > 100:
                        log_data.append({"step": "TOUCHPAD_DRAG_RIGHT", "time": str(datetime.now())})
                        state = "CLICK_RIGHT"
                        start_pos = None
                        time.sleep(0.3)
            
            # Cliques do mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Botão esquerdo
                if event.button == 1 and state == "CLICK_LEFT":
                    log_data.append({"step": "TOUCHPAD_LEFT_CLICK", "time": str(datetime.now())})
                    state = "CLICK_MIDDLE"
                    time.sleep(0.3)
                
                # Botão do meio
                elif event.button == 2 and state == "CLICK_MIDDLE":
                    log_data.append({"step": "TOUCHPAD_MIDDLE_CLICK", "time": str(datetime.now())})
                    state = "DRAG_RIGHT"
                    time.sleep(0.3)
                
                # Botão direito
                elif event.button == 3 and state == "CLICK_RIGHT":
                    log_data.append({"step": "TOUCHPAD_RIGHT_CLICK", "time": str(datetime.now())})
                    state = "SCROLL"
                    time.sleep(0.3)
                
                # Scroll para cima
                elif event.button == 4 and state == "SCROLL":
                    scroll_count += 1
                    if scroll_count == 1:
                        log_data.append({"step": "TOUCHPAD_SCROLL_UP", "time": str(datetime.now())})
                    elif scroll_count >= 2:
                        state = "SCROLL_DOWN"
                        scroll_count = 0
                
                # Scroll para baixo
                elif event.button == 5 and state == "SCROLL_DOWN":
                    scroll_count += 1
                    if scroll_count == 1:
                        log_data.append({"step": "TOUCHPAD_SCROLL_DOWN", "time": str(datetime.now())})
                    elif scroll_count >= 2:
                        state = "DONE"
        
        # Exibir instruções baseadas no estado atual
        if state == "DRAG_LEFT":
            draw_text(["👉 Arraste o mouse para a ESQUERDA (>100px)"])
        
        elif state == "CLICK_LEFT":
            draw_text(["👉 Clique com o BOTÃO ESQUERDO do mouse"], (0, 255, 0))
        
        elif state == "CLICK_MIDDLE":
            draw_text(["👉 Clique com o BOTÃO DO MEIO do mouse"], (255, 255, 0))
        
        elif state == "DRAG_RIGHT":
            draw_text(["👉 Arraste o mouse para a DIREITA (>100px)"])
        
        elif state == "CLICK_RIGHT":
            draw_text(["👉 Clique com o BOTÃO DIREITO do mouse"], (255, 100, 100))
        
        elif state == "SCROLL":
            draw_text([f"👉 Role o scroll PARA CIMA (2x)", f"Rolagens: {scroll_count}/2"], (100, 200, 255))
        
        elif state == "SCROLL_DOWN":
            draw_text([f"👉 Role o scroll PARA BAIXO (2x)", f"Rolagens: {scroll_count}/2"], (100, 200, 255))
        
        elif state == "DONE":
            draw_text(["✅ Teste de touchpad concluído!", "Pressione ESC para continuar"], (0, 255, 0))
        
        CLOCK.tick(10)



if __name__ == "__main__":
    import sys
    import os
    
    # Adiciona o diretório raiz ao path para permitir imports absolutos
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    sys.path.insert(0, root_dir)
    
    # Simular ambiente do alltests.py para teste standalone
    pygame.init()
    WIDTH, HEIGHT = 1920, 1080
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Teste de Touchpad")
    FONT = pygame.font.SysFont("Arial", 20)
    CLOCK = pygame.time.Clock()
    
    # Criar módulo temporário para simular alltests
    import types
    alltests_module = types.ModuleType('alltests')
    alltests_module.SCREEN = SCREEN
    alltests_module.WIDTH = WIDTH
    alltests_module.HEIGHT = HEIGHT
    alltests_module.FONT = FONT
    alltests_module.CLOCK = CLOCK
    sys.modules['src.alltests'] = alltests_module
    
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

