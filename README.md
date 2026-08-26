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

## Instalação (Windows 10/11)

Abra o PowerShell na pasta raiz do repositório e execute:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Fixe a versão do Python com `py -3.10`.** O `pygame` 2.6.1 não publica wheel
para Python 3.14, e num venv 3.14 o app morre com
`ModuleNotFoundError: No module named 'pygame.base'`. Se o `py -0p` mostrar o
3.14 como padrão (`*`), um `py -m venv` sem versão cai nessa armadilha.
Validado em 3.10.11; 3.11/3.12/3.13 também têm wheel.

Toda a detecção de hardware no Windows (USB, vídeo, áudio, rede, WiFi) usa
`ctypes`/`winreg` da biblioteca padrão — não há dependência específica de
plataforma além do que já está no `requirements.txt`.

Antes de rodar o app, confira o ambiente:

```powershell
python scripts\smoke_test.py
```

Duas coisas exigem privilégio de administrador e degradam sozinhas sem ele:
ajustar o relógio pelo NTP e alguns caminhos de rede. O resto funciona como
usuário normal.

### Configuração (obrigatória)

O agente não carrega segredo nenhum no código nem no binário. Copie o template
e preencha:

```powershell
copy revycheck.env.example revycheck.env
```

O arquivo fica **ao lado do executável** (ou na raiz do repo, em dev) e é lido
em tempo de execução. Variável de ambiente tem precedência. Sem
`REVYCHECK_API_KEY` o app não inicia.

A chave vem do `REVYCHECK_API_KEY` do `.env` de `Revy/apps/api`, e abre só as
rotas `/revy-check/*` — não é a chave mestra da API. Se um binário vazar,
rotaciona-se essa chave sozinha, editando um arquivo, sem rebuild.

`REVYCHECK_DEV_PASSWORD` vazio **desabilita o modo DEV**, que é o que se quer
numa bancada de produção: em DEV dá para aprovar teste na mão.

### Como o agente fala com o banco

Não fala. Toda persistência passa pela API Revy:

| Rota | Quando |
|---|---|
| `POST /revy-check/buscamodelo` | início, para saber portas e recursos do modelo |
| `POST /revy-check/cadastrar` | quando o modelo ainda não existe no catálogo |
| `POST /revy-check/testefinal` | no fim, com o log do checklist |

As rotas vivem em `Revy/apps/api` (`functions/revycheck.py` + o
`router_revycheck` no `main.py`).

### Cadastro de portas por sistema operacional

A mesma porta física tem nomes diferentes em cada SO (`0000:00:14.0/3.2` no
Linux, `PCIROOT(0)#PCI(1400)/3.2` no Windows), e as saídas de vídeo idem. Um
equipamento cadastrado na linha Debian **não** casa na linha Windows: cada
modelo precisa de um cadastro por SO.

A coluna `platform` já existe no banco (`scripts/add_platform_column.sql`, já
aplicada). O agente envia a plataforma em toda busca e todo cadastro, e a API
filtra por ela.

### Gerar o executável

```powershell
pyinstaller main.spec
```

O binário sai em `dist\RevyCheck.exe`. Leia a nota de segurança no topo do
`main.spec` antes de distribuir.

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
- Quando solicitado, digite a senha DEV (`REVYCHECK_DEV_PASSWORD` no `revycheck.env`).
- Sem essa variável preenchida o modo DEV fica **desabilitado**: a hotkey não destrava nada.

No modo DEV, o app permite fechar com ESC e salva o log antes de sair.

### Atalhos do modo DEV

| Atalho | O que faz |
|---|---|
| `Ctrl+Shift+A` | Aprova o passo atual e vai para o próximo |
| `Ctrl+Shift+J` | Abre o menu de passos e salta para o escolhido |
| `ESC` | Sai do app salvando o log |

Se o DEV já estiver ativo quando o fluxo começa, o menu de passos aparece logo
após a seleção do tipo de teste — dá para entrar direto no passo que interessa,
sem passar por tela, teclado, touchpad, wifi, câmera, USB, vídeo e áudio antes.
`ESC` no menu segue o fluxo normal, do começo.

Aprovação manual vai para o log como `DEV_APROVADO_<PASSO>`, e não com o nome
do passo real: uma execução aprovada na mão **não** pode ficar indistinguível
de uma que passou de verdade.

Os atalhos são inertes em PROD — as funções checam `app_state.MODE` e saem sem
fazer nada, então não há como um operador dispará-los na linha.

## Estrutura importante

- `src/main.py` — loop principal e orquestração dos estados de teste
- `src/hal/` — camada de hardware: a mesma API sobre Linux e Windows
  - `linux.py` — sysfs, procfs, `iw`/`nmcli`, PulseAudio
  - `windows.py` — cfgmgr32 (USB), CCD API (vídeo), registro (áudio/rede/DMI),
    wlanapi (WiFi), tudo por `ctypes`/`winreg`
  - o backend é escolhido por `sys.platform` no import; os steps de teste não
    sabem em qual SO estão rodando
- `src/config.py` — configuração e segredos, lidos do `revycheck.env`/ambiente
- `src/api_client.py` — cliente das rotas `/revy-check/*` da API Revy
- `src/functions/` — os passos do checklist e a interface
  - `device_info.py` — devolve configuração do equipamento (mapa de portas, flags)
  - `usb.py` — detecção de presença em portas USB
  - `video_ports.py` — checagem e desenho das saídas de vídeo
  - `audio.py` — reprodução de tons e detecção de headphone/microfone
  - `ethernet.py` — checagem de rede
  - `screen.py`, `keyboard.py`, `save_log.py`, `tab_lock.py` — utilitários
- `scripts/` — scripts auxiliares, migrações SQL e o smoke test
- `WINDOWS.md` — como o porte para Windows funciona, com o mapeamento de cada
  API e os pontos ainda em aberto

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