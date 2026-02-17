import pygame
import sys

def test_touchpad():
    """
    Testa o touchpad/mouse usando pygame.
    - Arraste para a esquerda e clique com o botão esquerdo
    - Arraste para a direita e clique com o botão direito
    - Use o scroll (roda do mouse)
    """
    pygame.init()
    
    # Configurações da janela
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Teste de Touchpad/Mouse")
    
    # Cores
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 100, 255)
    YELLOW = (255, 255, 0)
    GRAY = (150, 150, 150)
    
    # Variáveis de controle
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 24)
    
    # Testes a serem realizados
    tests = {
        'left_drag': False,
        'left_click': False,
        'right_drag': False,
        'right_click': False,
        'scroll_up': False,
        'scroll_down': False
    }
    
    # Posição inicial do mouse
    start_pos = None
    dragging_left = False
    dragging_right = False
    
    # Valor do scroll
    scroll_value = 0
    
    running = True
    while running:
        screen.fill(WHITE)
        
        # Título
        title = font.render("Teste de Touchpad/Mouse", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
        
        # Instruções
        instructions = [
            "1. Arraste o mouse para a ESQUERDA (>50px)",
            "2. Clique com o BOTÃO ESQUERDO na área verde",
            "3. Arraste o mouse para a DIREITA (>50px)",
            "4. Clique com o BOTÃO DIREITO na área vermelha",
            "5. Role o scroll PARA CIMA e PARA BAIXO",
            "",
            "Pressione ESC para sair"
        ]
        
        y_offset = 70
        for instruction in instructions:
            if instruction:
                text = small_font.render(instruction, True, BLACK)
            else:
                text = small_font.render(instruction, True, WHITE)
            screen.blit(text, (50, y_offset))
            y_offset += 30
        
        # Áreas de clique
        left_click_area = pygame.Rect(100, 300, 250, 100)
        right_click_area = pygame.Rect(450, 300, 250, 100)
        
        # Desenhar áreas de clique
        pygame.draw.rect(screen, GREEN if not tests['left_click'] else GRAY, left_click_area)
        pygame.draw.rect(screen, BLACK, left_click_area, 2)
        left_text = small_font.render("Clique ESQUERDO aqui", True, BLACK)
        screen.blit(left_text, (left_click_area.centerx - left_text.get_width() // 2,
                                 left_click_area.centery - left_text.get_height() // 2))
        
        pygame.draw.rect(screen, RED if not tests['right_click'] else GRAY, right_click_area)
        pygame.draw.rect(screen, BLACK, right_click_area, 2)
        right_text = small_font.render("Clique DIREITO aqui", True, BLACK)
        screen.blit(right_text, (right_click_area.centerx - right_text.get_width() // 2,
                                  right_click_area.centery - right_text.get_height() // 2))
        
        # Status dos testes
        status_y = 430
        status_texts = [
            f"✓ Arrasto Esquerda" if tests['left_drag'] else "✗ Arrasto Esquerda",
            f"✓ Clique Esquerdo" if tests['left_click'] else "✗ Clique Esquerdo",
            f"✓ Arrasto Direita" if tests['right_drag'] else "✗ Arrasto Direita",
            f"✓ Clique Direito" if tests['right_click'] else "✗ Clique Direito",
            f"✓ Scroll Cima" if tests['scroll_up'] else "✗ Scroll Cima",
            f"✓ Scroll Baixo" if tests['scroll_down'] else "✗ Scroll Baixo"
        ]
        
        for i, status_text in enumerate(status_texts):
            color = GREEN if "✓" in status_text else RED
            text = small_font.render(status_text, True, color)
            col = i % 2
            row = i // 2
            screen.blit(text, (100 + col * 350, status_y + row * 30))
        
        # Indicador de scroll
        scroll_bar_rect = pygame.Rect(WIDTH // 2 - 50, 520, 100, 20)
        pygame.draw.rect(screen, GRAY, scroll_bar_rect)
        scroll_text = small_font.render(f"Scroll: {scroll_value}", True, BLACK)
        screen.blit(scroll_text, (WIDTH // 2 - scroll_text.get_width() // 2, 545))
        
        # Verificar se todos os testes foram concluídos
        if all(tests.values()):
            success_text = font.render("TODOS OS TESTES CONCLUÍDOS!", True, GREEN)
            screen.blit(success_text, (WIDTH // 2 - success_text.get_width() // 2, HEIGHT - 50))
        
        # Processar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # Detecção de movimento do mouse
            elif event.type == pygame.MOUSEMOTION:
                if start_pos is None:
                    start_pos = event.pos
                else:
                    dx = event.pos[0] - start_pos[0]
                    
                    # Arrasto para a esquerda (dx negativo)
                    if dx < -50:
                        tests['left_drag'] = True
                        dragging_left = True
                    
                    # Arrasto para a direita (dx positivo)
                    elif dx > 50:
                        tests['right_drag'] = True
                        dragging_right = True
            
            # Cliques do mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Botão esquerdo (1)
                if event.button == 1:
                    if left_click_area.collidepoint(event.pos):
                        tests['left_click'] = True
                
                # Botão direito (3)
                elif event.button == 3:
                    if right_click_area.collidepoint(event.pos):
                        tests['right_click'] = True
                
                # Scroll para cima (4)
                elif event.button == 4:
                    tests['scroll_up'] = True
                    scroll_value += 1
                
                # Scroll para baixo (5)
                elif event.button == 5:
                    tests['scroll_down'] = True
                    scroll_value -= 1
            
            # Resetar posição inicial ao soltar o botão
            elif event.type == pygame.MOUSEBUTTONUP:
                start_pos = pygame.mouse.get_pos()
                dragging_left = False
                dragging_right = False
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    
    # Retornar resultado dos testes
    return all(tests.values()), tests


if __name__ == "__main__":
    print("Iniciando teste de touchpad...")
    success, results = test_touchpad()
    
    print("\n" + "="*50)
    print("RESULTADOS DO TESTE DE TOUCHPAD")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name}: {status}")
    
    print("="*50)
    
    if success:
        print("\n✓ TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO!")
        sys.exit(0)
    else:
        print("\n✗ ALGUNS TESTES NÃO FORAM CONCLUÍDOS")
        sys.exit(1)
