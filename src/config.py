"""Configuração do agente. Nenhum segredo literal aqui.

Os valores vêm, nesta ordem de precedência:

1. variável de ambiente;
2. arquivo `revycheck.env` ao lado do executável (ou na raiz do repo, em dev);
3. o default, quando existir um que não seja segredo.

O arquivo ao lado do executável é o que serve à bancada: o app é distribuído
como binário num compartilhamento de rede, e um binário distribuído acaba
lido. Chave em arquivo se rotaciona editando um arquivo; chave compilada se
rotaciona rebuildando e republicando em toda bancada.

Formato do arquivo, uma chave por linha:

    REVYCHECK_API_URL=http://revy.selbetti.com.br:8000/revy-check
    REVYCHECK_API_KEY=...
"""

import os
import sys
from pathlib import Path

CONFIG_FILENAME = "revycheck.env"

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


def _carregar_arquivo():
    global _arquivo
    if _arquivo is not None:
        return _arquivo

    _arquivo = {}
    caminho = base_dir() / CONFIG_FILENAME
    if not caminho.is_file():
        return _arquivo

    for linha in caminho.read_text(encoding="utf-8").splitlines():
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


def obrigatorio(nome):
    """Valor que não tem default seguro. Sem ele o app não deve iniciar."""
    valor = get(nome)
    if not valor:
        raise ConfigAusente(
            f"{nome} não configurado.\n\n"
            f"Defina em {base_dir() / CONFIG_FILENAME} ou como variável de "
            f"ambiente. Veja revycheck.env.example."
        )
    return valor


class ConfigAusente(RuntimeError):
    """Falta configuração para o app funcionar."""


# --------------------------------------------------------------------- API


def api_url():
    return get("REVYCHECK_API_URL", DEFAULT_API_URL).rstrip("/")


def api_key():
    return obrigatorio("REVYCHECK_API_KEY")


def api_timeout():
    try:
        return float(get("REVYCHECK_API_TIMEOUT", "15"))
    except ValueError:
        return 15.0


# --------------------------------------------------------------------- SMB


def smb_config():
    """Destino das fotos da câmera. Vazio desliga o envio."""
    return {
        "server": get("REVYCHECK_SMB_HOST", ""),
        "share": get("REVYCHECK_SMB_SHARE", ""),
        "username": get("REVYCHECK_SMB_USER", ""),
        "password": get("REVYCHECK_SMB_PASSWORD", ""),
        "remote_path": get("REVYCHECK_SMB_PATH", ""),
    }


# --------------------------------------------------------------------- DEV


def dev_password():
    """Senha do modo DEV. Sem ela configurada, o modo DEV fica indisponível.

    O default antigo era 'dev123' no código: qualquer um que lesse o fonte (ou
    extraísse o binário) destravava o DEV na bancada e aprovava teste na mão.
    """
    return get("REVYCHECK_DEV_PASSWORD", "")
