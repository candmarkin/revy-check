# 📸 Módulo de Câmera - RevyCheck

Sistema de captura de foto com preview em tela cheia e envio automático para SMB share.

## 🎯 Funcionalidades

- ✅ Preview em tempo real da câmera
- ✅ Captura de foto em alta resolução
- ✅ Efeito visual de flash ao tirar foto
- ✅ Envio automático para compartilhamento SMB/CIFS
- ✅ Interface fullscreen com Pygame
- ✅ Nomenclatura automática com serial do dispositivo

## 📋 Dependências

### Debian/Ubuntu

```bash
sudo apt-get install -y \
    python3-opencv \
    python3-pygame \
    python3-numpy \
    cifs-utils
```

### Via pip (se necessário)

```bash
pip3 install opencv-python pygame numpy
```

## 🚀 Instalação Rápida (Debian Minimal)

Execute o script de instalação automática:

```bash
cd ~/Desktop/Git/revy-check
chmod +x install_debian.sh
sudo ./install_debian.sh
```

Este script irá:
1. Instalar todas as dependências (Xorg, Python, OpenCV, etc)
2. Configurar xinit para iniciar automaticamente
3. Criar scripts de inicialização
4. Configurar permissões para montagem SMB

## 🎮 Uso Standalone

Para testar apenas o módulo de câmera:

```bash
cd ~/Desktop/Git/revy-check
python3 src/functions/camera.py
```

## 🔧 Configuração SMB

Edite a configuração no código ou passe como parâmetro:

```python
smb_config = {
    'server': '192.168.1.100',      # IP do servidor SMB
    'share': 'fotos',                # Nome do compartilhamento
    'username': 'usuario',           # Usuário
    'password': 'senha',             # Senha
    'remote_path': 'cameras'         # Pasta dentro do share
}
```

## 📱 Controles

### Durante o Preview
- **ESPAÇO** - Tirar foto
- **ESC** - Cancelar e sair

### Após tirar a foto
- **ENTER** - Enviar foto para SMB
- **R** - Tirar outra foto
- **ESC** - Cancelar e sair

## 🔌 Integração com alltests.py

Veja o arquivo `CAMERA_INTEGRATION_EXAMPLE.py` para exemplo completo.

### Passos básicos:

1. **Importar o módulo:**
```python
from src.functions.camera import camera_test_step
```

2. **Configurar SMB:**
```python
SMB_CONFIG = {
    'server': '192.168.1.100',
    'share': 'fotos',
    'username': 'usuario',
    'password': 'senha',
    'remote_path': 'cameras'
}
```

3. **Adicionar estado no fluxo:**
```python
elif state == "CAMERA_STEP":
    device_serial = get_device_serial()  # Função já existe no alltests.py
    result = camera_test_step(SCREEN, FONT, device_serial, SMB_CONFIG)
    
    if result['success']:
        add_log({"step":"CAMERA_TEST", "result":"APROVADO"})
    else:
        add_log({"step":"CAMERA_TEST", "result":"REPROVADO"})
    
    state = "NEXT_STEP"
```

## 🖥️ Inicialização com xinit

### Arquivo .xinitrc (criado automaticamente)

O script de instalação cria um `.xinitrc` que:
- Desabilita screensaver
- Desabilita power management
- Inicia PulseAudio
- Executa o RevyCheck em fullscreen

### Iniciar manualmente

```bash
startx
```

### Iniciar automaticamente no boot

O script de instalação pergunta se você quer auto-login e auto-start.

## 📂 Estrutura de Arquivos

```
revy-check/
├── src/
│   └── functions/
│       └── camera.py              # Módulo principal
├── install_debian.sh              # Script de instalação
├── CAMERA_INTEGRATION_EXAMPLE.py  # Exemplo de integração
└── README_CAMERA.md               # Este arquivo
```

## 🔍 Troubleshooting

### Câmera não detectada

```bash
# Verificar se a câmera está disponível
ls /dev/video*

# Testar com v4l2
v4l2-ctl --list-devices

# Dar permissões ao usuário
sudo usermod -aG video $USER
```

### SMB não monta

```bash
# Testar montagem manual
sudo mount -t cifs //servidor/share /mnt/test \
    -o username=usuario,password=senha

# Verificar conectividade
ping servidor
smbclient -L //servidor -U usuario
```

### X não inicia

```bash
# Verificar logs
cat ~/.local/share/xorg/Xorg.0.log

# Verificar se Xorg está instalado
which X

# Reinstalar se necessário
sudo apt-get install --reinstall xorg
```

### OpenCV não abre câmera

```bash
# Instalar v4l-utils
sudo apt-get install v4l-utils

# Verificar dispositivos
v4l2-ctl --list-devices

# Testar com ferramenta simples
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'ERRO')"
```

## 📸 Formato das Fotos

- **Formato:** JPEG
- **Nome:** `camera_{serial}_{timestamp}.jpg`
- **Exemplo:** `camera_ABC123_20260217_143022.jpg`
- **Local temporário:** `/tmp/revy_photos/`
- **Local final:** `//servidor/share/cameras/` (configurável)

## 🔒 Permissões Necessárias

O script de instalação configura automaticamente em `/etc/sudoers.d/revycheck`:

```
usuario ALL=(ALL) NOPASSWD: /bin/mount -t cifs *
usuario ALL=(ALL) NOPASSWD: /bin/umount *
```

Isso permite montar/desmontar SMB sem senha.

## 💡 Dicas

1. **Iluminação:** Certifique-se de ter boa iluminação para fotos de qualidade
2. **Posicionamento:** A câmera deve estar estável e bem posicionada
3. **Resolução:** Ajuste em `camera.py` linha 37 se necessário
4. **Orientação:** Ajuste a rotação em `camera.py` linha 54 se a imagem estiver invertida

## 📊 Logs

Os logs da câmera são salvos junto com os outros testes:

```json
{
  "step": "CAMERA_TEST",
  "time": "2026-02-17 14:30:22",
  "result": "APROVADO",
  "photo_path": "/tmp/revy_photos/camera_ABC123_20260217_143022.jpg"
}
```

## 🎨 Personalização

### Mudar resolução da câmera

Em `camera.py`, linha 36-37:

```python
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)   # Largura
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Altura
```

### Mudar índice da câmera

Se você tem múltiplas câmeras:

```python
camera.init_camera(camera_index=1)  # 0, 1, 2, etc
```

### Customizar interface

Modifique o método `draw_ui()` em `camera.py` para mudar cores, posições, textos, etc.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `~/.local/share/xorg/Xorg.0.log`
2. Execute em modo debug: `python3 -m pdb src/functions/camera.py`
3. Teste cada componente separadamente (câmera, SMB, X)
