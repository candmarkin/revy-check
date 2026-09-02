"""Configuração do agente. Nenhum segredo literal aqui.

Os valores vêm, nesta ordem de precedência:

1. variável de ambiente;
2. arquivo `revycheck.env`, no primeiro destes lugares que existir:
   `%REVYCHECK_ENV%`, `%PROGRAMDATA%\RevyCheck\`, o `CONFIG_SHARE` compilado,
   a pasta do executável (que em dev é a raiz do repo);
3. o default, quando existir um que não seja segredo.

Arquivo, e não literal no código: o app é distribuído como binário para as
bancadas, e binário distribuído acaba lido (`pyi-archive_viewer` extrai o
bundle inteiro). Chave em arquivo se rotaciona editando um arquivo; chave
compilada se rotaciona rebuildando e republicando em toda bancada.

A pasta do executável é o último lugar da lista de propósito. Quando o `.exe`
fica numa pasta pública, essa pasta é gravável por muita gente, e um
`revycheck.env` plantado ali apontaria o agente para outra API.

Formato do arquivo, uma chave por linha. Nada aqui é segredo: o técnico
autentica com a credencial dele no login, e o agente não guarda chave.

    REVYCHECK_API_URL=http://revy.selbetti.com.br:8000/revy-check
    REVYCHECK_API_TIMEOUT=15
"""

import os
import sys
from pathlib import Path

CONFIG_FILENAME = "revycheck.env"

# Caminho do arquivo de config numa pasta de acesso restrito, compilado no
# binário. Serve ao caso "um .exe só, numa pasta pública": a pasta pública
# guarda o executável e mais nada, e a chave mora num share com ACL, que só a
# conta do técnico lê. Caminho não é segredo -- quem chega no share sem
# permissão não lê o arquivo, e quem tem permissão não precisa do caminho
# escondido. Vazio desliga esta etapa da busca.
#
#     CONFIG_SHARE = r"\\srv-arquivos\revycheck$\revycheck.env"
CONFIG_SHARE = ""

# Sobrescreve tudo, para teste e para bancada fora do padrão:
#     set REVYCHECK_ENV=D:\config\revycheck.env
CONFIG_PATH_VAR = "REVYCHECK_ENV"

DEFAULT_API_URL = "http://revy.selbetti.com.br:8000/revy-check"

_arquivo = None


def base_dir():
    """Diretório do executável, ou a raiz do repo quando rodando do fonte.

    `sys.frozen` é o que o PyInstaller/Nuitka marcam no binário congelado;
    `sys.executable` aponta para o .exe, e não para o python.exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def candidatos():
    """Onde procurar o arquivo, na ordem. O primeiro que existir vence.

    A ordem serve à bancada, não ao desenvolvimento: config gerenciada pela
    máquina (ProgramData) ou pelo share com ACL ganha de um `revycheck.env`
    largado ao lado do `.exe` -- se o executável mora numa pasta pública,
    qualquer um escreve nessa pasta, e um arquivo plantado ali redirecionaria
    o agente para outra API.
    """
    caminho = os.environ.get(CONFIG_PATH_VAR)
    if caminho:
        yield Path(caminho)

    program_data = os.environ.get("PROGRAMDATA")
    if program_data:
        yield Path(program_data) / "RevyCheck" / CONFIG_FILENAME

    if CONFIG_SHARE:
        yield Path(CONFIG_SHARE)

    yield base_dir() / CONFIG_FILENAME


def arquivo_em_uso():
    """Primeiro candidato que existe, ou None. Só para mensagem de erro."""
    for caminho in candidatos():
        try:
            if caminho.is_file():
                return caminho
        except OSError:
            continue  # share fora do ar, caminho inválido: segue a lista
    return None


def _carregar_arquivo():
    global _arquivo
    if _arquivo is not None:
        return _arquivo

    _arquivo = {}
    caminho = arquivo_em_uso()
    if caminho is None:
        return _arquivo

    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Nao foi possivel ler {caminho}: {exc}")
        return _arquivo

    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        _arquivo[chave.strip()] = valor.strip().strip('"').strip("'")
    return _arquivo


def get(nome, default=None):
    valor = os.environ.get(nome)
    if valor:
        return valor
    return _carregar_arquivo().get(nome) or default


# Nada aqui é obrigatório. O agente não tem mais segredo para carregar: quem
# autentica é o login do técnico (`api_client.login`), e a URL tem default.
# Um `.exe` sem `revycheck.env` nenhum sobe e fala com a API de produção.


# --------------------------------------------------------------------- API


def api_url():
    return get("REVYCHECK_API_URL", DEFAULT_API_URL).rstrip("/")


def api_timeout():
    try:
        return float(get("REVYCHECK_API_TIMEOUT", "15"))
    except ValueError:
        return 15.0


# --------------------------------------------------------------------- DEV
#
# Nao ha' senha de DEV. Quem libera e' o `role` do usuario logado
# (`functions.dev_mode.ROLES_DEV`), que vem da API no login. A senha antiga era
# compartilhada, ficava em arquivo na bancada, e o valor original ainda esta no
# historico do git -- alem de o teste de teclado destravar o DEV sem pedir
# senha nenhuma.
