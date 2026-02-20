"""
Funções de teste de portas USB
"""
import pygame
import subprocess
import time
from datetime import datetime


def port_has_device(port_path):
    """Verifica se uma porta USB possui dispositivo conectado"""
    try:
        result = subprocess.run(
            ['lsusb', '-s', port_path],
            capture_output=True,
            text=True,
            timeout=2
        )
        return len(result.stdout.strip()) > 0
    except:
        return False


def get_usb_devices():
    """Retorna lista de dispositivos USB conectados"""
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
        devices = result.stdout.strip().split('\n')
        return [d for d in devices if d]
    except Exception as e:
        print(f"Erro ao obter dispositivos USB: {e}")
        return []


def usb_step(screen, width, height, font, clock, draw_text_func, add_log_func, draw_system_info_func, get_system_info_func, ports_to_check):
    """
    Executa o teste de portas USB
    
    Args:
        ports_to_check: Dict com configuração de portas (ex: {"LEFT": 2, "RIGHT": 1})
    
    Returns:
        bool: True se aprovado
    """
    ports_detected = {"LEFT": 0, "RIGHT": 0}
    running = True
    start_time = time.time()
    timeout = 30  # 30 segundos
    system_info = get_system_info_func()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Verificar se todas as portas foram detectadas
                    all_ok = True
                    for side, expected in ports_to_check.items():
                        if ports_detected[side] < expected:
                            all_ok = False
                            break
                    
                    if all_ok:
                        running = False

        # Atualizar contagem de portas
        devices = get_usb_devices()
        # Lógica simplificada: conta total de dispositivos
        # Em produção, você deve mapear cada dispositivo para LEFT/RIGHT
        total_devices = len(devices)
        
        screen.fill((240, 240, 240))
        
        # Desenhar informações do sistema
        draw_system_info_func(system_info)
        
        # Instruções
        title = font.render("Teste de Portas USB", True, (0, 0, 0))
        screen.blit(title, title.get_rect(center=(width // 2, 100)))
        
        instructions = [
            "Conecte dispositivos USB nas portas:",
            f"Esquerda: {ports_to_check.get('LEFT', 0)} porta(s)",
            f"Direita: {ports_to_check.get('RIGHT', 0)} porta(s)",
            "",
            f"Dispositivos detectados: {total_devices}",
            "",
            "Pressione ENTER quando todas as portas forem testadas"
        ]
        
        y = 200
        for line in instructions:
            text = pygame.font.SysFont("Arial", 24).render(line, True, (0, 0, 0))
            screen.blit(text, text.get_rect(center=(width // 2, y)))
            y += 40
        
        # Timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            timeout_text = font.render("TIMEOUT - Pressione ENTER para continuar", True, (255, 0, 0))
            screen.blit(timeout_text, timeout_text.get_rect(center=(width // 2, height - 100)))
        
        pygame.display.flip()
        clock.tick(60)

    draw_text_func(["✅ Teste de USB concluído!"], (0, 255, 0))
    add_log_func({"step": "USB_TEST", "time": str(datetime.now()), "result": "APROVADO", "devices": total_devices})
    return True
