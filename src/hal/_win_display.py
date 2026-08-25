"""Saidas de video no Windows, equivalente ao `/sys/class/drm` do Linux.

Usa a CCD API (`QueryDisplayConfig`). O flag `QDC_ALL_PATHS` e' o ponto todo:
alem dos monitores ativos ele enumera os alvos **desconectados**, que e' do que
o teste precisa -- "conecte o monitor na porta X" so' funciona se a porta vazia
aparecer na lista. O campo `targetAvailable` e' o `status == "connected"` do DRM.

`WmiMonitorConnectionParams` nao serve aqui: so' lista monitor conectado.
"""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

ERROR_SUCCESS = 0
QDC_ALL_PATHS = 0x00000001
DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME = 2

OUTPUT_TECHNOLOGY = {
    0xFFFFFFFF: "OTHER",
    0: "VGA",
    1: "SVIDEO",
    2: "COMPOSITE",
    3: "COMPONENT",
    4: "DVI",
    5: "HDMI",
    6: "LVDS",
    8: "D_JPN",
    9: "SDI",
    10: "DISPLAYPORT",
    11: "DISPLAYPORT_EMBEDDED",
    12: "UDI",
    13: "UDI_EMBEDDED",
    14: "SDTVDONGLE",
    15: "MIRACAST",
    16: "INDIRECT_WIRED",
    17: "INDIRECT_VIRTUAL",
    0x80000000: "INTERNAL",
}

# Saidas que nao sao porta fisica: monitores sem fio, RDP e drivers de tela
# virtual. Nesta bancada apareceram 16 delas -- entrariam no teste como portas
# eternamente desconectadas.
VIRTUAL_TECHNOLOGIES = {"MIRACAST", "INDIRECT_WIRED", "INDIRECT_VIRTUAL", "SDTVDONGLE"}

# Equivalentes do eDP/LVDS: a tela embutida, que tem passo proprio.
INTERNAL_TECHNOLOGIES = {"INTERNAL", "DISPLAYPORT_EMBEDDED", "UDI_EMBEDDED", "LVDS"}

_CACHE_TTL = 0.25
_cache = {"at": 0.0, "targets": []}


class _LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]


class _PATH_SOURCE_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", _LUID),
        ("id", wintypes.UINT),
        ("modeInfoIdx", wintypes.UINT),
        ("statusFlags", wintypes.UINT),
    ]


class _PATH_TARGET_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", _LUID),
        ("id", wintypes.UINT),
        ("modeInfoIdx", wintypes.UINT),
        ("outputTechnology", wintypes.UINT),
        ("rotation", wintypes.UINT),
        ("scaling", wintypes.UINT),
        ("refreshRateNumerator", wintypes.UINT),
        ("refreshRateDenominator", wintypes.UINT),
        ("scanLineOrdering", wintypes.UINT),
        ("targetAvailable", wintypes.BOOL),
        ("statusFlags", wintypes.UINT),
    ]


class _PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", _PATH_SOURCE_INFO),
        ("targetInfo", _PATH_TARGET_INFO),
        ("flags", wintypes.UINT),
    ]


class _MODE_INFO(ctypes.Structure):
    # O conteudo nao interessa: so' precisa do tamanho certo para o array que
    # a API preenche junto com os paths.
    _fields_ = [("_raw", ctypes.c_byte * 64)]


class _DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.UINT),
        ("size", wintypes.UINT),
        ("adapterId", _LUID),
        ("id", wintypes.UINT),
    ]


class _TARGET_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", _DEVICE_INFO_HEADER),
        ("flags", wintypes.UINT),
        ("outputTechnology", wintypes.UINT),
        ("edidManufactureId", wintypes.USHORT),
        ("edidProductCodeId", wintypes.USHORT),
        ("connectorInstance", wintypes.UINT),
        ("monitorFriendlyDeviceName", wintypes.WCHAR * 64),
        ("monitorDevicePath", wintypes.WCHAR * 128),
    ]


def make_entry(technology, connector_instance, target_id):
    """Identificador estavel da porta, no lugar do 'HDMI-A-1' do DRM.

    O `target_id` entra na chave porque `(tecnologia, connectorInstance)` nao e'
    unico em maquina com mais de uma GPU: numa bancada com iGPU + dGPU
    apareceram dois `DISPLAYPORT-0`, com target 4352 e 200195. O `adapterId`
    nao serve de desempate -- e' um LUID regerado a cada boot.
    """
    return f"{technology}-{connector_instance}#{target_id}"


def technology_of(entry):
    return str(entry).split("-", 1)[0]


def _enumerate():
    n_path = wintypes.UINT()
    n_mode = wintypes.UINT()
    rc = user32.GetDisplayConfigBufferSizes(
        QDC_ALL_PATHS, ctypes.byref(n_path), ctypes.byref(n_mode)
    )
    if rc != ERROR_SUCCESS or n_path.value == 0:
        return []

    paths = (_PATH_INFO * n_path.value)()
    modes = (_MODE_INFO * n_mode.value)()
    rc = user32.QueryDisplayConfig(
        QDC_ALL_PATHS,
        ctypes.byref(n_path),
        ctypes.byref(paths),
        ctypes.byref(n_mode),
        ctypes.byref(modes),
        None,
    )
    if rc != ERROR_SUCCESS:
        return []

    targets = {}
    for i in range(n_path.value):
        target = paths[i].targetInfo
        technology = OUTPUT_TECHNOLOGY.get(target.outputTechnology, "OTHER")
        if technology in VIRTUAL_TECHNOLOGIES:
            continue

        name = _TARGET_DEVICE_NAME()
        name.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
        name.header.size = ctypes.sizeof(_TARGET_DEVICE_NAME)
        name.header.adapterId = target.adapterId
        name.header.id = target.id
        named = user32.DisplayConfigGetDeviceInfo(ctypes.byref(name)) == ERROR_SUCCESS

        entry = make_entry(
            technology, name.connectorInstance if named else 0, target.id
        )
        # A mesma porta aparece em varios paths (um por source possivel).
        # Basta um deles reportar o alvo disponivel para a porta estar ocupada.
        record = targets.setdefault(
            entry,
            {
                "entry": entry,
                "technology": technology,
                "connected": False,
                "monitor": name.monitorFriendlyDeviceName if named else "",
            },
        )
        if target.targetAvailable:
            record["connected"] = True
            if named and name.monitorFriendlyDeviceName:
                record["monitor"] = name.monitorFriendlyDeviceName

    return sorted(targets.values(), key=lambda t: t["entry"])


def targets(force=False):
    now = time.monotonic()
    if force or now - _cache["at"] > _CACHE_TTL:
        _cache["targets"] = _enumerate()
        _cache["at"] = now
    return _cache["targets"]


def available():
    """False quando nenhuma saida fisica e' enumerada: driver de video ausente."""
    return bool(targets())
