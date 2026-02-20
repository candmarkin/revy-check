"""
Funções de teste de portas de vídeo (HDMI/DisplayPort)
"""
import pygame
import subprocess
from datetime import datetime


def get_video_status():
    """Verifica status das portas de vídeo"""
    try:
        result = subprocess.run(
            ['xrandr', '--query'],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout
        
        hdmi_connected = 'HDMI' in output and 'connected' in output
        dp_connected = 'DP' in output and 'connected' in output
        
        return {
            "HDMI": hdmi_connected,
            "DisplayPort": dp_connected
        }
    except Exception as e:
        print(f"Erro ao verificar portas de vídeo: {e}")
        return {"HDMI": False, "DisplayPort": False}


def draw_video_status(screen, width, height, font, status, clock, draw_system_info_func, system_info):
    """Desenha o status das portas de vídeo"""
    screen.fill((240, 240, 240))
    
    # Desenhar informações do sistema
    draw_system_info_func(system_info)
    
    title = font.render("Teste de Portas de Vídeo", True, (0, 0, 0))
    screen.blit(title, title.get_rect(center=(width // 2, 100)))
    
    y = 200
    for port, connected in status.items():
        status_text = "✅ Conectado" if connected else "❌ Desconectado"
        color = (0, 200, 0) if connected else (200, 0, 0)
        
        text = pygame.font.SysFont("Arial", 28).render(f"{port}: {status_text}", True, color)
        screen.blit(text, text.get_rect(center=(width // 2, y)))
        y += 60
    
    instruction = pygame.font.SysFont("Arial", 20).render(
        "Pressione ENTER para continuar",
        True, (100, 100, 100)
    )
    screen.blit(instruction, instruction.get_rect(center=(width // 2, height - 100)))
    
    pygame.display.flip()
    clock.tick(60)


def video_ports_step(screen, width, height, font, clock, draw_text_func, add_log_func, draw_system_info_func, get_system_info_func):
    """
    Executa o teste de portas de vídeo
    
    Returns:
        dict: Status das portas
    """
    running = True
    status = get_video_status()
    system_info = get_system_info_func()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    running = False
        
        draw_video_status(screen, width, height, font, status, clock, draw_system_info_func, system_info)
    
    draw_text_func(["✅ Teste de vídeo concluído!"], (0, 255, 0))
    add_log_func({
        "step": "VIDEO_TEST",
        "time": str(datetime.now()),
        "result": "APROVADO",
        "hdmi": status.get("HDMI", False),
        "displayport": status.get("DisplayPort", False)
    })
    
    return status
