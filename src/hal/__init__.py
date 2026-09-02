"""Camada de hardware: a mesma API sobre Linux (sysfs) e Windows (Win32).

O backend e' escolhido por `sys.platform` no import. Quem chama nao sabe em qual
SO esta rodando -- os steps de teste falam so' com os nomes reexportados aqui.

O pacote se chama `hal` e nao `platform` de proposito: `python src/main.py`
coloca `src/` no `sys.path[0]`, e um pacote chamado `platform` sombrearia o
modulo `platform` da biblioteca padrao para o processo inteiro.
"""

import sys

if sys.platform == "win32":
    from src.hal import windows as _impl
else:
    from src.hal import linux as _impl

PLATFORM = _impl.PLATFORM

# A lista abaixo e' a interface. Um backend que nao implementar tudo quebra
# aqui, no import, e nao no meio de um teste na bancada.

# --- identificacao -----------------------------------------------------
dmi = _impl.dmi
cpu_vendor = _impl.cpu_vendor
serial_number = _impl.serial_number
system_info = _impl.system_info

# --- USB ---------------------------------------------------------------
mass_storage_ports = _impl.mass_storage_ports
mass_storage_port_ids = _impl.mass_storage_port_ids
is_physical_port_id = _impl.is_physical_port_id
port_has_device = _impl.port_has_device
usb_topology = _impl.usb_topology

# --- video -------------------------------------------------------------
video_available = _impl.video_available
video_entries = _impl.video_entries
video_connector_name = _impl.video_connector_name
video_connector_status = _impl.video_connector_status
is_internal_panel = _impl.is_internal_panel
NO_VIDEO_DRIVER_HINT = _impl.NO_VIDEO_DRIVER_HINT

# --- rede --------------------------------------------------------------
ethernet_interfaces = _impl.ethernet_interfaces
ethernet_connected = _impl.ethernet_connected
wifi_interfaces = _impl.wifi_interfaces
wifi_enabled = _impl.wifi_enabled
wifi_enable = _impl.wifi_enable
wifi_scan = _impl.wifi_scan
wifi_connection_info = _impl.wifi_connection_info

# --- audio -------------------------------------------------------------
jack_detection_available = _impl.jack_detection_available
jack_detection_error = _impl.jack_detection_error
headphone_connected = _impl.headphone_connected

# --- sistema / kiosk ---------------------------------------------------
lock_hotkeys = _impl.lock_hotkeys
unlock_hotkeys = _impl.unlock_hotkeys
set_system_time = _impl.set_system_time
photos_dir = _impl.photos_dir
camera_backend = _impl.camera_backend


def connected_video_ports():
    """Connectors de video externos conectados agora.

    Usado pelo cadastro para identificar a porta pelo delta de conexao: e' a
    unica forma que funciona igual nos dois SOs, ja' que nem o nome do
    connector do DRM nem o `connectorInstance` do Windows dizem em qual lado do
    chassi a porta fica.
    """
    connected = set()
    for entry in video_entries():
        if is_internal_panel(entry):
            continue
        if video_connector_status(entry) == "connected":
            connected.add(entry)
    return connected
