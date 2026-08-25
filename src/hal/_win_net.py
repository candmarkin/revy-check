"""Interfaces de rede no Windows, equivalente ao `/sys/class/net` do Linux.

A lista de adaptadores sai do registro (classe de rede), que diz o tipo de midia
e se o adaptador e' virtual; o estado do link (`carrier`) sai do `psutil`.

`*IfType`            6 = Ethernet 802.3, 71 = IEEE 802.11
`*PhysicalMediaType` 14 = 802.3, 9 = Native 802.11, 10 = Bluetooth
`*NdisDeviceType`    1 = endpoint virtual (VPN, host-only, loopback)
"""

import winreg

_CLASS_KEY = (
    r"SYSTEM\CurrentControlSet\Control\Class"
    r"\{4d36e972-e325-11ce-bfc1-08002be10318}"
)
_NETWORK_KEY = (
    r"SYSTEM\CurrentControlSet\Control\Network"
    r"\{4d36e972-e325-11ce-bfc1-08002be10318}"
)

IF_TYPE_ETHERNET = 6
IF_TYPE_WIRELESS = 71

MEDIA_802_3 = 14
MEDIA_NATIVE_802_11 = 9

# Adaptadores virtuais que se declaram Ethernet fisica. Nao da' para separar
# pelo registro: um cliente VPN registra `*PhysicalMediaType` 14 e
# `*NdisDeviceType` 0, igual a uma placa de verdade.
_VIRTUAL_HINTS = (
    "virtual",
    "vpn",
    "tap-",
    "tun",
    "loopback",
    "wan miniport",
    "kernel debug",
    "hyper-v",
    "vmware",
    "virtualbox",
    "wintun",
    "wireguard",
    "tailscale",
    "npcap",
    "teredo",
    "6to4",
    "wi-fi direct",
    "hosted network",
    "microsoft wi-fi",
)


def _value(key, name, default=None):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return default


def _connection_name(guid):
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, rf"{_NETWORK_KEY}\{guid}\Connection"
        ) as key:
            return _value(key, "Name")
    except OSError:
        return None


def _adapters():
    """[(nome da conexao, descricao do driver, if_type, media, ndis_type)]."""
    found = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _CLASS_KEY)
    except OSError:
        return found

    with root:
        index = 0
        while True:
            try:
                sub = winreg.EnumKey(root, index)
            except OSError:
                break
            index += 1
            if not sub.isdigit():
                continue

            try:
                with winreg.OpenKey(root, sub) as key:
                    guid = _value(key, "NetCfgInstanceId")
                    if not guid:
                        continue
                    found.append(
                        (
                            _connection_name(guid),
                            _value(key, "DriverDesc", ""),
                            _value(key, "*IfType"),
                            _value(key, "*PhysicalMediaType"),
                            _value(key, "*NdisDeviceType", 0),
                        )
                    )
            except OSError:
                continue
    return [a for a in found if a[0]]


def _present_names():
    """Nomes de conexao que o SO reporta agora.

    O registro guarda tambem adaptadores ja' removidos; sem este filtro o
    cadastro ofereceria placas que nao estao mais na maquina.
    """
    try:
        import psutil

        return set(psutil.net_if_stats())
    except Exception:
        return None


def _looks_virtual(description):
    lowered = (description or "").lower()
    return any(hint in lowered for hint in _VIRTUAL_HINTS)


def _filter(if_type, media):
    present = _present_names()
    interfaces = []
    for name, description, adapter_type, adapter_media, ndis_type in _adapters():
        if adapter_type != if_type or adapter_media != media:
            continue
        if ndis_type == 1 or _looks_virtual(description):
            continue
        if present is not None and name not in present:
            continue
        interfaces.append((name, description))
    return sorted(interfaces)


def ethernet_interfaces():
    return _filter(IF_TYPE_ETHERNET, MEDIA_802_3)


def wifi_interfaces():
    return _filter(IF_TYPE_WIRELESS, MEDIA_NATIVE_802_11)


def link_up(interface):
    """Equivalente do `/sys/class/net/<if>/carrier`.

    O Windows derruba o status operacional do adaptador assim que o cabo sai,
    entao `isup` e' o mesmo sinal que o carrier do kernel.
    """
    try:
        import psutil

        stats = psutil.net_if_stats().get(interface)
    except Exception:
        return False
    return bool(stats and stats.isup)


def primary_ip():
    try:
        import socket

        import psutil
    except Exception:
        return "N/A"

    candidates = []
    for name, addrs in psutil.net_if_addrs().items():
        stats = psutil.net_if_stats().get(name)
        if not stats or not stats.isup:
            continue
        for addr in addrs:
            if addr.family != socket.AF_INET:
                continue
            ip = addr.address
            # 127.x e' loopback e 169.254.x e' APIPA: endereco de quem nao
            # conseguiu DHCP, que nao ajuda a identificar a maquina na rede.
            if ip.startswith(("127.", "169.254.")):
                continue
            candidates.append(ip)
    return candidates[0] if candidates else "N/A"
