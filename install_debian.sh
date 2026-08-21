#!/bin/bash

# Script de instalação e inicialização do RevyCheck no Debian Minimal
# Uso: sudo ./install_debian.sh

set -e

echo "========================================"
echo "RevyCheck - Instalação Debian Minimal"
echo "========================================"
echo ""

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Este script precisa ser executado como root (sudo)"
    exit 1
fi

echo "📦 Atualizando sistema..."
apt-get update

echo ""
echo "📦 Instalando dependências básicas..."
apt-get install -y \
    xorg \
    xinit \
    x11-xserver-utils \
    python3 \
    python3-pip \
    python3-pygame \
    python3-opencv \
    python3-numpy \
    python3-pulsectl \
    python3-tk \
    cifs-utils \
    usbutils \
    net-tools \
    alsa-utils \
    pulseaudio \
    sudo

echo ""
echo "📦 Instalando firmware (non-free-firmware)..."
# Sem estes blobs o amdgpu falha o early_init e /sys/class/drm fica vazio:
# nenhum connector, nenhum teste de video possivel. Vale para qualquer maquina
# AMD (Renoir, Green Sardine, Cezanne...) que entre na linha de vistoria.
apt-get install -y \
    firmware-amd-graphics \
    firmware-misc-nonfree \
    firmware-iwlwifi \
    firmware-realtek

echo ""
echo "📦 Instalando dependências Python adicionais via pip..."
pip3 install --break-system-packages -r requirements.txt || pip3 install mysql-connector-python ntplib

echo ""
echo "✅ Dependências instaladas!"
echo ""

# Obter o usuário real (não root)
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "👤 Usuário detectado: $REAL_USER"
echo "🏠 Home: $REAL_HOME"
echo ""

# Criar .xinitrc para iniciar o RevyCheck automaticamente
echo "📝 Configurando .xinitrc..."
cat > "$REAL_HOME/.xinitrc" << 'EOF'
#!/bin/bash

# Desabilitar screensaver e power management
xset s off
xset -dpms
xset s noblank

# Configurar resolução (ajuste conforme necessário)
# xrandr --output HDMI-1 --mode 1920x1080

# Iniciar PulseAudio se não estiver rodando
pulseaudio --start 2>/dev/null || true

# Aguardar X inicializar
sleep 2

# Executar RevyCheck
cd /home/$USER/Desktop/Git/revy-check
python3 src/alltests.py

# Após fechar o RevyCheck, desligar o X
sleep 1
EOF

chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.xinitrc"
chmod +x "$REAL_HOME/.xinitrc"

echo "✅ .xinitrc configurado!"
echo ""

# Criar script de inicialização rápida
echo "📝 Criando script de inicialização..."
cat > "$REAL_HOME/start_revycheck.sh" << 'EOF'
#!/bin/bash

# Script para iniciar RevyCheck com xinit

echo "🚀 Iniciando RevyCheck..."
echo ""
echo "Pressione Ctrl+C para cancelar em 3 segundos..."
sleep 3

# Iniciar X com o RevyCheck
startx
EOF

chown "$REAL_USER:$REAL_USER" "$REAL_HOME/start_revycheck.sh"
chmod +x "$REAL_HOME/start_revycheck.sh"

echo "✅ Script de inicialização criado!"
echo ""

# Configurar auto-login no console (opcional)
read -p "⚠️  Deseja configurar auto-login no console? (s/N): " AUTO_LOGIN
if [[ "$AUTO_LOGIN" =~ ^[Ss]$ ]]; then
    echo "📝 Configurando auto-login..."
    
    # Criar diretório de override do getty
    mkdir -p /etc/systemd/system/getty@tty1.service.d/
    
    # Criar arquivo de override
    cat > /etc/systemd/system/getty@tty1.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $REAL_USER --noclear %I \$TERM
EOF
    
    systemctl daemon-reload
    echo "✅ Auto-login configurado para o usuário $REAL_USER no tty1"
    echo ""
fi

# Configurar inicialização automática do X (opcional)
read -p "⚠️  Deseja iniciar o RevyCheck automaticamente no boot? (s/N): " AUTO_START
if [[ "$AUTO_START" =~ ^[Ss]$ ]]; then
    echo "📝 Configurando auto-start..."
    
    # Adicionar ao .bash_profile para iniciar X automaticamente
    cat >> "$REAL_HOME/.bash_profile" << 'EOF'

# Auto-start RevyCheck no tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
fi
EOF
    
    chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.bash_profile"
    echo "✅ Auto-start configurado!"
    echo ""
fi

# Configurar permissões sudo para montagem SMB (necessário para enviar fotos)
echo "📝 Configurando permissões sudo para SMB..."
cat >> /etc/sudoers.d/revycheck << EOF
# Permitir $REAL_USER montar/desmontar compartilhamentos SMB
$REAL_USER ALL=(ALL) NOPASSWD: /bin/mount -t cifs *
$REAL_USER ALL=(ALL) NOPASSWD: /bin/umount *
$REAL_USER ALL=(ALL) NOPASSWD: /usr/bin/date *
$REAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/ntpdate *
EOF

chmod 440 /etc/sudoers.d/revycheck
echo "✅ Permissões configuradas!"
echo ""

echo "========================================"
echo "✅ Instalação concluída!"
echo "========================================"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Para iniciar manualmente:"
echo "   $ ~/start_revycheck.sh"
echo "   ou"
echo "   $ startx"
echo ""
echo "2. Para testar a câmera separadamente:"
echo "   $ cd ~/Desktop/Git/revy-check"
echo "   $ python3 src/functions/camera.py"
echo ""
echo "3. Configuração SMB para envio de fotos:"
echo "   Edite o arquivo src/alltests.py e configure:"
echo "   smb_config = {"
echo "       'server': '192.168.1.100',"
echo "       'share': 'fotos',"
echo "       'username': 'usuario',"
echo "       'password': 'senha',"
echo "       'remote_path': 'cameras'"
echo "   }"
echo ""
echo "4. Reinicie o sistema para aplicar todas as configurações:"
echo "   $ sudo reboot"
echo ""
echo "========================================"
