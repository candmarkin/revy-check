"""Portas USB fisicas no Windows, equivalente ao `/sys/bus/usb/devices` do Linux.

A identificacao vem de `DEVPKEY_Device_LocationPaths`, que descreve o caminho
fisico no device tree e nao a ordem de enumeracao:

    Linux    0000:00:14.0/3.2
    Windows  PCIROOT(0)#PCI(1400)#USBROOT(0)#USB(3)#USB(2)

O `Class=Mass Storage` (`bInterfaceClass == 08`) que o backend Linux procura
vira o servico `USBSTOR`, que fica no no' do dispositivo -- nao nas interfaces
filhas que o Windows cria para dispositivos compostos (`...&MI_00`).
"""

import time

from src.hal import _win_cfgmgr as cm

MASS_STORAGE_SERVICE = "USBSTOR"

# A enumeracao completa custa alguns milissegundos e o loop principal roda a
# 10 fps consultando a mesma porta. O TTL e' curto o bastante para o operador
# nao perceber e para o cadastro enxergar a remocao do pendrive.
_CACHE_TTL = 0.25
_cache = {"at": 0.0, "ports": {}}


def _port_id(location_paths):
    """('PCIROOT(0)#PCI(1400)', '3.2') a partir do location path do dispositivo.

    O controlador fica na parte PCI do caminho e a cadeia de portas nos
    segmentos `USB(n)`. O `USBROOT(0)` sai fora: e' o hub raiz do controlador,
    equivalente ao numero de bus que o backend Linux tambem descarta.
    """
    for path in location_paths or []:
        if "USBROOT" not in path:
            continue
        parts = path.split("#")
        controller = "#".join(p for p in parts if p.startswith(("PCIROOT(", "PCI(")))
        chain = ".".join(p[4:-1] for p in parts if p.startswith("USB("))
        if controller and chain:
            return controller, chain
    return None, None


def _acpi_panel(location_paths):
    """Ultimo no ACPI do caminho ('HS10'), a dica mais proxima do _PLD do Linux.

    O Windows nao expoe o painel do chassi como o `physical_location/panel` do
    kernel. Serve so' para o operador conferir no cadastro que rotulou a porta
    certa -- nao entra na identificacao.
    """
    for path in location_paths or []:
        if not path.startswith("ACPI("):
            continue
        leaf = path.split("#")[-1]
        if leaf.startswith("ACPI(") and leaf.endswith(")"):
            return leaf[5:-1].rstrip("_")
    return None


def _enumerate():
    """{port_id: (servico, painel, device_id)} de todas as portas USB ocupadas.

    As interfaces de um dispositivo composto (`...&MI_00`) compartilham a porta
    fisica do pai e entram no mesmo registro. Elas nao sao descartadas de
    proposito: em pendrive com emulacao de CD quem carrega o `USBSTOR` e' a
    interface, e o pai aparece como `USBCCGP`. Por isso o USBSTOR de qualquer
    no' da porta vence -- e' a leitura equivalente ao `bInterfaceClass` que o
    backend Linux faz nas interfaces, e nao no dispositivo.
    """
    ports = {}
    for device_id in cm.device_ids("USB"):
        devinst = cm.locate(device_id)
        if devinst is None:
            continue

        paths = cm.prop(devinst, cm.DEVPKEY_Device_LocationPaths)
        controller, chain = _port_id(paths)
        if not controller:
            continue

        port_id = f"{controller}/{chain}"
        service = (cm.prop(devinst, cm.DEVPKEY_Device_Service) or "").upper()
        known = ports.get(port_id)
        if known and known[0] == MASS_STORAGE_SERVICE:
            continue
        if known and service != MASS_STORAGE_SERVICE:
            continue  # mantem o primeiro no' visto; so' USBSTOR sobrescreve
        ports[port_id] = (service, _acpi_panel(paths), device_id)
    return ports


def all_ports(force=False):
    now = time.monotonic()
    if force or now - _cache["at"] > _CACHE_TTL:
        _cache["ports"] = _enumerate()
        _cache["at"] = now
    return _cache["ports"]


def mass_storage_ports(force=False):
    """{port_id: painel} das portas com um dispositivo de armazenamento."""
    return {
        port_id: panel
        for port_id, (service, panel, _) in all_ports(force).items()
        if service == MASS_STORAGE_SERVICE
    }


def is_physical_port_id(bus):
    """True se `bus` for um location path do Windows.

    Distingue dos cadastros do Linux ('0000:00:14.0') e dos legados
    ('Bus 002'), que nunca casariam com uma porta desta maquina.
    """
    return isinstance(bus, str) and bus.startswith("PCIROOT(")


def topology():
    """Linhas no espirito do `lsusb -t`, para o overlay do modo DEV."""
    lines = []
    for port_id, (service, panel, device_id) in sorted(all_ports().items()):
        panel_hint = f" [{panel}]" if panel else ""
        lines.append(f"{port_id}{panel_hint}  Service={service or '-'}  {device_id}")
    return lines or ["Nenhum dispositivo USB enumerado"]
