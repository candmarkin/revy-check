# Revy Check

Checklist técnico interativo para validar hardware embarcado (USB, vídeo, áudio, ethernet, teclado, tela).

Este projeto implementa uma aplicação em Pygame que guia um operador por uma sequência de testes e registra os eventos em um log.

## Principais funcionalidades

- Teste de portas USB (conectar/remover pendrives)
- Teste de saídas de vídeo (detecção e desenho das saídas)
- Teste de áudio: headphone, speaker e microfone (sons / bipes)
- Teste de rede (Ethernet)
- Suporte a tela e teclado embutidos
- Registro de eventos em arquivo através de `save_log()`

## Requisitos

- Windows 10/11 (testado neste projeto) — instruções anteriores
- Debian (minimal) — instruções específicas abaixo
- Python 3.10+ (compatível com 3.11/3.12)
- Biblioteca: `pygame`

É recomendado criar um ambiente virtual antes de instalar dependências.

## Instalação (PowerShell)

Abra o PowerShell na pasta raiz do repositório e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install pygame
```

Observação: o repositório atualmente não inclui um `requirements.txt`. Se você adicionar dependências extras, atualize este README.

## Instalação (Debian minimal)

Debian minimal normalmente não inclui bibliotecas nativas necessárias para compilar/runar o `pygame`. Execute os passos abaixo como root ou com `sudo`.

1) Atualize os pacotes e instale dependências de sistema (pacotes comuns necessários para pygame e compilação de extensões C):

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
  libasound2-dev libpulse-dev libfreetype6-dev libjpeg-dev libsndfile1 \
  libjpeg62-turbo-dev
```

Observação: esta lista cobre dependências comuns que permitem compilar/instalar `pygame` via pip. Em distribuições muito enxutas algumas bibliotecas podem variar; ajuste conforme necessário.

2) Criar e ativar um ambiente virtual, atualizar pip e instalar `pygame`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install pygame
```

3) Executar o projeto:

```bash
python3 src/main.py
```

Se ocorrerem erros ao instalar o `pygame` via pip, verifique as mensagens de compilação e instale os pacotes de -dev correspondentes (por exemplo `libavcodec-dev`, `libsdl2-dev`, etc.).

## Como executar

Rode o script a partir da raiz do repositório (as importações assumem a estrutura de pastas atual):

```powershell
python src\main.py
```

Ou em Linux/Debian:

```bash
python3 src/main.py
```

Ao iniciar, uma janela Pygame abrirá e orientará o operador passo a passo pelos testes.

## Fluxo de testes (resumido)

1. Tela embutida (se disponível)
2. Teclado embutido (se disponível)
3. Teste de cada porta USB definida pela configuração (conectar -> remover)
4. Teste de vídeo
5. Teste de headphone (conectar / remover)
6. Teste de speaker
7. Teste de microfone
8. Teste de ethernet
9. Fim e geração de log

O fluxo principal está em `src/main.py` e as responsabilidades específicas ficam em `src/functions/`.

## Modo DEV

Por padrão o aplicativo inicia com `MODE = "PROD"` em `src/main.py`.

- Para destravar o modo DEV durante a execução, pressione a hotkey: Ctrl (esq) + Shift (esq) + d + v
- Quando solicitado, digite a senha DEV (valor padrão: `dev123` em `src/main.py`).

No modo DEV, o app permite fechar com ESC e salva o log antes de sair.

## Estrutura importante

- `src/main.py` — loop principal e orquestração dos estados de teste
- `src/functions/` — módulos auxiliares (detecção de hardware, áudio, vídeo, ethernet e utilitários)
  - `fetch_device_info.py` — devolve configuração da plataforma (mapa de portas, flags)
  - `usb.py` — detecção de presença em portas USB
  - `video_ports.py` — checagem e desenho das saídas de vídeo
  - `audio.py` — reprodução de tons e detecção de headphone/microfone
  - `ethernet.py` — checagem de rede
  - `screen.py`, `keyboard.py`, `save_log.py`, `tab_lock.py` — utilitários
- `scripts/` — scripts auxiliares para testes e manutenção

## Logs

Os eventos são acumulados na variável `log_data` durante a execução. Ao finalizar, `save_log()` grava esses eventos em arquivo (ver `src/functions/save_log.py`).

## Debug / desenvolvimento

- Execute a partir da raiz do repositório para evitar problemas de importação.
- Use a hotkey para entrar em modo DEV e facilitar testes interativos.

## Próximos passos recomendados

- Incluir testes automatizados e configurar CI
- Adicionar um `LICENSE` se desejar publicar o projeto com termos claros

## Contribuição e contato

Abra uma issue para dúvidas ou envie um pull request com melhorias.

---

Arquivo atualizado: documentação ampliada com instruções para Debian minimal.