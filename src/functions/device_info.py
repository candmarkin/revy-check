from src import api_client, hal
from src.functions.cadastro import cadastro_portas


class DeviceNotRegistered(Exception):
    """O modelo lido do DMI nao existe no catalogo."""


def fetch_device_info(max_cadastros=1):
    """Config do device, cadastrando o modelo se ele ainda nao existir.

    O cadastro roda no maximo `max_cadastros` vezes: antes isto se chamava de
    volta sem limite, entao cadastro cancelado ou com erro recursava ate'
    estourar a pilha.
    """
    for tentativa in range(max_cadastros + 1):
        try:
            return _fetch_device_info_once()
        except DeviceNotRegistered as exc:
            if tentativa >= max_cadastros:
                raise
            print(exc)
            cadastro_portas()

    raise DeviceNotRegistered("cadastro do device nao concluido")


def _fetch_device_info_once():
    manufacturer, productname = hal.dmi()
    vendor = hal.cpu_vendor()

    try:
        dados = api_client.buscar_modelo(productname, vendor, hal.PLATFORM)
    except api_client.ModeloNaoCadastrado as exc:
        raise DeviceNotRegistered(str(exc)) from exc

    for aviso in dados.get("avisos", []):
        print(f"AVISO: {aviso}")

    print(
        f"Device ID for '{productname}' (CPU {vendor or '?'}, "
        f"{hal.PLATFORM}): {dados['device_id']}"
    )

    features = dados.get("features", {})
    port_map = [(p["bus"], p["port"], p["label"]) for p in dados.get("port_map", [])]
    video_ports = [
        {"label": v["label"], "entry": v["entry"]} for v in dados.get("video_ports", [])
    ]

    return {
        "MANUFACTURER": manufacturer,
        "PRODUCT_NAME": dados.get("product_name") or productname,
        "CPU_VENDOR": vendor,
        "PORT_MAP": port_map,
        "VIDEO_PORTS": video_ports,
        "HAS_EMBEDDED_SCREEN": features.get("has_embedded_screen", False),
        "HAS_EMBEDDED_KEYBOARD": features.get("has_embedded_keyboard", False),
        # A coluna no banco sempre se chamou `has_ethernet`. O codigo antigo
        # lia `has_ethernet_port`, que nao existe, entao a chave caia no
        # default `False` e o teste de rede nunca rodava -- em nenhum dos 89
        # equipamentos cadastrados.
        "HAS_ETHERNET_PORT": features.get("has_ethernet", False),
        "ETH_INTERFACE": dados.get("eth_interface") or "",
        "HAS_SPEAKER": features.get("has_speaker", False),
        "HAS_HEADPHONE_JACK": features.get("has_headphone_jack", False),
        "HAS_MICROPHONE": features.get("has_microphone", False),
        "HAS_WIFI": features.get("has_wifi", False),
        "HAS_TOUCHPAD": features.get("has_touchpad", False),
        "HAS_CAMERA": features.get("has_camera", False),
    }
