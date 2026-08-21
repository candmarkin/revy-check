"""
Identificacao de portas fisicas pelo sysfs, independente de chipset.

O mesmo modelo comercial (ex.: ThinkPad T14 Gen 1) existe em variante Intel e
AMD. Os numeros de bus do `lsusb -t` e o indice `cardN` do DRM mudam entre elas
-- e o indice do card muda ate' entre boots da mesma maquina, conforme a ordem
de probe do driver. Aqui as portas sao identificadas por caminho fisico, que e'
estavel.
"""

import glob
import os

USB_DEVICES = "/sys/bus/usb/devices"
DRM_CLASS = "/sys/class/drm"

USB_CLASS_MASS_STORAGE = "08"


# --------------------------------------------------------------------- USB


def _usb_device_dir(path):
    """Sobe no sysfs a partir de `path` ate' o diretorio do dispositivo USB.

    O dispositivo e' o unico nivel da cadeia que expoe `busnum`: abaixo dele
    ficam as interfaces (`1-3:1.0`) e acima o controlador.
    """
    current = os.path.realpath(path)
    while current not in ("/sys", "/"):
        if os.path.exists(os.path.join(current, "busnum")):
            return current
        current = os.path.dirname(current)
    return None


def usb_port_id(device_dir):
    """ID estavel da porta fisica: '<BDF do controlador>/<cadeia de portas>'.

    '/sys/devices/pci0000:00/0000:00:14.0/usb1/1-3.2' -> '0000:00:14.0/3.2'

    O numero do bus (o '1' de '1-3.2') fica de fora de proposito: depende da
    ordem de probe dos controladores xHCI e chega a mudar entre boots. A cadeia
    de portas ('3.2') e' fisica, e o BDF identifica o controlador.
    """
    return _port_id_from_path(os.path.realpath(device_dir))


def _port_id_from_path(resolved):
    """Parte pura de `usb_port_id`, separada para poder ser testada."""
    parts = resolved.split("/")
    devpath = parts[-1]
    # O BDF mais proximo do dispositivo e' o controlador xHCI; niveis acima
    # (bridges, 'pci0000:00') tem menos de dois ':'.
    controller = next((p for p in reversed(parts) if p.count(":") == 2), "?")
    chain = devpath.split("-", 1)[1] if "-" in devpath else devpath
    return f"{controller}/{chain}"


def is_physical_port_id(bus):
    """True se `bus` for um BDF de PCI (formato novo), False se for legado.

    Registros antigos gravaram 'Bus 002' na coluna `bus`; os novos gravam
    '0000:00:14.0'. So' o BDF tem dois ':'.
    """
    return isinstance(bus, str) and bus.count(":") == 2


def usb_physical_location(device_dir):
    """Painel do chassi ('left', 'right', 'top', ...) via ACPI _PLD, ou None.

    Exposto pelo kernel >= 5.18. Quando o firmware da maquina preenche isso
    corretamente e' a identificacao mais robusta possivel, porque nao depende
    nem do chipset nem do BDF.
    """
    try:
        with open(os.path.join(device_dir, "physical_location", "panel")) as f:
            return f.read().strip()
    except OSError:
        return None


def mass_storage_ports():
    """{port_id: painel} das portas com um dispositivo de armazenamento.

    Equivale ao `Class=Mass Storage` que era procurado no `lsusb -t`, mas lendo
    direto do sysfs. O painel vem do ACPI _PLD e pode ser None.
    """
    ports = {}
    for iface in glob.glob(f"{USB_DEVICES}/*:*"):
        try:
            with open(os.path.join(iface, "bInterfaceClass")) as f:
                if f.read().strip() != USB_CLASS_MASS_STORAGE:
                    continue
        except OSError:
            continue
        device_dir = _usb_device_dir(iface)
        if device_dir:
            ports[usb_port_id(device_dir)] = usb_physical_location(device_dir)
    return ports


def mass_storage_port_ids():
    """IDs das portas fisicas com um dispositivo de armazenamento conectado."""
    return set(mass_storage_ports())


# --------------------------------------------------------------------- DRM


class DrmUnavailable(RuntimeError):
    """Nenhum connector DRM presente: o driver de video nao carregou."""


def drm_connector_name(entry):
    """Remove o prefixo 'cardN-' de uma entrada DRM.

    'card0-HDMI-A-1' -> 'HDMI-A-1'. O indice do card depende da ordem de probe
    do driver (i915, amdgpu, simpledrm), entao a parte util e' so' o nome do
    connector.
    """
    base = os.path.basename(str(entry).rstrip("/"))
    if base.startswith("card") and "-" in base:
        return base.split("-", 1)[1]
    return base


def drm_connectors():
    """Diretorios de connector presentes em /sys/class/drm."""
    return sorted(glob.glob(f"{DRM_CLASS}/card*-*"))


def drm_available():
    return bool(drm_connectors())


def find_drm_connector(entry):
    """Diretorio do connector que casa com `entry`, ignorando o indice do card."""
    wanted = drm_connector_name(entry)
    for path in drm_connectors():
        if drm_connector_name(path) == wanted:
            return path
    return None


def drm_connector_status(entry):
    """'connected', 'disconnected' ou 'unknown' para a entrada informada."""
    path = find_drm_connector(entry)
    if not path:
        return "unknown"
    try:
        with open(os.path.join(path, "status")) as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def is_internal_panel(entry):
    """True para a tela embutida (eDP/LVDS), que nao entra no teste de portas."""
    name = drm_connector_name(entry)
    return name.startswith("eDP") or name.startswith("LVDS")


# --------------------------------------------------------------------- CPU


def cpu_vendor():
    """'intel', 'amd' ou '' -- discrimina variantes do mesmo modelo comercial."""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("vendor_id"):
                    value = line.split(":", 1)[1].strip()
                    if value == "GenuineIntel":
                        return "intel"
                    if value == "AuthenticAMD":
                        return "amd"
                    return value.lower()
    except OSError:
        pass
    return ""
