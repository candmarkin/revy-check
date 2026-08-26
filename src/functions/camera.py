import pygame
import cv2
import numpy as np
from datetime import datetime
import os
from pathlib import Path

from src import config, hal
from src.functions import dev_mode

class CameraTest:
    def __init__(self, screen, font, smb_config=None):
        """
        Inicializa o teste de câmera
        
        Args:
            screen: Surface do pygame para renderização
            font: Fonte do pygame para texto
            smb_config: Dict com configurações SMB {'server', 'share', 'username', 'password', 'remote_path'}
        """
        self.screen = screen
        self.font = font
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.smb_config = smb_config or {}
        
        self.camera = None
        self.running = False
        self.photo_taken = False
        self.photo_path = None
        self.upload_success = False
        
    def init_camera(self, camera_index=0):
        """Inicializa a câmera"""
        try:
            self.camera = cv2.VideoCapture(camera_index, hal.camera_backend())
            if not self.camera.isOpened():
                return False, "Não foi possível abrir a câmera"
            
            # Configurar resolução
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            return True, "Câmera inicializada"
        except Exception as e:
            return False, f"Erro ao inicializar câmera: {str(e)}"
    
    def release_camera(self):
        """Libera a câmera"""
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def capture_frame(self):
        """Captura um frame da câmera"""
        if not self.camera:
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        # Converter BGR (OpenCV) para RGB (Pygame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Rotacionar 90 graus se necessário (ajuste conforme orientação)
        frame = np.rot90(frame)
        
        return frame
    
    def frame_to_surface(self, frame):
        """Converte frame numpy para Surface do pygame"""
        if frame is None:
            return None
        
        # Redimensionar para caber na tela mantendo aspect ratio
        h, w = frame.shape[:2]
        scale = min(self.width / w, self.height / h) * 0.9
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        frame_resized = cv2.resize(frame, (new_w, new_h))
        surface = pygame.surfarray.make_surface(frame_resized)
        
        return surface
    
    def save_photo(self, frame, device_serial=None):
        """Salva a foto localmente"""
        if frame is None:
            return False, "Nenhum frame para salvar"
        
        try:
            photos_dir = hal.photos_dir()
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if device_serial:
                filename = f"camera_{device_serial}_{timestamp}.jpg"
            else:
                filename = f"camera_{timestamp}.jpg"
            
            self.photo_path = photos_dir / filename
            
            # Converter RGB de volta para BGR para salvar
            frame_bgr = cv2.cvtColor(np.rot90(frame, -1), cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(self.photo_path), frame_bgr)
            
            return True, str(self.photo_path)
        except Exception as e:
            return False, f"Erro ao salvar foto: {str(e)}"
    
    def upload_to_smb(self):
        """Envia a foto para o compartilhamento SMB.

        O transporte fica no backend: `mount -t cifs` no Linux (com sudo),
        sessao autenticada + copia para caminho UNC no Windows.
        """
        if not self.photo_path or not os.path.exists(self.photo_path):
            return False, "Nenhuma foto para enviar"

        cfg = self.smb_config or config.smb_config()
        if not all([cfg.get("server"), cfg.get("share"),
                    cfg.get("username"), cfg.get("password")]):
            return False, "SMB nao configurado (veja revycheck.env)"

        ok, mensagem = hal.smb_upload(
            self.photo_path,
            cfg["server"], cfg["share"], cfg["username"], cfg["password"],
            cfg.get("remote_path", ""),
        )

        # A foto e' do rosto do colaborador e a maquina vai para ele. Antes
        # ficava no diretorio temporario para sempre, mesmo depois do envio.
        if ok:
            try:
                self.photo_path.unlink()
            except OSError as exc:
                print(f"Nao foi possivel apagar {self.photo_path}: {exc}")
        return ok, mensagem

    def draw_ui(self, surface, message="", color=(255, 255, 255)):
        """Desenha a interface com preview da câmera"""
        self.screen.fill((0, 0, 0))
        
        if surface:
            # Centralizar o preview da câmera
            x = (self.width - surface.get_width()) // 2
            y = (self.height - surface.get_height()) // 2 - 50
            self.screen.blit(surface, (x, y))
            
            # Desenhar borda verde ao redor do preview
            pygame.draw.rect(self.screen, (0, 255, 0), 
                           (x-2, y-2, surface.get_width()+4, surface.get_height()+4), 3)
        
        # Instruções
        if not self.photo_taken:
            instructions = [
                "ESPAÇO - Tirar foto",
                "ESC - Cancelar"
            ]
        else:
            instructions = [
                "ENTER - Enviar foto",
                "R - Tirar outra foto",
                "ESC - Cancelar"
            ]
        
        y_offset = self.height - 150
        for instruction in instructions:
            text = self.font.render(instruction, True, (255, 255, 0))
            x = (self.width - text.get_width()) // 2
            self.screen.blit(text, (x, y_offset))
            y_offset += 35
        
        # Mensagem de status
        if message:
            msg_surface = self.font.render(message, True, color)
            x = (self.width - msg_surface.get_width()) // 2
            self.screen.blit(msg_surface, (x, 50))
        
        pygame.display.flip()
    
    def run(self, device_serial=None):
        """
        Executa o teste de câmera
        
        Returns:
            tuple: (success, message, photo_path)
        """
        # Inicializar câmera
        success, msg = self.init_camera()
        if not success:
            self.draw_ui(None, msg, (255, 0, 0))
            pygame.time.wait(3000)
            return False, msg, None
        
        self.running = True
        self.photo_taken = False
        current_frame = None
        message = "Posicione-se para a foto"
        message_color = (255, 255, 255)
        clock = pygame.time.Clock()
        
        try:
            while self.running:
                # Eventos
                for event in pygame.event.get():
                    dev_mode.handle(event)
                    if event.type == pygame.QUIT:
                        self.running = False
                        return False, "Cancelado pelo usuário", None
                    
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                            return False, "Cancelado pelo usuário", None
                        
                        elif event.key == pygame.K_SPACE and not self.photo_taken:
                            # Tirar foto
                            success, result = self.save_photo(current_frame, device_serial)
                            if success:
                                self.photo_taken = True
                                message = f"Foto salva: {result}"
                                message_color = (0, 255, 0)
                                # Efeito de flash
                                self.screen.fill((255, 255, 255))
                                pygame.display.flip()
                                pygame.time.wait(100)
                            else:
                                message = result
                                message_color = (255, 0, 0)
                        
                        elif event.key == pygame.K_r and self.photo_taken:
                            # Tirar outra foto
                            self.photo_taken = False
                            message = "Posicione-se para a foto"
                            message_color = (255, 255, 255)
                        
                        elif event.key == pygame.K_RETURN and self.photo_taken:
                            # Enviar foto
                            message = "Enviando foto..."
                            message_color = (255, 255, 0)
                            surface = self.frame_to_surface(current_frame)
                            self.draw_ui(surface, message, message_color)
                            
                            success, result = self.upload_to_smb()
                            if success:
                                message = result
                                message_color = (0, 255, 0)
                                self.upload_success = True
                            else:
                                message = result
                                message_color = (255, 0, 0)
                            
                            surface = self.frame_to_surface(current_frame)
                            self.draw_ui(surface, message, message_color)
                            pygame.time.wait(3000)
                            self.running = False
                            return success, result, str(self.photo_path) if self.photo_path else None
                
                # Capturar e exibir frame
                if not self.photo_taken:
                    current_frame = self.capture_frame()
                    surface = self.frame_to_surface(current_frame)
                else:
                    # Mostrar foto capturada
                    surface = self.frame_to_surface(current_frame)
                
                self.draw_ui(surface, message, message_color)
                clock.tick(30)  # 30 FPS
                
        finally:
            self.release_camera()
        
        return False, "Teste não concluído", None


def camera_test_step(screen, font, device_serial=None, smb_config=None):
    """
    Função auxiliar para integrar com o sistema de testes
    
    Args:
        screen: Surface do pygame
        font: Fonte do pygame
        device_serial: Serial do dispositivo para nomear arquivo
        smb_config: Configuração do SMB (opcional)
    
    Returns:
        dict: {'success': bool, 'message': str, 'photo_path': str}
    """
    camera = CameraTest(screen, font, smb_config)
    success, message, photo_path = camera.run(device_serial)
    
    return {
        'success': success,
        'message': message,
        'photo_path': photo_path
    }


if __name__ == "__main__":
    # Teste standalone
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    font = pygame.font.SysFont("Arial", 24)
    smb_config = {}
    
    result = camera_test_step(screen, font, device_serial="TEST123", smb_config=smb_config)
    print(result)
    
    pygame.quit()
