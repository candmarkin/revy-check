# 📡 Módulo de Teste WiFi - RevyCheck

Sistema completo de detecção e teste de placa WiFi com interface gráfica Pygame.

## 🎯 Funcionalidades

- ✅ Detecção automática da interface WiFi (wlan0, wlp*, etc)
- ✅ Verificação de status (habilitado/desabilitado)
- ✅ Habilitação automática se desabilitado
- ✅ Scan de redes disponíveis
- ✅ Exibição de força do sinal (barras visuais)
- ✅ Suporte para 2.4GHz e 5GHz
- ✅ Interface fullscreen com Pygame
- ✅ Lista top 10 redes com melhor sinal
- ✅ Informações de conexão atual (se conectado)

## 📋 Dependências

### Debian/Ubuntu

```bash
sudo apt-get install -y \
    python3-pygame \
    wireless-tools \
    iw \
    network-manager \
    net-tools
```

### Permissões necessárias

Para executar o scan, você precisa de permissões sudo. Configure em `/etc/sudoers.d/revycheck`:

```bash
sudo visudo -f /etc/sudoers.d/revycheck
```

Adicione:
```
usuario ALL=(ALL) NOPASSWD: /usr/sbin/iw * scan
usuario ALL=(ALL) NOPASSWD: /sbin/ip link set * up
usuario ALL=(ALL) NOPASSWD: /sbin/ip link set * down
```

Ou execute o script de instalação que configura automaticamente:
```bash
sudo ./install_debian.sh
```

## 🚀 Uso Standalone

Para testar apenas o módulo WiFi:

```bash
cd ~/Desktop/Git/revy-check
python3 src/functions/wifi.py
```

## 🎮 Controles

- **ESPAÇO** - Escanear redes WiFi
- **ENTER** - Aprovar teste (se redes foram encontradas)
- **ESC** - Cancelar e sair

## 📊 Interface

A interface mostra:

1. **Status da Interface**
   - Nome da interface (wlan0, wlp3s0, etc)
   - Status (habilitado/desabilitado)

2. **Conexão Atual**
   - SSID da rede conectada
   - Força do sinal (barras e dBm)

3. **Lista de Redes**
   - Top 10 redes por força de sinal
   - SSID, banda (2.4GHz/5GHz), sinal em dBm
   - Barras visuais de força do sinal

4. **Instruções**
   - Controles disponíveis

## 🔧 Métodos de Detecção

O módulo tenta múltiplos métodos para detectar WiFi:

### 1. iw dev
```bash
iw dev
```
- Método preferencial
- Mais detalhado
- Requer pacote `iw`

### 2. ip link
```bash
ip link show
```
- Fallback se iw não disponível
- Busca interfaces wlan* ou wlp*

### 3. NetworkManager (nmcli)
```bash
nmcli device status
```
- Para sistemas com NetworkManager
- Mais user-friendly

## 📡 Scan de Redes

### Método 1: iw scan
```bash
sudo iw wlan0 scan
```
- Mais completo
- Retorna: SSID, BSSID, sinal (dBm), frequência, etc

### Método 2: nmcli
```bash
nmcli device wifi list
```
- Mais simples
- Funciona com NetworkManager

## 🔌 Integração com alltests.py

Veja o arquivo `WIFI_INTEGRATION_EXAMPLE.py` para exemplo completo.

### Passos básicos:

1. **Importar o módulo:**
```python
from src.functions.wifi import wifi_test_step
```

2. **Verificar se tem WiFi (opcional):**
```python
def has_wifi_hardware():
    try:
        output = subprocess.check_output(["iw", "dev"], text=True)
        return "Interface" in output
    except:
        return False

HAS_WIFI = has_wifi_hardware()
```

3. **Adicionar estado no fluxo:**
```python
elif state == "WIFI_STEP":
    if HAS_WIFI:
        result = wifi_test_step(SCREEN, FONT)
        
        if result['success']:
            add_log({
                "step": "WIFI_TEST",
                "result": "APROVADO",
                "interface": result['interface'],
                "networks": result['networks_found']
            })
        else:
            add_log({
                "step": "WIFI_TEST",
                "result": "REPROVADO"
            })
    
    state = "NEXT_STEP"
```

## 📊 Formato do Resultado

```python
{
    'success': True,
    'message': 'WiFi OK - 12 redes detectadas',
    'interface': 'wlan0',
    'networks_found': 12,
    'networks': [
        {
            'ssid': 'MinhaRede',
            'signal': -45,
            'frequency': 5180,
            'band': '5GHz',
            'bssid': 'AA:BB:CC:DD:EE:FF'
        },
        # ... top 5 redes
    ]
}
```

## 🎨 Força do Sinal

### Escala dBm (valores negativos)
- **-50 dBm ou melhor**: 4 barras (excelente) 🟢
- **-60 dBm**: 3 barras (bom) 🟢
- **-70 dBm**: 2 barras (regular) 🟡
- **-80 dBm**: 1 barra (fraco) 🟠
- **-90 dBm ou pior**: 0 barras (muito fraco) 🔴

### Escala percentual (0-100)
- **80-100%**: 4 barras
- **60-79%**: 3 barras
- **40-59%**: 2 barras
- **20-39%**: 1 barra
- **0-19%**: 0 barras

## 🔍 Troubleshooting

### WiFi não detectado

```bash
# Verificar se o driver está carregado
lspci | grep -i network
lshw -C network

# Verificar módulos do kernel
lsmod | grep wifi
lsmod | grep 80211

# Verificar rfkill
rfkill list
# Se bloqueado:
sudo rfkill unblock wifi
```

### Não consegue fazer scan

```bash
# Verificar permissões
sudo iw wlan0 scan

# Se funcionar, configure sudoers:
sudo visudo -f /etc/sudoers.d/revycheck
```

### Interface não sobe

```bash
# Tentar manualmente
sudo ip link set wlan0 up

# Verificar NetworkManager
systemctl status NetworkManager

# Desabilitar gerenciamento do NM (se necessário)
sudo nmcli device set wlan0 managed no
```

### Nenhuma rede encontrada

```bash
# Verificar se WiFi está desbloqueado
rfkill list

# Verificar se há redes no ar
sudo iwlist wlan0 scan | grep ESSID

# Verificar se a antena está conectada (notebooks)
# Alguns notebooks têm switch físico ou Fn+tecla
```

## 🌐 Bandas Suportadas

O teste detecta automaticamente:
- **2.4 GHz**: 2400-2500 MHz
- **5 GHz**: 5000-6000 MHz

## 📝 Logs

Exemplo de log gerado:

```json
{
  "step": "WIFI_TEST",
  "time": "2026-02-17 15:45:30",
  "result": "APROVADO",
  "interface": "wlan0",
  "networks_found": 15,
  "top_networks": [
    "Revy-5G",
    "Revy-2.4G",
    "Vizinho-WiFi",
    "NET_2G_123456",
    "Claro_5G"
  ]
}
```

## 🔐 Segurança

O módulo **NÃO**:
- ❌ Conecta em redes
- ❌ Armazena senhas
- ❌ Modifica configurações permanentes
- ❌ Envia dados para redes externas

Apenas:
- ✅ Detecta interface
- ✅ Habilita interface (se necessário)
- ✅ Faz scan de redes disponíveis
- ✅ Mostra informações públicas (SSID, sinal, banda)

## 💡 Dicas

1. **Posicionamento**: Mantenha o dispositivo próximo a roteadores para melhor detecção
2. **Scan múltiplo**: Pressione ESPAÇO várias vezes para ver mais redes
3. **Tempo de scan**: O primeiro scan pode demorar 5-10 segundos
4. **Redes ocultas**: SSIDs ocultos não serão detectados
5. **Interferência**: Ambientes com muitos dispositivos podem afetar a detecção

## 🆘 Comandos Úteis

```bash
# Informações detalhadas da interface
iw wlan0 info

# Status do link
iw wlan0 link

# Potências de transmissão suportadas
iw wlan0 txpower

# Canais disponíveis
iw wlan0 channels

# Estatísticas
iw wlan0 station dump

# Desbloquear WiFi
sudo rfkill unblock wifi

# Reiniciar interface
sudo ip link set wlan0 down
sudo ip link set wlan0 up
```

## 📦 Instalação de Drivers

### Intel WiFi
```bash
sudo apt-get install firmware-iwlwifi
```

### Broadcom WiFi
```bash
sudo apt-get install firmware-b43-installer
```

### Realtek WiFi
```bash
sudo apt-get install firmware-realtek
```

### Atheros WiFi
```bash
sudo apt-get install firmware-atheros
```

## 🎯 Casos de Uso

1. **Teste de Qualidade**: Verificar se WiFi funciona antes de enviar dispositivo
2. **Diagnóstico**: Identificar problemas de hardware WiFi
3. **Validação**: Confirmar que drivers estão instalados e funcionando
4. **Benchmarking**: Comparar força de sinal entre dispositivos
