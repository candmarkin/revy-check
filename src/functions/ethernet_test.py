"""
Funções de teste de conexão Ethernet
"""
import pygame
import subprocess
import time
from datetime import datetime


def ethernet_connected():
    """Verifica se há conexão Ethernet ativa"""
    try:
        # Verifica interfaces de rede com IP
        result = subprocess.run(
            ['ip', 'addr', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            # Procura por interface ethernet (eth0, enp*, etc)
            if ('eth' in line or 'enp' in line) and 'state UP' in line:
                # Verifica se tem IP atribuído
                if i + 1 < len(lines) and 'inet ' in lines[i + 1]:
                    return True
        
        return False
    except Exception as e:
        print(f"Erro ao verificar Ethernet: {e}")
        return False


def ethernet_step(screen, width, height, font, clock, draw_text_func, add_log_func, draw_system_info_func, get_system_info_func):
    """
    Executa o teste de conexão Ethernet
    
    Returns:
        bool: True se conectado
    """
    running = True
    connected = False
    check_interval = 1.0  # Verifica a cada 1 segundo
    last_check = 0
    system_info = get_system_info_func()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and connected:
                    running = False

        # Verificar conexão periodicamente
        current_time = time.time()
        if current_time - last_check > check_interval:
            connected = ethernet_connected()
            last_check = current_time

        screen.fill((240, 240, 240))
        
        # Desenhar informações do sistema
        draw_system_info_func(system_info)
        
        title = font.render("Teste de Ethernet", True, (0, 0, 0))
        screen.blit(title, title.get_rect(center=(width // 2, 100)))
        
        if connected:
            status_text = "✅ Ethernet Conectada"
            status_color = (0, 200, 0)
            instruction = "Pressione ENTER para continuar"
        else:
            status_text = "❌ Ethernet Desconectada"
            status_color = (200, 0, 0)
            instruction = "Conecte o cabo Ethernet..."
        
        status = pygame.font.SysFont("Arial", 32).render(status_text, True, status_color)
        screen.blit(status, status.get_rect(center=(width // 2, height // 2)))
        
        instr_text = pygame.font.SysFont("Arial", 20).render(instruction, True, (100, 100, 100))
        screen.blit(instr_text, instr_text.get_rect(center=(width // 2, height - 100)))
        
        pygame.display.flip()
        clock.tick(60)

    draw_text_func(["✅ Teste de Ethernet concluído!"], (0, 255, 0))
    add_log_func({
        "step": "ETHERNET_TEST",
        "time": str(datetime.now()),
        "result": "APROVADO" if connected else "FALHOU"
    })
    
    return connected
