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

### Login do técnico (é o que autentica)

O agente não carrega segredo nenhum — nem no código, nem no binário, nem em
arquivo ao lado dele. Ao abrir, ele pede **e-mail e senha do Revy web**, a
mesma credencial que o técnico já usa. A API valida contra `users.password`
(bcrypt, o mesmo hash do NextAuth) e devolve a `key` do usuário; o agente manda
essa chave em `X-USER-KEY` nas chamadas seguintes, e a guarda **só em
memória** — fecha o app, acabou a sessão.

```
POST /revy-check/login   {email, senha}  ->  {id, name, role, key}
POST /revy-check/*       header X-USER-KEY: <key do usuário>
```

O que isso resolve:

- **Executável sem segredo.** Pode ficar numa pasta pública: extrair o bundle
  não rende nada. Era o oposto com a chave compartilhada de antes.
- **Revogação por pessoa**, no cadastro do usuário, sem tocar em bancada e sem
  rebuild. Chave compartilhada exigia republicar em toda bancada.
- **Autoria no log.** `/testefinal` grava quem estava logado
  (`scripts/add_logs_user_columns.sql`). Importa porque o modo DEV permite
  aprovar teste na mão — antes o log não dizia quem aprovou.
- Cinco senhas erradas para o mesmo e-mail bloqueiam o login por 5 minutos
  (`functions/auth.py` na API).

Se a chave for revogada no meio do turno, o envio do log volta para a tela de
login e continua de onde parou — o checklist não é perdido.

### Configuração (opcional)

```powershell
copy revycheck.env.example revycheck.env
```

Nada aqui é obrigatório: sem arquivo nenhum o agente fala com a API de
produção (`DEFAULT_API_URL`). O arquivo serve para apontar outra URL, ajustar
timeout, habilitar o modo DEV e configurar o SMB das fotos.

O único segredo que ainda sobra na bancada é `REVYCHECK_SMB_*` — credencial de
servidor de arquivos. Enquanto ela estiver no `revycheck.env`, o arquivo precisa
de ACL; use conta de serviço com escrita só na pasta de fotos, nunca conta
pessoal. Vazio desliga o envio, e o teste de câmera continua rodando.

O modo DEV **não tem mais senha**: quem destrava é o papel do usuário logado
(`role == "admin"`). Não há nada a configurar aqui.

### Como o agente fala com o banco

Não fala. Toda persistência passa pela API Revy:

| Rota | Quando | Autenticação |
|---|---|---|
| `POST /revy-check/login` | ao abrir o app | nenhuma (é a porta de entrada) |
| `POST /revy-check/buscamodelo` | início, para saber portas e recursos do modelo | `X-USER-KEY` |
| `POST /revy-check/cadastrar` | quando o modelo ainda não existe no catálogo | `X-USER-KEY` |
| `POST /revy-check/testefinal` | no fim, com o log do checklist | `X-USER-KEY` |

As rotas vivem em `Revy/apps/api` (`functions/revycheck.py`, `functions/auth.py`
e o `router_revycheck` no `main.py`). Depois de trocar a autenticação, a API
precisa de `pip install -e .` (dependência nova: `bcrypt`) e restart.

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
python scripts\verificar_bundle.py
```

O binário sai em `dist\RevyCheck.exe` (~70 MB, um arquivo só). O
`verificar_bundle.py` abre o bundle (CArchive + PYZ) e procura os **valores**
do seu `revycheck.env` dentro dele — inclusive em docstring e comentário, que
viajam no `.pyc`. Sai com código 1 se algo vazou. Rode antes de publicar.

O `revycheck.env` **não entra no bundle** — de propósito, e o `main.spec`
explica por quê: `pyi-archive_viewer dist\RevyCheck.exe` extrai tudo que foi
empacotado, então segredo compilado é segredo publicado.

### Distribuir: um `.exe` só, numa pasta pública

A pasta pública guarda **apenas o `RevyCheck.exe`**, e agora isso é seguro por
construção: o binário não tem segredo dentro. Quem autoriza é o login do
técnico, então extrair o bundle (`pyi-archive_viewer dist\RevyCheck.exe`) não
rende nada além de código.

Sem `revycheck.env` em lugar nenhum o agente usa a URL de produção e funciona.
Quando existir arquivo, ele é procurado nesta ordem (`src/config.py`,
`candidatos()`):

| Ordem | Lugar | Quando usar |
|---|---|---|
| 1 | `%REVYCHECK_ENV%` (caminho de arquivo) | teste, bancada fora do padrão |
| 2 | `%PROGRAMDATA%\RevyCheck\revycheck.env` | provisionar por máquina |
| 3 | `CONFIG_SHARE` compilado em `config.py` | share com ACL, zero setup por bancada |
| 4 | ao lado do `.exe` | dev, e bancada com pasta própria |

Variável de ambiente do processo vence qualquer arquivo. A pasta do executável
é a **última** de propósito: pasta pública é gravável por muita gente, e um
`revycheck.env` plantado ali apontaria o agente para outra API.

**ACL só faz falta enquanto `REVYCHECK_SMB_*` estiver preenchido** — é o último
segredo da bancada. Nesse caso use `CONFIG_SHARE` (opção 3) ou `ProgramData`
(opção 2) com permissão de leitura restrita:

```powershell
icacls \\srv-arquivos\revycheck$\revycheck.env /inheritance:r ^
  /grant:r "DOMINIO\Administradores:(F)" ^
  /grant:r "DOMINIO\Tecnicos-Bancada:(R)"
```

Com o SMB vazio (ou depois que o upload da foto passar pela API), o
`revycheck.env` só tem endereço e timeout: pode ficar na pasta pública ao lado
do `.exe`, sem ACL, ou não existir.

O modo DEV é liberado por `role == "admin"` do usuário logado, e cada liberação
entra no log do checklist com nome e papel — importa porque em DEV dá para
aprovar teste na mão.

### O que o técnico vê

- **Tela de login** ao abrir: e-mail e senha do Revy. Senha errada avisa na
  hora; API fora do ar mostra o motivo e a URL tentada, em vez de fechar
  calado.
- **Pasta somente-leitura**: normal. A cópia local do log
  (`checklist_log.json`) falha com aviso e o envio para a API continua; as
  fotos da câmera vão para `%TEMP%\revy_photos`.
- **Primeiro clique é lento**: onefile desempaca ~70 MB em `%TEMP%\_MEIxxxx` a
  cada execução (~7 s local, mais em SMB). Se incomodar, builde em `onedir` e
  publique a pasta.
- **Aviso de segurança do Windows** ao abrir `.exe` de caminho UNC: adicione o
  share à zona de Intranet local, ou copie para a máquina.
- **Para matar o app**: encerre a **árvore** de processos. Onefile roda como
  bootloader + filho; matar só o pai deixa o filho vivo, ainda com o hook de
  teclado instalado (`taskkill /IM RevyCheck.exe /T /F`).
- **Diagnóstico rápido** de qual arquivo o app leu:
  `python scripts\smoke_test.py` — a primeira linha (`config`) mostra o caminho
  em uso, a URL e se o DEV está habilitado, sem imprimir valor nenhum.

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

O app sempre inicia em `MODE = "PROD"`. Quem destrava o DEV é o **papel do
usuário logado**, não uma senha:

- Hotkey: Ctrl (esq) + Shift (esq) + `d` + `v`.
- Se o `role` do usuário estiver em `ROLES_DEV` (`src/functions/dev_mode.py`,
  hoje `("admin",)`), o DEV liga e a tela confirma `DEV liberado: <nome>`.
- Qualquer outro papel vê `DEV negado: <nome> (<papel>)` e continua em PROD.
- Cada liberação entra no log do checklist (`step: DEV_MODE`) com nome e papel.

`--dev` na linha de comando é **pedido, não permissão**: o flag é resolvido
depois do login, pelo mesmo `role`. Sem isso, um atalho com `--dev` na bancada
daria DEV a qualquer um que clicasse nele.

Por que papel e não senha: senha de DEV era compartilhada, ficava em arquivo na
bancada e circulava entre turnos — e o teste de teclado destravava o DEV **sem
pedir senha nenhuma** (`keyboard.py`). Papel se revoga no cadastro do usuário,
sem tocar em bancada. Para incluir supervisor, é uma linha: `ROLES_DEV =
("admin", "supervisor")`.

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