import pygame
import subprocess
import time
import re
import shutil
from datetime import datetime

class WiFiTest:
    def __init__(self, screen, font):
        """
        Inicializa o teste de WiFi
        
        Args:
            screen: Surface do pygame para renderização
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

    def _command_exists(self, command):
        return shutil.which(command) is not None

    def _has_iw(self):
        return self._command_exists("iw") or self._command_exists("sudo")

    def _run_iw(self, args, timeout=5):
        commands = []
        if self._command_exists("iw"):
            commands.append(["iw", *args])
        if self._command_exists("sudo"):
            commands.append(["sudo", "-n", "iw", *args])

        last_error = None
        for cmd in commands:
            try:
                return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=timeout)
            except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        raise FileNotFoundError("iw não disponível")
        
    def detect_wifi_interface(self):
        """Detecta a interface WiFi do sistema"""
        try:
            # Método 1: iw dev
            if self._has_iw():
                try:
                    output = self._run_iw(["dev"], timeout=5)
                    for line in output.split('\n'):
                        if 'Interface' in line:
                            interface = line.split()[-1]
                            if interface.startswith('wl') or interface.startswith('wlan'):
                                self.wifi_interface = interface
                                self.has_wifi = True
                                return True, interface
                except:
                    pass
            
            # Método 2: ip link
            if not self.wifi_interface and self._command_exists("ip"):
                output = subprocess.check_output(["ip", "link", "show"], text=True, timeout=5)
                for line in output.split('\n'):
                    if 'wlan' in line or 'wlp' in line:
                        match = re.search(r'\d+:\s+(\w+):', line)
                        if match:
                            self.wifi_interface = match.group(1)
                            self.has_wifi = True
                            return True, self.wifi_interface
            
            # Método 3: nmcli (NetworkManager)
            if self._command_exists("nmcli"):
                try:
                    output = subprocess.check_output(
                        ["nmcli", "device", "status"], 
                        text=True, 
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )
                    for line in output.split('\n')[1:]:
                        if 'wifi' in line.lower():
                            parts = line.split()
                            if parts:
                                self.wifi_interface = parts[0]
                                self.has_wifi = True
                                return True, self.wifi_interface
                except:
                    pass

            if not (self._has_iw() or self._command_exists("ip") or self._command_exists("nmcli")):
                return False, "Comandos WiFi não disponíveis (iw/ip/nmcli)"
            
            return False, "Nenhuma interface WiFi detectada"
            
        except Exception as e:
            return False, f"Erro ao detectar WiFi: {str(e)}"
    
    def check_wifi_status(self):
        """Verifica se o WiFi está habilitado"""
        if not self.wifi_interface:
            return False
        
        try:
            # Verificar se a interface está UP
            if self._command_exists("ip"):
                output = subprocess.check_output(
                    ["ip", "link", "show", self.wifi_interface], 
                    text=True,
                    timeout=5
                )
                self.wifi_enabled = "UP" in output and "state UP" in output
                return self.wifi_enabled

            if self._command_exists("nmcli"):
                output = subprocess.check_output(["nmcli", "radio", "wifi"], text=True, timeout=5)
                self.wifi_enabled = output.strip().lower() == "enabled"
                return self.wifi_enabled

            return False
        except:
            return False
    
    def enable_wifi(self):
        """Habilita a interface WiFi"""
        if not self.wifi_interface:
            return False, "Interface WiFi não detectada"
        
        try:
            ip_result = None
            if self._command_exists("ip"):
                ip_result = subprocess.run(
                    ["ip", "link", "set", self.wifi_interface, "up"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if ip_result.returncode == 0:
                    time.sleep(2)
                    return True, "WiFi habilitado"

            nmcli_result = None
            if self._command_exists("nmcli"):
                nmcli_result = subprocess.run(
                    ["nmcli", "radio", "wifi", "on"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if nmcli_result.returncode == 0:
                    time.sleep(2)
                    return True, "WiFi habilitado"

            if not any(self._command_exists(cmd) for cmd in ("ip", "nmcli")):
                return False, "Sem comando para habilitar WiFi (ip/nmcli)"

            ip_error = ip_result.stderr.strip() if ip_result and ip_result.stderr else ""
            nmcli_error = nmcli_result.stderr.strip() if nmcli_result and nmcli_result.stderr else ""
            error_message = ip_error or nmcli_error or "Falha ao habilitar WiFi"
            return False, error_message
        except Exception as e:
            return False, f"Erro ao habilitar WiFi: {str(e)}"
    
    def scan_networks(self):
        """Escaneia redes WiFi disponíveis"""
        if not self.wifi_interface:
            return False, []
        
        try:
            # Método 1: iw scan
            if self._has_iw():
                try:
                    output = self._run_iw([self.wifi_interface, "scan"], timeout=10)

                    networks = []
                    current_network = {}

                    for line in output.split('\n'):
                        line = line.strip()

                        if line.startswith('BSS'):
                            if current_network:
                                networks.append(current_network)
                            current_network = {'bssid': line.split()[1].rstrip('(on')}

                        elif 'SSID:' in line:
                            ssid = line.split('SSID:', 1)[1].strip()
                            if ssid:
                                current_network['ssid'] = ssid

                        elif 'signal:' in line:
                            match = re.search(r'(-?\d+\.\d+)\s*dBm', line)
                            if match:
                                current_network['signal'] = float(match.group(1))

                        elif 'freq:' in line:
                            match = re.search(r'freq:\s*(\d+)', line)
                            if match:
                                freq = int(match.group(1))
                                current_network['frequency'] = freq
                                if freq >= 5000:
                                    current_network['band'] = '5GHz'
                                else:
                                    current_network['band'] = '2.4GHz'

                    if current_network and 'ssid' in current_network:
                        networks.append(current_network)

                    # Ordenar por sinal (mais forte primeiro)
                    networks.sort(key=lambda x: x.get('signal', -100), reverse=True)
                    self.networks_found = networks
                    return True, networks
                
                except subprocess.TimeoutExpired:
                    return False, []
                except:
                    pass
            
            # Método 2: nmcli (NetworkManager)
            if self._command_exists("nmcli"):
                try:
                    output = subprocess.check_output(
                        ["nmcli", "-f", "SSID,SIGNAL,FREQ,BSSID", "device", "wifi", "list"],
                        text=True,
                        stderr=subprocess.DEVNULL,
                        timeout=10
                    )

                    networks = []
                    for line in output.split('\n')[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                ssid = ' '.join(parts[:-3]) if len(parts) > 3 else parts[0]
                                if ssid and ssid != '--':
                                    network = {
                                        'ssid': ssid,
                                        'signal': int(parts[-3]) if len(parts) >= 3 else 0,
                                        'frequency': int(parts[-2]) if len(parts) >= 2 else 0,
                                        'bssid': parts[-1] if len(parts) >= 1 else ''
                                    }

                                    if network['frequency'] >= 5000:
                                        network['band'] = '5GHz'
                                    else:
                                        network['band'] = '2.4GHz'

                                    networks.append(network)

                    networks.sort(key=lambda x: x.get('signal', 0), reverse=True)
                    self.networks_found = networks
                    return True, networks
                except:
                    pass
            
            return False, []
            
        except Exception as e:
            return False, []
    
    def get_connection_info(self):
        """Obtém informações da conexão atual"""
        if not self.wifi_interface:
            return None
        
        try:
            # Método 1: iw
            if self._has_iw():
                try:
                    output = self._run_iw([self.wifi_interface, "link"], timeout=5)

                    if "Not connected" in output:
                        return None

                    info = {}
                    for line in output.split('\n'):
                        if 'SSID:' in line:
                            info['ssid'] = line.split('SSID:', 1)[1].strip()
                        elif 'signal:' in line:
                            match = re.search(r'(-?\d+)\s*dBm', line)
                            if match:
                                info['signal'] = int(match.group(1))

                    return info if info else None
                except:
                    pass
            
            # Método 2: nmcli
            if self._command_exists("nmcli"):
                try:
                    output = subprocess.check_output(
                        ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "device", "wifi"],
                        text=True,
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )

                    for line in output.split('\n'):
                        if line.startswith('yes:'):
                            parts = line.split(':')
                            if len(parts) >= 3:
                                return {
                                    'ssid': parts[1],
                                    'signal': int(parts[2]) if parts[2].isdigit() else 0
                                }
                except:
                    pass
            
            return None
            
        except Exception:
            return None
    
    def signal_to_bars(self, signal):
        """Converte sinal em número de barras (0-4)"""
        if isinstance(signal, int) and signal < 0:
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
            conn_text = f"Conectado: {conn_info.get('ssid', 'N/A')}"
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
                ssid = network.get('ssid', 'N/A')
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
            "ESC - Cancelar"
        ]
        
        y_inst = self.height - 100
        for instruction in instructions:
            inst_surface = self.font_small.render(instruction, True, (200, 200, 200))
            self.screen.blit(inst_surface, ((self.width - inst_surface.get_width()) // 2, y_inst))
            y_inst += 25
        
        pygame.display.flip()
    
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
        max_wait_seconds = 20
        started_at = time.time()
        
        # Detectar interface WiFi
        has_wifi, info = self.detect_wifi_interface()
        
        if not has_wifi:
            self.draw_ui(info, (255, 0, 0))
            pygame.time.wait(3000)
            return {
                'success': False,
                'message': info,
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
                self.draw_ui(msg, (255, 0, 0))
                pygame.time.wait(3000)
        
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
                if event.type == pygame.QUIT:
                    running = False
                    return {
                        'success': False,
                        'message': "Cancelado pelo usuário",
                        'interface': self.wifi_interface,
                        'networks_found': len(self.networks_found)
                    }
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        return {
                            'success': False,
                            'message': "Cancelado pelo usuário",
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
                        started_at = time.time()
                        
                        message = f"{len(networks)} redes encontradas" if success else "Erro ao escanear"
                        message_color = (0, 255, 0) if len(networks) > 0 else (255, 0, 0)
                    
                    elif event.key == pygame.K_RETURN:
                        # Aprovar teste
                        if len(self.networks_found) > 0:
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
            if elapsed >= max_wait_seconds:
                if len(self.networks_found) > 0:
                    return {
                        'success': True,
                        'message': f"WiFi OK - auto aprovação após {max_wait_seconds}s",
                        'interface': self.wifi_interface,
                        'networks_found': len(self.networks_found),
                        'networks': self.networks_found[:5]
                    }
                return {
                    'success': False,
                    'message': f"Timeout no teste WiFi ({max_wait_seconds}s)",
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
