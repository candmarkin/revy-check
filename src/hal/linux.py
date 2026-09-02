"""Backend Linux: sysfs, procfs e utilitarios de linha de comando.

O grosso deste arquivo veio de `src/functions/hw_paths.py` e da coleta de
`src/functions/system_info.py`, sem mudanca de comportamento -- so' mudou de
lugar, para caber atras da interface de `src.hal`.

Identificacao por caminho fisico, e nao por indice: o mesmo modelo comercial
(ex.: ThinkPad T14 Gen 1) existe em variante Intel e AMD. Os numeros de bus do
`lsusb -t` e o indice `cardN` do DRM mudam entre elas -- e o indice do card muda
ate' entre boots da mesma maquina, conforme a ordem de probe do driver.
"""

import glob
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

PLATFORM = "linux"

USB_DEVICES = "/sys/bus/usb/devices"
DRM_CLASS = "/sys/class/drm"

USB_CLASS_MASS_STORAGE = "08"

NO_VIDEO_DRIVER_HINT = (
    "Nenhum connector em /sys/class/drm. Verifique: dmesg | grep -i 'firmware load'"
)


def _read(path, default=""):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def _run(cmd, default=""):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return default


# --------------------------------------------------------------- identificacao


def dmi():
    """(fabricante, nome do produto) lidos do DMI."""
    manufacturer = _read("/sys/class/dmi/id/sys_vendor")
    # So' a Lenovo poe o modelo comercial em product_version; nas outras o
    # product_name e' que serve.
    if "LENOVO" in manufacturer.upper():
        product = _read("/sys/class/dmi/id/product_version", "UnknownDevice")
    else:
        product = _read("/sys/class/dmi/id/product_name", "UnknownDevice")
    return manufacturer, product or "UnknownDevice"


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


def serial_number():
    return _read("/sys/class/dmi/id/product_serial", "unknown") or "unknown"


def system_info():
    info = {"serial": _read("/sys/class/dmi/id/product_serial", "N/A") or "N/A"}

    cpu = "N/A"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    info["cpu"] = cpu

    ram = "N/A"
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    ram = f"{round(int(line.split()[1]) / (1024 ** 2), 1)} GB"
                    break
    except (OSError, ValueError):
        pass
    info["ram"] = ram

    disk = _run(["lsblk", "-o", "NAME,SIZE", "-dn"])
    info["disk"] = " / ".join(disk.splitlines()) if disk else "N/A"

    ips = _run(["hostname", "-I"])
    info["ip"] = ips.split()[0] if ips.split() else "N/A"

    return info


# ------------------------------------------------------------------------ USB


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
    return _read(os.path.join(device_dir, "physical_location", "panel")) or None


def mass_storage_ports():
    """{port_id: painel} das portas com um dispositivo de armazenamento.

    Equivale ao `Class=Mass Storage` que era procurado no `lsusb -t`, mas lendo
    direto do sysfs. O painel vem do ACPI _PLD e pode ser None.
    """
    ports = {}
    for iface in glob.glob(f"{USB_DEVICES}/*:*"):
        if _read(os.path.join(iface, "bInterfaceClass")) != USB_CLASS_MASS_STORAGE:
            continue
        device_dir = _usb_device_dir(iface)
        if device_dir:
            ports[usb_port_id(device_dir)] = usb_physical_location(device_dir)
    return ports


def mass_storage_port_ids():
    """IDs das portas fisicas com um dispositivo de armazenamento conectado."""
    return set(mass_storage_ports())


def port_has_device(bus, port_id):
    """True se a porta cadastrada estiver com um pendrive conectado.

    Aceita os dois formatos de cadastro: o novo, por caminho fisico no sysfs
    (bus='0000:00:14.0', port_id='3.2'), e o legado, que gravava o texto do
    `lsusb -t` (bus='Bus 002', port_id='Port 003:'). O formato legado quebra
    entre variantes Intel/AMD do mesmo modelo porque a numeracao de bus muda
    com o chipset, mas continua sendo lido para nao invalidar cadastros antigos.
    """
    if is_physical_port_id(bus):
        return f"{bus}/{port_id}" in mass_storage_port_ids()
    return _legacy_port_has_device(bus, port_id)


def _legacy_port_has_device(bus, port_id):
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        for bus_string in output.split("/:"):
            for line in bus_string.splitlines():
                if port_id in line and "Class=Mass Storage" in line and bus in bus_string:
                    return True
    except Exception as e:
        print("Erro ao executar lsusb:", e)
    return False


def usb_topology():
    """Linhas da topologia USB, para o overlay do modo DEV."""
    output = _run(["lsusb", "-t"])
    return output.splitlines() if output else ["lsusb indisponivel"]


# ------------------------------------------------------------------------ DRM


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


video_connector_name = drm_connector_name


def _drm_connectors():
    """Diretorios de connector presentes em /sys/class/drm."""
    return sorted(glob.glob(f"{DRM_CLASS}/card*-*"))


def video_available():
    return bool(_drm_connectors())


def video_entries():
    """Nomes dos connectors presentes, sem o prefixo 'cardN-'."""
    return [drm_connector_name(path) for path in _drm_connectors()]


def _find_drm_connector(entry):
    """Diretorio do connector que casa com `entry`, ignorando o indice do card."""
    wanted = drm_connector_name(entry)
    for path in _drm_connectors():
        if drm_connector_name(path) == wanted:
            return path
    return None


def video_connector_status(entry):
    """'connected', 'disconnected' ou 'unknown' para a entrada informada."""
    path = _find_drm_connector(entry)
    if not path:
        return "unknown"
    return _read(os.path.join(path, "status")) or "unknown"


def is_internal_panel(entry):
    """True para a tela embutida (eDP/LVDS), que nao entra no teste de portas."""
    name = drm_connector_name(entry)
    return name.startswith("eDP") or name.startswith("LVDS")


# ----------------------------------------------------------------------- rede


def ethernet_interfaces():
    """[(nome, descricao)] das interfaces cabeadas, para o cadastro."""
    interfaces = []
    for path in sorted(glob.glob("/sys/class/net/*")):
        name = os.path.basename(path)
        if name == "lo" or os.path.exists(os.path.join(path, "wireless")):
            continue
        if not os.path.exists(os.path.join(path, "device")):
            continue  # sem device fisico: bridge, tun, docker...
        interfaces.append((name, _read(os.path.join(path, "device/uevent"))[:60]))
    return interfaces


def ethernet_connected(eth_interface):
    return _read(f"/sys/class/net/{eth_interface}/carrier") == "1"


def wifi_interfaces():
    return [
        (os.path.basename(os.path.dirname(path)), "")
        for path in sorted(glob.glob("/sys/class/net/*/wireless"))
    ]


# ----------------------------------------------------------------------- wifi
#
# `iw` e' a fonte preferida porque devolve dBm e frequencia; `nmcli` entra como
# alternativa nas imagens que rodam NetworkManager e nao tem o iw instalado.


def _has(command):
    return shutil.which(command) is not None


def _run_iw(args, timeout=10):
    commands = []
    if _has("iw"):
        commands.append(["iw", *args])
    if _has("sudo"):
        commands.append(["sudo", "-n", "iw", *args])

    for cmd in commands:
        try:
            return subprocess.check_output(
                cmd, text=True, stderr=subprocess.DEVNULL, timeout=timeout
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return None


def wifi_enabled(interface=None):
    if not interface:
        found = wifi_interfaces()
        interface = found[0][0] if found else None
    if not interface:
        return False

    if _has("ip"):
        output = _run(["ip", "link", "show", interface])
        if output:
            return "state UP" in output
    if _has("nmcli"):
        return _run(["nmcli", "radio", "wifi"]).strip().lower() == "enabled"
    return False


def wifi_enable(interface=None):
    if not interface:
        found = wifi_interfaces()
        interface = found[0][0] if found else None
    if not interface:
        return False, "Interface WiFi não detectada"

    if _has("ip"):
        result = subprocess.run(
            ["sudo", "ip", "link", "set", interface, "up"],
            check=False, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            time.sleep(2)
            return True, "WiFi habilitado"
    if _has("nmcli"):
        result = subprocess.run(
            ["nmcli", "radio", "wifi", "on"],
            check=False, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            time.sleep(2)
            return True, "WiFi habilitado"
    return False, "Sem comando para habilitar WiFi (ip/nmcli)"


def _parse_iw_scan(output):
    networks = {}
    current = {}
    for raw in output.split("\n"):
        line = raw.strip()
        if line.startswith("BSS"):
            if current.get("ssid"):
                networks.setdefault(current["ssid"], current)
            current = {"bssid": line.split()[1].rstrip("(on"), "signal": -100, "frequency": 0}
        elif line.startswith("SSID:"):
            current["ssid"] = line.split("SSID:", 1)[1].strip()
        elif line.startswith("signal:"):
            match = re.search(r"(-?\d+(?:\.\d+)?)\s*dBm", line)
            if match:
                current["signal"] = int(float(match.group(1)))
        elif line.startswith("freq:"):
            match = re.search(r"freq:\s*(\d+)", line)
            if match:
                current["frequency"] = int(match.group(1))
    if current.get("ssid"):
        networks.setdefault(current["ssid"], current)

    for network in networks.values():
        network["band"] = "5GHz" if network["frequency"] >= 5000 else "2.4GHz"
    return sorted(networks.values(), key=lambda n: n["signal"], reverse=True)


def _parse_nmcli_scan(output):
    networks = []
    for line in output.split("\n")[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        ssid = " ".join(parts[:-3])
        if not ssid or ssid == "--":
            continue
        try:
            signal, frequency = int(parts[-3]), int(parts[-2])
        except ValueError:
            continue
        networks.append({
            "ssid": ssid,
            "signal": signal,
            "frequency": frequency,
            "band": "5GHz" if frequency >= 5000 else "2.4GHz",
            "bssid": parts[-1],
        })
    return sorted(networks, key=lambda n: n["signal"], reverse=True)


def wifi_scan(interface=None):
    if not interface:
        found = wifi_interfaces()
        interface = found[0][0] if found else None
    if not interface:
        return False, []

    output = _run_iw([interface, "scan"])
    if output:
        return True, _parse_iw_scan(output)

    if _has("nmcli"):
        output = _run(
            ["nmcli", "-f", "SSID,SIGNAL,FREQ,BSSID", "device", "wifi", "list"]
        )
        if output:
            return True, _parse_nmcli_scan(output)
    return False, []


def wifi_connection_info(interface=None):
    if not interface:
        found = wifi_interfaces()
        interface = found[0][0] if found else None
    if not interface:
        return None

    output = _run_iw([interface, "link"], timeout=5)
    if output and "Not connected" not in output:
        info = {}
        for raw in output.split("\n"):
            line = raw.strip()
            if line.startswith("SSID:"):
                info["ssid"] = line.split("SSID:", 1)[1].strip()
            elif line.startswith("signal:"):
                match = re.search(r"(-?\d+)\s*dBm", line)
                if match:
                    info["signal"] = int(match.group(1))
        if info:
            return info

    if _has("nmcli"):
        for line in _run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "device", "wifi"]).split("\n"):
            if line.startswith("yes:"):
                parts = line.split(":")
                if len(parts) >= 3:
                    return {
                        "ssid": parts[1],
                        "signal": int(parts[2]) if parts[2].isdigit() else 0,
                    }
    return None


# ---------------------------------------------------------------------- audio

try:
    import pulsectl

    _pulse = pulsectl.Pulse("headphone-monitor")
    _pulse_error = None
except Exception as exc:
    _pulse = None
    _pulse_error = f"{type(exc).__name__}: {exc}"


def jack_detection_available():
    """False quando o pulsectl nao carregou.

    Sem isso quem chama nao distingue "nenhum headphone plugado" de "nao da'
    para detectar headphone nenhum", e o passo espera para sempre um evento
    que nunca vai chegar.
    """
    return _pulse is not None


def jack_detection_error():
    return _pulse_error


def headphone_connected():
    if not _pulse:
        return False
    for sink in _pulse.sink_list():
        try:
            port_name = sink.port_active.name.lower()
            if "headphone" in port_name or "analog-output-headphones" in port_name:
                return True
        except Exception:
            continue
    return False


# -------------------------------------------------------------- sistema/kiosk


def lock_hotkeys():
    for key in ("switch-applications", "switch-windows"):
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.wm.keybindings", key, "[]"],
            check=False,
        )


def unlock_hotkeys():
    for key in ("switch-applications", "switch-windows"):
        subprocess.run(
            ["gsettings", "reset", "org.gnome.desktop.wm.keybindings", key],
            check=False,
        )


def set_system_time(dt):
    """Ajusta o relogio do sistema. Precisa de sudo sem senha para `date`."""
    formatted = dt.strftime("%m%d%H%M%Y.%S")
    return subprocess.run(["sudo", "date", formatted], check=False).returncode == 0


def photos_dir():
    path = Path("/tmp/revy_photos")
    path.mkdir(parents=True, exist_ok=True)
    return path


def camera_backend():
    """Backend do OpenCV; o padrao (V4L2) e' o certo no Linux."""
    import cv2

    return cv2.CAP_ANY


