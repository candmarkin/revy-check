"""Backend Windows: Win32 puro via `ctypes` e `winreg`.

Cada funcao aqui e' o par da homonima em `linux.py`. Onde o Linux le um arquivo
do sysfs, aqui se le uma propriedade do device tree, uma chave do registro ou
uma API do Win32 -- sempre pelo identificador fisico, nunca pelo indice de
enumeracao, pelo mesmo motivo que la': indice muda entre boots.

Nenhum destes caminhos precisa de dependencia externa. So' `system_info()` toca
o `psutil` (disco/IP) e um unico `powershell` para o serial do BIOS, que nao
tem equivalente no registro.
"""

import ctypes
import json
import subprocess
import tempfile
import winreg
from ctypes import wintypes
from datetime import timezone
from pathlib import Path

from src.hal import (
    _win_audio,
    _win_display,
    _win_kiosk,
    _win_net,
    _win_usb,
    _win_wifi,
)

PLATFORM = "windows"

NO_VIDEO_DRIVER_HINT = (
    "Nenhuma saida de video enumerada. Verifique o driver da GPU no "
    "Gerenciador de Dispositivos."
)

_BIOS_KEY = r"HARDWARE\DESCRIPTION\System\BIOS"
_CPU_KEY = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"

_CREATE_NO_WINDOW = 0x08000000


def _reg(path, name, default=""):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            value = winreg.QueryValueEx(key, name)[0]
    except OSError:
        return default
    return str(value).strip() or default


def _powershell(script, default=None):
    """Roda um script curto e devolve o JSON que ele imprimir.

    Usado so' para o que nao existe no registro. `CREATE_NO_WINDOW` evita o
    flash de console preto por cima da tela cheia do pygame.
    """
    try:
        output = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=20,
            creationflags=_CREATE_NO_WINDOW,
        )
        return json.loads(output) if output.strip() else default
    except Exception:
        return default


# --------------------------------------------------------------- identificacao


def dmi():
    """(fabricante, nome do produto), equivalente ao /sys/class/dmi/id.

    O registro expoe os mesmos campos do SMBIOS que o DMI do Linux, e a
    ramificacao da Lenovo se traduz 1:1: `SystemVersion` e' o `product_version`,
    onde so' a Lenovo grava o modelo comercial.
    """
    manufacturer = _reg(_BIOS_KEY, "SystemManufacturer")
    if "LENOVO" in manufacturer.upper():
        product = _reg(_BIOS_KEY, "SystemVersion") or _reg(_BIOS_KEY, "SystemProductName")
    else:
        product = _reg(_BIOS_KEY, "SystemProductName")
    return manufacturer, product or "UnknownDevice"


def cpu_vendor():
    """'intel', 'amd' ou '' -- discrimina variantes do mesmo modelo comercial."""
    vendor = _reg(_CPU_KEY, "VendorIdentifier")
    if vendor == "GenuineIntel":
        return "intel"
    if vendor == "AuthenticAMD":
        return "amd"
    return vendor.lower()


_serial_cache = None


def serial_number():
    """Serial do BIOS. Unica informacao que exige WMI, entao fica em cache."""
    global _serial_cache
    if _serial_cache is None:
        data = _powershell(
            "(Get-CimInstance Win32_BIOS).SerialNumber | ConvertTo-Json -Compress"
        )
        _serial_cache = str(data).strip() if data else "unknown"
    return _serial_cache


def _total_ram_gb():
    class _MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = _MemoryStatus()
    status.dwLength = ctypes.sizeof(_MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return "N/A"
    return f"{round(status.ullTotalPhys / (1024 ** 3), 1)} GB"


def _disks():
    try:
        import psutil
    except ImportError:
        return "N/A"

    seen = []
    for part in psutil.disk_partitions(all=False):
        try:
            total = psutil.disk_usage(part.mountpoint).total
        except OSError:
            continue  # unidade removivel sem midia
        seen.append(f"{part.device.rstrip(chr(92))} {round(total / (1024 ** 3))}G")
    return " / ".join(seen) if seen else "N/A"


def system_info():
    return {
        "serial": serial_number(),
        "cpu": _reg(_CPU_KEY, "ProcessorNameString", "N/A"),
        "ram": _total_ram_gb(),
        "disk": _disks(),
        "ip": _win_net.primary_ip(),
    }


# ------------------------------------------------------------------------ USB

mass_storage_ports = _win_usb.mass_storage_ports
is_physical_port_id = _win_usb.is_physical_port_id
usb_topology = _win_usb.topology


def mass_storage_port_ids():
    return set(mass_storage_ports())


def port_has_device(bus, port_id):
    """True se a porta cadastrada estiver com um pendrive conectado.

    Um cadastro feito no Linux ('0000:00:14.0') nunca casa aqui: o mesmo pino
    fisico tem outro nome no Windows ('PCIROOT(0)#PCI(1400)'). Nesse caso a
    porta e' reprovada em vez de dar falso positivo -- o modelo precisa ser
    cadastrado tambem no Windows.
    """
    if not is_physical_port_id(bus):
        return False
    return f"{bus}/{port_id}" in mass_storage_port_ids()


# ---------------------------------------------------------------------- video


def video_available():
    return _win_display.available()


def video_entries():
    return [target["entry"] for target in _win_display.targets()]


def video_connector_name(entry):
    """No Windows a entrada ja' e' o nome canonico da porta.

    Existe para casar com o backend Linux, onde o 'cardN-' precisa sair.
    """
    return str(entry)


def video_connector_status(entry):
    for target in _win_display.targets():
        if target["entry"] == entry:
            return "connected" if target["connected"] else "disconnected"
    return "unknown"


def is_internal_panel(entry):
    """True para a tela embutida, que nao entra no teste de portas."""
    return _win_display.technology_of(entry) in _win_display.INTERNAL_TECHNOLOGIES


# ----------------------------------------------------------------------- rede

ethernet_interfaces = _win_net.ethernet_interfaces
wifi_interfaces = _win_net.wifi_interfaces


def _wifi_description(interface):
    """Descricao do driver a partir do nome da conexao ('Wi-Fi 4').

    A Native Wifi API identifica a placa pela descricao do driver, nao pelo
    nome da conexao que o cadastro guarda.
    """
    for name, description in wifi_interfaces():
        if name == interface:
            return description
    return None


def wifi_enabled(interface=None):
    return _win_wifi.enabled(_wifi_description(interface))


def wifi_enable(interface=None):
    """O Windows nao permite ligar o radio por API sem interacao do usuario.

    `WlanSetInterface` com radio state exige privilegio e nao funciona com o
    modo aviao; o caminho suportado e' o proprio operador ligar. Retornar o
    estado real e' mais honesto do que fingir que ligou.
    """
    if wifi_enabled(interface):
        return True, "WiFi já habilitado"
    return False, "Ligue o WiFi (tecla de rádio / modo avião) e repita o teste"


def wifi_scan(interface=None):
    ok, entries = _win_wifi.scan(_wifi_description(interface))
    if not ok:
        return False, []

    networks = {}
    for ssid, rssi, frequency_khz, bssid in entries:
        if not ssid or not ssid.strip():
            continue  # rede oculta: sem SSID nao ha' o que mostrar
        frequency = frequency_khz // 1000  # a API devolve kHz, o resto usa MHz
        best = networks.get(ssid)
        if best is None or rssi > best["signal"]:
            networks[ssid] = {
                "ssid": ssid,
                "signal": rssi,
                "frequency": frequency,
                "band": "5GHz" if frequency >= 5000 else "2.4GHz",
                "bssid": bssid,
            }

    ordered = sorted(networks.values(), key=lambda n: n["signal"], reverse=True)
    return True, ordered


def wifi_connection_info(interface=None):
    found = _win_wifi.connection(_wifi_description(interface))
    if not found:
        return None
    ssid, quality = found
    return {"ssid": ssid, "signal": quality}


def ethernet_connected(eth_interface):
    if _win_net.link_up(eth_interface):
        return True

    # O nome da conexao no Windows ('Ethernet 6') e' renomeavel pelo usuario, e
    # o cadastro pode ter sido feito com outro nome. Se a maquina tem uma unica
    # placa cabeada, ela e' a que o teste quer.
    interfaces = ethernet_interfaces()
    if len(interfaces) == 1 and interfaces[0][0] != eth_interface:
        return _win_net.link_up(interfaces[0][0])
    return False


# ---------------------------------------------------------------------- audio

jack_detection_available = _win_audio.jack_detection_available
headphone_connected = _win_audio.headphone_connected


def jack_detection_error():
    return None if jack_detection_available() else "nenhum endpoint de headphone"


# -------------------------------------------------------------- sistema/kiosk

lock_hotkeys = _win_kiosk.lock_hotkeys
unlock_hotkeys = _win_kiosk.unlock_hotkeys


def set_system_time(dt):
    """Ajusta o relogio. Precisa de privilegio de administrador.

    `SetSystemTime` recebe UTC; converter aqui evita depender do fuso da
    maquina, que e' justamente o que pode estar errado.
    """

    class _SystemTime(ctypes.Structure):
        _fields_ = [
            ("wYear", wintypes.WORD),
            ("wMonth", wintypes.WORD),
            ("wDayOfWeek", wintypes.WORD),
            ("wDay", wintypes.WORD),
            ("wHour", wintypes.WORD),
            ("wMinute", wintypes.WORD),
            ("wSecond", wintypes.WORD),
            ("wMilliseconds", wintypes.WORD),
        ]

    utc = dt.astimezone(timezone.utc)
    system_time = _SystemTime(
        utc.year, utc.month, 0, utc.day, utc.hour, utc.minute, utc.second,
        utc.microsecond // 1000,
    )
    if ctypes.windll.kernel32.SetSystemTime(ctypes.byref(system_time)):
        return True

    print("SetSystemTime falhou (precisa de admin); tentando w32tm /resync")
    try:
        return subprocess.run(
            ["w32tm", "/resync"],
            check=False,
            capture_output=True,
            timeout=30,
            creationflags=_CREATE_NO_WINDOW,
        ).returncode == 0
    except Exception:
        return False


def photos_dir():
    path = Path(tempfile.gettempdir()) / "revy_photos"
    path.mkdir(parents=True, exist_ok=True)
    return path

def camera_backend():
    """Backend do OpenCV. O padrao no Windows escolhe mal e abre lento."""
    import cv2

    return cv2.CAP_MSMF
