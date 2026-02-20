# Atualização: Testes de WiFi, Touchpad e Câmera

## 📋 Resumo das Mudanças

Esta atualização adiciona três novos testes ao sistema revy-check:
- **WiFi**: Teste de conectividade e detecção de redes
- **Touchpad**: Teste de movimentos, cliques e scroll
- **Câmera**: Teste de captura de imagem

## 🗄️ Alterações no Banco de Dados

### Novas Colunas na Tabela `devices`

Foram adicionadas três novas colunas na tabela `devices`:

```sql
ALTER TABLE devices 
ADD COLUMN has_wifi TINYINT(1) DEFAULT 0 COMMENT 'Indica se o dispositivo possui WiFi';

ALTER TABLE devices 
ADD COLUMN has_touchpad TINYINT(1) DEFAULT 0 COMMENT 'Indica se o dispositivo possui touchpad';

ALTER TABLE devices 
ADD COLUMN has_camera TINYINT(1) DEFAULT 0 COMMENT 'Indica se o dispositivo possui câmera/webcam';
```

**Para aplicar as mudanças no banco de dados, execute:**
```bash
mysql -h revy.selbetti.com.br -u drack -p revycheck < scripts/add_new_device_columns.sql
```

## 📂 Arquivos Modificados

### `src/alltests.py`
- ✅ Importação dos novos módulos (`WiFiTest`, `CameraTest`, `touchpad_step`)
- ✅ Adição das perguntas no cadastro de dispositivos
- ✅ Atualização da função `send_to_db()` para incluir as novas colunas
- ✅ Atualização da função `fetch_device_info()` para buscar as novas configurações
- ✅ Adição das variáveis globais `HAS_WIFI`, `HAS_TOUCHPAD`, `HAS_CAMERA`
- ✅ Integração dos testes no fluxo principal (estados `WIFI_STEP`, `TOUCHPAD_STEP`, `CAMERA_STEP`)

## 🔄 Fluxo de Testes Atualizado

```
START_STEP
  ↓
SCREEN_STEP (se HAS_EMBEDDED_SCREEN)
  ↓
KEYBOARD_STEP (se HAS_EMBEDDED_KEYBOARD)
  ↓
USB_STEP
  ↓
VIDEO_STEP
  ↓
HEADPHONE_STEP (se HAS_HEADPHONE_JACK)
  ↓
SPEAKER_STEP (se HAS_SPEAKER)
  ↓
MIC_STEP (se HAS_MICROPHONE)
  ↓
ETHERNET_STEP (se HAS_ETHERNET_PORT)
  ↓
WIFI_STEP (se HAS_WIFI) ⭐ NOVO
  ↓
TOUCHPAD_STEP (se HAS_TOUCHPAD) ⭐ NOVO
  ↓
CAMERA_STEP (se HAS_CAMERA) ⭐ NOVO
  ↓
DONE
```

## 📝 Logs Gerados

### WiFi
- `WIFI_TEST_START`: Início do teste de WiFi
- `WIFI_TEST`: Resultado do teste (APROVADO/REPROVADO)

### Touchpad
- `TOUCHPAD_TEST_START`: Início do teste de touchpad
- `TOUCHPAD_DRAG_LEFT`: Arrasto para a esquerda
- `TOUCHPAD_LEFT_CLICK`: Clique com botão esquerdo
- `TOUCHPAD_MIDDLE_CLICK`: Clique com botão do meio
- `TOUCHPAD_DRAG_RIGHT`: Arrasto para a direita
- `TOUCHPAD_RIGHT_CLICK`: Clique com botão direito
- `TOUCHPAD_SCROLL_UP`: Scroll para cima
- `TOUCHPAD_SCROLL_DOWN`: Scroll para baixo

### Câmera
- `CAMERA_TEST_START`: Início do teste de câmera
- `CAMERA_TEST`: Resultado do teste (APROVADO/REPROVADO)

## 🎯 Funcionalidades dos Testes

### WiFi Test (`src/functions/wifi.py`)
- Detecta interface WiFi do sistema
- Escaneia redes disponíveis
- Mostra força do sinal
- Verifica conectividade

### Touchpad Test (`src/functions/touchpad.py`)
- Testa arrasto para esquerda/direita
- Testa clique botão esquerdo/meio/direito
- Testa scroll para cima/baixo
- Interface visual integrada ao padrão do sistema

### Camera Test (`src/functions/camera.py`)
- Inicializa câmera/webcam
- Captura preview em tempo real
- Tira foto para validação
- Suporte para upload SMB (opcional)

## ⚙️ Dependências

Certifique-se de que as seguintes dependências estão instaladas:

```bash
pip install pygame opencv-python numpy
```

## 🚀 Como Usar

1. Execute o script SQL para adicionar as colunas no banco de dados
2. Execute o `alltests.py` normalmente
3. Durante o cadastro, responda às novas perguntas sobre WiFi, Touchpad e Câmera
4. Os testes serão executados automaticamente no fluxo

## ✅ Checklist de Validação

- [ ] Script SQL executado no banco de dados
- [ ] Dependências Python instaladas (pygame, opencv-python, numpy)
- [ ] Cadastro de novo dispositivo com as novas perguntas
- [ ] Teste de WiFi funcionando
- [ ] Teste de Touchpad funcionando
- [ ] Teste de Câmera funcionando
- [ ] Logs sendo salvos corretamente

## 📊 Compatibilidade

- **Sistema Operacional**: Linux (Ubuntu/Debian)
- **Python**: 3.8+
- **Banco de Dados**: MySQL 5.7+

## 🐛 Troubleshooting

### Erro ao importar módulos
```bash
pip install -r requirements.txt
```

### Erro no banco de dados
Verifique se as colunas foram criadas:
```sql
DESCRIBE devices;
```

### WiFi não detectado
Verifique se o sistema possui interface wireless:
```bash
iw dev
# ou
ip link show
```

### Câmera não detectada
Verifique dispositivos de vídeo:
```bash
ls /dev/video*
```

---

**Data da Atualização**: 17 de Fevereiro de 2026  
**Versão**: 2.0  
**Autor**: Sistema revy-check
