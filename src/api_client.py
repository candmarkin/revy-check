"""Cliente dos endpoints /revy-check/* da API Revy.

Substitui o acesso direto ao MySQL. O agente roda na bancada, na máquina já
com a imagem do cliente, e é distribuído como binário — falar com o banco
exigia embutir a credencial do MySQL no executável. Agora carrega só uma chave
de API que abre três rotas e é revogável sem rebuild.
"""

import requests

from src import config


class ApiError(RuntimeError):
    """Falha de comunicação ou erro devolvido pela API."""


class ModeloNaoCadastrado(ApiError):
    """404 do /buscamodelo: o equipamento ainda não existe no catálogo."""


def _post(rota, payload, timeout=None):
    url = f"{config.api_url()}/{rota}"
    try:
        resposta = requests.post(
            url,
            json=payload,
            headers={"X-API-KEY": config.api_key()},
            timeout=timeout or config.api_timeout(),
        )
    except requests.RequestException as exc:
        raise ApiError(f"Sem resposta de {url}: {type(exc).__name__}") from exc

    if resposta.status_code == 404:
        raise ModeloNaoCadastrado(_detalhe(resposta))
    if resposta.status_code == 401:
        raise ApiError("Chave de API recusada. Confira REVYCHECK_API_KEY.")
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
    """True se a API responde e aceita a chave.

    Usado na espera por rede do início do fluxo. Um `buscamodelo` com nome
    vazio devolve 404 (modelo inexistente), que já prova que a rota respondeu
    e autenticou — sem escrever nada.
    """
    try:
        buscar_modelo("", "", "")
    except ModeloNaoCadastrado:
        return True
    except ApiError:
        return False
    return True
