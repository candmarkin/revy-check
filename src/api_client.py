"""Cliente dos endpoints /revy-check/* da API Revy.

O agente não carrega segredo nenhum. Quem autentica é o técnico: `login()`
troca e-mail + senha do Revy web pela `key` do usuário, e as chamadas
seguintes vão com essa chave no header `X-USER-KEY`. A chave fica só em
memória, morre com o processo, e é revogável no cadastro do usuário.

Antes daqui havia uma chave de API compartilhada dentro do executável. Binário
distribuído acaba lido (`pyi-archive_viewer` extrai o bundle inteiro), então
aquela chave era pública na prática, e rotacionar exigia rebuild e
republicação em toda bancada.
"""

import requests

from src import config


class ApiError(RuntimeError):
    """Falha de comunicação ou erro devolvido pela API."""


class ModeloNaoCadastrado(ApiError):
    """404 do /buscamodelo: o equipamento ainda não existe no catálogo."""


class NaoAutenticado(ApiError):
    """401: sem login, ou a chave do usuário foi revogada no cadastro."""


class CredenciaisInvalidas(ApiError):
    """401 do /login: e-mail ou senha errados."""


class LoginBloqueado(ApiError):
    """429 do /login: tentativas demais para o mesmo e-mail."""


# Sessão do turno. Só memória: nada de chave em disco, nem no log, nem no
# `revycheck.env`. Fecha o app, acabou a sessão.
_sessao = {"key": None, "name": None, "role": None, "id": None}


def usuario():
    """Quem está logado, ou None."""
    return dict(_sessao) if _sessao["key"] else None


def encerrar_sessao():
    _sessao.update({"key": None, "name": None, "role": None, "id": None})


def login(email, senha):
    """Troca e-mail + senha do Revy pela chave do usuário e abre a sessão.

    A senha passa uma vez, no login, e não é guardada em lugar nenhum. O que
    fica é a `key`, que a API valida nas chamadas seguintes.
    """
    resposta = _post("login", {"email": email, "senha": senha}, autenticado=False)
    chave = resposta.get("key")
    if not chave:
        raise ApiError("Login sem chave na resposta: API desatualizada?")
    _sessao.update({
        "key": chave,
        "name": resposta.get("name") or email,
        "role": resposta.get("role") or "",
        "id": resposta.get("id"),
    })
    return usuario()


def _post(rota, payload, timeout=None, autenticado=True):
    url = f"{config.api_url()}/{rota}"
    headers = {}
    if autenticado:
        if not _sessao["key"]:
            raise NaoAutenticado("Sem login nesta sessão.")
        headers["X-USER-KEY"] = _sessao["key"]

    try:
        resposta = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout or config.api_timeout(),
        )
    except requests.RequestException as exc:
        raise ApiError(f"Sem resposta de {url}: {type(exc).__name__}") from exc

    if resposta.status_code == 404:
        raise ModeloNaoCadastrado(_detalhe(resposta))
    if resposta.status_code == 429:
        raise LoginBloqueado(_detalhe(resposta))
    if resposta.status_code == 401:
        # No /login é credencial errada; nas outras rotas é sessão inválida --
        # chave revogada, ou o app chamou antes de logar.
        if rota == "login":
            raise CredenciaisInvalidas(_detalhe(resposta))
        encerrar_sessao()
        raise NaoAutenticado(_detalhe(resposta))
    if not resposta.ok:
        raise ApiError(f"HTTP {resposta.status_code}: {_detalhe(resposta)}")

    try:
        return resposta.json()
    except ValueError as exc:
        raise ApiError(f"Resposta não-JSON de {url}") from exc


def _detalhe(resposta):
    try:
        corpo = resposta.json()
    except ValueError:
        return resposta.text[:200]
    detalhe = corpo.get("detail", corpo) if isinstance(corpo, dict) else corpo
    return str(detalhe)[:300]


def buscar_modelo(product_name, cpu_vendor, platform):
    """Configuração do equipamento. Levanta ModeloNaoCadastrado se for novo."""
    return _post("buscamodelo", {
        "product_name": product_name,
        "cpu_vendor": cpu_vendor,
        "platform": platform,
    })


def cadastrar_modelo(product_name, cpu_vendor, platform, features,
                     eth_interface, port_map, video_ports, tipo="Notebook"):
    return _post("cadastrar", {
        "product_name": product_name,
        "cpu_vendor": cpu_vendor,
        "platform": platform,
        "type": tipo,
        "eth_interface": eth_interface,
        "features": features,
        "port_map": port_map,
        "video_ports": video_ports,
    })


def enviar_teste_final(device_serial, entries):
    """Grava o log do checklist. A API insere tudo numa transação só.

    Isso é o que torna o retry seguro: uma tentativa que falhe no meio não
    deixa metade dos passos gravados para a próxima duplicar.
    """
    return _post("testefinal", {
        "device_serial": device_serial,
        "entries": [
            {
                "step": e.get("step", ""),
                "time": str(e.get("time", "")),
                "result": e.get("result", "REPROVADO"),
            }
            for e in entries
        ],
    })


def disponivel():
    """True se a API responde. Não exige login, e não escreve nada.

    É a espera por rede do início do fluxo, que roda ANTES do login: manda um
    `/login` vazio e aceita qualquer resposta HTTP como sinal de vida. A API
    devolve 401 para credencial vazia, e 401 já prova que ela respondeu.

    Antes isto era um `buscamodelo` com nome vazio -- que agora exige sessão, e
    sessão é o que ainda não existe nesse ponto do fluxo.
    """
    try:
        _post("login", {"email": "", "senha": ""}, autenticado=False)
    except (CredenciaisInvalidas, LoginBloqueado, ModeloNaoCadastrado):
        return True
    except ApiError:
        return False
    return True
