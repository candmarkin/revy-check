import time

import pygame

from src import hal
from src.functions import dev_mode


class WiFiTest:
    def __init__(self, screen, font):
        """
        Inicializa o teste de WiFi

        Args:
            screen: Surface do pygame para renderizacao
            font: Fonte do pygame para texto
        """
        self.screen = screen
        self.font = font
        self.font_large = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.width = screen.get_width()
        self.height = screen.get_height()

        self.wifi_interface = None
        self.has_wifi = False
        self.wifi_enabled = False
        self.networks_found = []
        self.connected_network = None
        self.signal_strength = 0

        self._connection = None
        self._connection_at = 0.0

    # Toda a conversa com o radio fica em `src.hal`: `iw`/`nmcli` no Linux,
    # Native Wifi API no Windows. Aqui sobra so' a tela.

    def detect_wifi_interface(self):
        """Detecta a interface WiFi do sistema"""
        interfaces = hal.wifi_interfaces()
        if not interfaces:
            return False, "Nenhuma interface WiFi detectada"

        self.wifi_interface = interfaces[0][0]
        self.has_wifi = True
        return True, self.wifi_interface

    def check_wifi_status(self):
        """Verifica se o WiFi esta habilitado"""
        self.wifi_enabled = hal.wifi_enabled(self.wifi_interface)
        return self.wifi_enabled

    def enable_wifi(self):
        """Habilita a interface WiFi"""
        if not self.wifi_interface:
            return False, "Interface WiFi nao detectada"
        return hal.wifi_enable(self.wifi_interface)

    def scan_networks(self):
        """Escaneia redes WiFi disponiveis"""
        if not self.wifi_interface:
            return False, []
        ok, networks = hal.wifi_scan(self.wifi_interface)
        self.networks_found = networks
        return ok, networks

    # Consultar o radio custa caro: no Windows abre e fecha uma sessao da
    # Native Wifi API, no Linux dispara um `iw link`. Como `draw_ui` chama isto
    # a cada frame, sem cache seriam ~30 consultas por segundo -- o suficiente
    # para a tela travar e, no Windows, para a rajada de handles derrubar o app.
    CONNECTION_TTL = 2.0

    def get_connection_info(self, force=False):
        """Informacoes da conexao atual, no maximo uma consulta a cada TTL."""
        if not self.wifi_interface:
            return None

        now = time.monotonic()
        if force or now - self._connection_at > self.CONNECTION_TTL:
            try:
                self._connection = hal.wifi_connection_info(self.wifi_interface)
            except Exception as exc:
                # A tela do teste nao pode morrer porque a consulta falhou: sem
                # isto, uma excecao aqui derruba o passo inteiro no meio do
                # desenho e leva o app junto.
                print(f"Falha ao consultar conexao WiFi: {type(exc).__name__}: {exc}")
                self._connection = None
            self._connection_at = now
        return self._connection

    def signal_to_bars(self, signal):
        """Converte sinal em número de barras (0-4)"""
        if not isinstance(signal, (int, float)):
            return 0
        if signal < 0:
            # dBm (negativo)
            if signal >= -50:
                return 4
            elif signal >= -60:
                return 3
            elif signal >= -70:
                return 2
            elif signal >= -80:
                return 1
            else:
                return 0
        else:
            # Percentual (0-100)
            if signal >= 80:
                return 4
            elif signal >= 60:
                return 3
            elif signal >= 40:
                return 2
            elif signal >= 20:
                return 1
            else:
                return 0
    
    def draw_signal_bars(self, x, y, signal, size=20):
        """Desenha barras de sinal WiFi"""
        bars = self.signal_to_bars(signal)
        bar_width = size // 5
        spacing = size // 6
        
        for i in range(4):
            bar_height = (i + 1) * (size // 4)
            bar_x = x + i * (bar_width + spacing)
            bar_y = y + size - bar_height
            
            if i < bars:
                color = (0, 255, 0) if bars >= 3 else (255, 255, 0) if bars >= 2 else (255, 165, 0)
            else:
                color = (100, 100, 100)
            
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, bar_width, bar_height))
    
    def draw_ui(self, message="", color=(255, 255, 255), networks=None, scanning=False):
        """Desenha a interface do teste WiFi"""
        self.screen.fill((20, 20, 40))
        
        # Título
        title = self.font_large.render("🌐 Teste de WiFi", True, (100, 200, 255))
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 30))
        
        y_offset = 100
        
        # Status da interface
        if self.wifi_interface:
            status_text = f"Interface: {self.wifi_interface}"
            status_color = (0, 255, 0) if self.wifi_enabled else (255, 165, 0)
            status = self.font.render(status_text, True, status_color)
            self.screen.blit(status, (50, y_offset))
            y_offset += 40
            
            # Status de habilitação
            enabled_text = "WiFi: HABILITADO" if self.wifi_enabled else "WiFi: DESABILITADO"
            enabled_color = (0, 255, 0) if self.wifi_enabled else (255, 0, 0)
            enabled = self.font.render(enabled_text, True, enabled_color)
            self.screen.blit(enabled, (50, y_offset))
            y_offset += 50
        
        # Conexão atual
        conn_info = self.get_connection_info()
        if conn_info:
            conn_ssid = str(conn_info.get('ssid', 'N/A')).replace('\x00', '')
            conn_text = f"Conectado: {conn_ssid}"
            conn = self.font.render(conn_text, True, (0, 255, 0))
            self.screen.blit(conn, (50, y_offset))
            
            # Barras de sinal
            signal_value = conn_info.get('signal', 0)
            self.draw_signal_bars(self.width - 150, y_offset, signal_value, 30)
            
            signal_text = f"{signal_value} dBm" if signal_value < 0 else f"{signal_value}%"
            signal_label = self.font_small.render(signal_text, True, (200, 200, 200))
            self.screen.blit(signal_label, (self.width - 200, y_offset + 35))
            
            y_offset += 70
        
        # Mensagem de status
        if message:
            msg_surface = self.font.render(message, True, color)
            self.screen.blit(msg_surface, (50, y_offset))
            y_offset += 50
        
        # Lista de redes
        if networks:
            networks_title = self.font.render(f"Redes Encontradas: {len(networks)}", True, (255, 255, 100))
            self.screen.blit(networks_title, (50, y_offset))
            y_offset += 40
            
            # Mostrar até 10 redes
            max_networks = min(10, len(networks))
            for i, network in enumerate(networks[:max_networks]):
                ssid = str(network.get('ssid', 'N/A')).replace('\x00', '')
                signal = network.get('signal', 0)
                band = network.get('band', '?')
                
                # Truncar SSID se muito longo
                if len(ssid) > 30:
                    ssid = ssid[:27] + "..."
                
                net_text = f"{i+1}. {ssid} ({band})"
                net_surface = self.font_small.render(net_text, True, (200, 200, 255))
                self.screen.blit(net_surface, (70, y_offset))
                
                # Barras de sinal
                self.draw_signal_bars(self.width - 150, y_offset, signal, 20)
                
                # Valor do sinal
                signal_text = f"{signal} dBm" if signal < 0 else f"{signal}%"
                signal_surface = self.font_small.render(signal_text, True, (150, 150, 150))
                self.screen.blit(signal_surface, (self.width - 200, y_offset + 22))
                
                y_offset += 35
            
            if len(networks) > max_networks:
                more_text = self.font_small.render(f"... e mais {len(networks) - max_networks} redes", True, (150, 150, 150))
                self.screen.blit(more_text, (70, y_offset))
        
        # Indicador de scan
        if scanning:
            scan_text = self.font.render("Escaneando...", True, (255, 255, 0))
            angle = (pygame.time.get_ticks() // 50) % 360
            rotated = pygame.transform.rotate(scan_text, angle)
            self.screen.blit(rotated, ((self.width - rotated.get_width()) // 2, self.height - 150))
        
        # Instruções
        instructions = [
            "ESPAÇO - Escanear redes",
            "ENTER - Aprovar teste",
            "ESC - Reprovar teste / Sair"
        ]
        
        y_inst = self.height - 100
        for instruction in instructions:
            inst_surface = self.font_small.render(instruction, True, (200, 200, 200))
            self.screen.blit(inst_surface, ((self.width - inst_surface.get_width()) // 2, y_inst))
            y_inst += 25
        
        pygame.display.flip()

    def hold_failure_screen(self, message, color=(255, 0, 0), networks=None):
        """Mantém a tela de falha ativa até o usuário sair manualmente."""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                dev_mode.handle(event)
                if event.type == pygame.QUIT:
                    return

            self.draw_ui(message, color, networks, scanning=False)
            clock.tick(30)
    
    def run(self):
        """
        Executa o teste de WiFi
        
        Returns:
            dict: {'success': bool, 'message': str, 'interface': str, 'networks_found': int}
        """
        clock = pygame.time.Clock()
        running = True
        scanning = False
        approved = False
        has_scanned = False
        max_wait_seconds = 20
        started_at = time.time()
        
        # Detectar interface WiFi
        has_wifi, info = self.detect_wifi_interface()
        
        if not has_wifi:
            fail_message = f"WiFi REPROVADO - {info}"
            self.hold_failure_screen(fail_message, (255, 0, 0))
            return {
                'success': False,
                'message': fail_message,
                'interface': None,
                'networks_found': 0
            }
        
        # Verificar status
        self.check_wifi_status()
        
        # Habilitar WiFi se necessário
        if not self.wifi_enabled:
            self.draw_ui("Habilitando WiFi...", (255, 255, 0))
            success, msg = self.enable_wifi()
            if success:
                self.wifi_enabled = True
                self.check_wifi_status()
            else:
                fail_message = f"WiFi REPROVADO - {msg}"
                self.hold_failure_screen(fail_message, (255, 0, 0))
                return {
                    'success': False,
                    'message': fail_message,
                    'interface': self.wifi_interface,
                    'networks_found': len(self.networks_found)
                }
        
        # Fazer scan inicial
        self.draw_ui("Escaneando redes WiFi...", (255, 255, 0))
        scanning = True
        pygame.display.flip()
        
        success, networks = self.scan_networks()
        scanning = False
        
        message = f"{len(networks)} redes encontradas" if success else "Nenhuma rede encontrada"
        message_color = (0, 255, 0) if len(networks) > 0 else (255, 165, 0)
        
        while running:
            for event in pygame.event.get():
                dev_mode.handle(event)
                if event.type == pygame.QUIT:
                    fail_message = "WiFi REPROVADO - Cancelado pelo usuário"
                    self.hold_failure_screen(fail_message, (255, 0, 0), self.networks_found)
                    return {
                        'success': False,
                        'message': fail_message,
                        'interface': self.wifi_interface,
                        'networks_found': len(self.networks_found)
                    }
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        fail_message = "WiFi REPROVADO - Cancelado pelo usuário"
                        self.hold_failure_screen(fail_message, (255, 0, 0), self.networks_found)
                        return {
                            'success': False,
                            'message': fail_message,
                            'interface': self.wifi_interface,
                            'networks_found': len(self.networks_found)
                        }
                    
                    elif event.key == pygame.K_SPACE:
                        # Escanear novamente
                        message = "Escaneando..."
                        message_color = (255, 255, 0)
                        scanning = True
                        self.draw_ui(message, message_color, self.networks_found, scanning)
                        
                        success, networks = self.scan_networks()
                        scanning = False
                        has_scanned = True
                        started_at = time.time()
                        
                        message = f"{len(networks)} redes encontradas" if success else "Erro ao escanear"
                        message_color = (0, 255, 0) if len(networks) > 0 else (255, 0, 0)
                    
                    elif event.key == pygame.K_RETURN:
                        # Aprovar teste
                        if not has_scanned:
                            message = "Pressione ESPAÇO para escanear antes de aprovar"
                            message_color = (255, 165, 0)
                        elif len(self.networks_found) > 0:
                            approved = True
                            running = False
                            return {
                                'success': True,
                                'message': f"WiFi OK - {len(self.networks_found)} redes detectadas",
                                'interface': self.wifi_interface,
                                'networks_found': len(self.networks_found),
                                'networks': self.networks_found[:5]  # Top 5
                            }
                        else:
                            message = "Escaneie redes antes de aprovar"
                            message_color = (255, 165, 0)

            elapsed = time.time() - started_at
            if elapsed >= max_wait_seconds and not has_scanned:
                fail_message = f"WiFi REPROVADO - Timeout no teste WiFi ({max_wait_seconds}s)"
                self.hold_failure_screen(fail_message, (255, 0, 0), self.networks_found)
                return {
                    'success': False,
                    'message': fail_message,
                    'interface': self.wifi_interface,
                    'networks_found': len(self.networks_found)
                }
            
            self.draw_ui(message, message_color, self.networks_found, scanning)
            clock.tick(30)
        
        return {
            'success': approved,
            'message': message,
            'interface': self.wifi_interface,
            'networks_found': len(self.networks_found)
        }


def wifi_test_step(screen, font):
    """
    Função auxiliar para integrar com o sistema de testes
    
    Args:
        screen: Surface do pygame
        font: Fonte do pygame
    
    Returns:
        dict: Resultado do teste
    """
    wifi = WiFiTest(screen, font)
    result = wifi.run()
    return result


if __name__ == "__main__":
    # Teste standalone
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    pygame.display.set_caption("Teste WiFi")
    font = pygame.font.SysFont("Arial", 24)
    
    result = wifi_test_step(screen, font)
    print(result)
    
    pygame.quit()
