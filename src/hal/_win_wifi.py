"""WiFi no Windows pela Native Wifi API (`wlanapi.dll`).

O backend Linux usa `iw`/`nmcli`. O equivalente aqui poderia ser `netsh wlan`,
mas a saida dele e' traduzida -- numa maquina em portugues o parser procuraria
"SSID" e acharia "SSID", mas "Sinal"/"Signal" e "Autenticacao"/"Authentication"
mudam. A API devolve struct binaria, que nao depende do idioma, e `WlanScan`
forca uma varredura de verdade no radio em vez de devolver cache.
"""

import ctypes
import time
from ctypes import wintypes

wlanapi = ctypes.WinDLL("wlanapi", use_last_error=True)

ERROR_SUCCESS = 0

# WLAN_INTERFACE_STATE
STATE_NOT_READY = 0
STATE_CONNECTED = 1
STATE_DISCONNECTED = 4

WLAN_MAX_NAME_LENGTH = 256
DOT11_SSID_MAX_LENGTH = 32

_OPCODE_CURRENT_CONNECTION = 7

# O radio leva alguns segundos para varrer todos os canais; a API retorna
# imediatamente e preenche a lista depois.
_SCAN_SETTLE_SECONDS = 4


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_byte * 8),
    ]


class _DOT11_SSID(ctypes.Structure):
    _fields_ = [
        ("uSSIDLength", ctypes.c_ulong),
        ("ucSSID", ctypes.c_ubyte * DOT11_SSID_MAX_LENGTH),
    ]

    def text(self):
        raw = bytes(self.ucSSID[: self.uSSIDLength])
        clean = raw.replace(b"\x00", b"")
        return clean.decode("utf-8", errors="replace").strip()


class _WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [
        ("InterfaceGuid", _GUID),
        ("strInterfaceDescription", wintypes.WCHAR * WLAN_MAX_NAME_LENGTH),
        ("isState", ctypes.c_uint),
    ]


class _WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [
        ("dwNumberOfItems", wintypes.DWORD),
        ("dwIndex", wintypes.DWORD),
        ("InterfaceInfo", _WLAN_INTERFACE_INFO * 1),
    ]


class _WLAN_RATE_SET(ctypes.Structure):
    _fields_ = [
        ("uRateSetLength", ctypes.c_ulong),
        ("usRateSet", ctypes.c_ushort * 126),
    ]


class _WLAN_BSS_ENTRY(ctypes.Structure):
    _fields_ = [
        ("dot11Ssid", _DOT11_SSID),
        ("uPhyId", ctypes.c_ulong),
        ("dot11Bssid", ctypes.c_ubyte * 6),
        ("dot11BssType", ctypes.c_uint),
        ("dot11BssPhyType", ctypes.c_uint),
        ("lRssi", ctypes.c_long),
        ("uLinkQuality", ctypes.c_ulong),
        ("bInRegDomain", ctypes.c_ubyte),
        ("usBeaconPeriod", ctypes.c_ushort),
        ("ullTimestamp", ctypes.c_ulonglong),
        ("ullHostTimestamp", ctypes.c_ulonglong),
        ("usCapabilityInformation", ctypes.c_ushort),
        ("ulChCenterFrequency", ctypes.c_ulong),
        ("wlanRateSet", _WLAN_RATE_SET),
        ("ulIeOffset", ctypes.c_ulong),
        ("ulIeSize", ctypes.c_ulong),
    ]


class _WLAN_BSS_LIST(ctypes.Structure):
    _fields_ = [
        ("dwTotalSize", wintypes.DWORD),
        ("dwNumberOfItems", wintypes.DWORD),
        ("wlanBssEntries", _WLAN_BSS_ENTRY * 1),
    ]


class _WLAN_ASSOCIATION_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("dot11Ssid", _DOT11_SSID),
        ("dot11BssType", ctypes.c_uint),
        ("dot11Bssid", ctypes.c_ubyte * 6),
        ("dot11PhyType", ctypes.c_uint),
        ("uDot11PhyIndex", ctypes.c_ulong),
        ("wlanSignalQuality", ctypes.c_ulong),
        ("ulRxRate", ctypes.c_ulong),
        ("ulTxRate", ctypes.c_ulong),
    ]


class _WLAN_SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("bSecurityEnabled", wintypes.BOOL),
        ("bOneXEnabled", wintypes.BOOL),
        ("dot11AuthAlgorithm", ctypes.c_uint),
        ("dot11CipherAlgorithm", ctypes.c_uint),
    ]


class _WLAN_CONNECTION_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("isState", ctypes.c_uint),
        ("wlanConnectionMode", ctypes.c_uint),
        ("strProfileName", wintypes.WCHAR * WLAN_MAX_NAME_LENGTH),
        ("wlanAssociationAttributes", _WLAN_ASSOCIATION_ATTRIBUTES),
        ("wlanSecurityAttributes", _WLAN_SECURITY_ATTRIBUTES),
    ]


def _free(pointer):
    if pointer:
        wlanapi.WlanFreeMemory(pointer)


class _Session:
    """Handle do serviço WLAN, aberto por operação e sempre fechado."""

    def __enter__(self):
        self.handle = wintypes.HANDLE()
        negotiated = wintypes.DWORD()
        rc = wlanapi.WlanOpenHandle(
            2, None, ctypes.byref(negotiated), ctypes.byref(self.handle)
        )
        if rc != ERROR_SUCCESS:
            raise OSError(f"WlanOpenHandle falhou ({rc})")
        return self

    def __exit__(self, *exc):
        wlanapi.WlanCloseHandle(self.handle, None)
        return False

    def interfaces(self):
        pointer = ctypes.POINTER(_WLAN_INTERFACE_INFO_LIST)()
        rc = wlanapi.WlanEnumInterfaces(self.handle, None, ctypes.byref(pointer))
        if rc != ERROR_SUCCESS:
            return []
        try:
            info_list = pointer.contents
            array = ctypes.cast(
                ctypes.byref(info_list.InterfaceInfo),
                ctypes.POINTER(_WLAN_INTERFACE_INFO * info_list.dwNumberOfItems),
            ).contents
            return [
                (_GUID.from_buffer_copy(item.InterfaceGuid),
                 item.strInterfaceDescription,
                 item.isState)
                for item in array
            ]
        finally:
            _free(pointer)


def _interface_by_description(session, description):
    found = session.interfaces()
    for guid, desc, state in found:
        if description and desc == description:
            return guid, desc, state
    return found[0] if found else None


def interfaces():
    """[(descricao, estado)] das placas WiFi que o servico enxerga."""
    try:
        with _Session() as session:
            return [(desc, state) for _, desc, state in session.interfaces()]
    except OSError:
        return []


def enabled(description=None):
    """True se o radio esta' ligado.

    `not_ready` e' o estado que o Windows reporta com o radio desligado por
    interruptor fisico ou pelo modo aviao.
    """
    try:
        with _Session() as session:
            found = _interface_by_description(session, description)
            return bool(found) and found[2] != STATE_NOT_READY
    except OSError:
        return False


def scan(description=None, settle=_SCAN_SETTLE_SECONDS):
    """[(ssid, dBm, frequencia kHz, bssid)] das redes ao alcance."""
    try:
        with _Session() as session:
            found = _interface_by_description(session, description)
            if not found:
                return False, []
            guid = found[0]

            wlanapi.WlanScan(session.handle, ctypes.byref(guid), None, None, None)
            time.sleep(settle)

            pointer = ctypes.POINTER(_WLAN_BSS_LIST)()
            rc = wlanapi.WlanGetNetworkBssList(
                session.handle, ctypes.byref(guid), None, 1, False, None,
                ctypes.byref(pointer),
            )
            if rc != ERROR_SUCCESS:
                return False, []

            try:
                bss_list = pointer.contents
                array = ctypes.cast(
                    ctypes.byref(bss_list.wlanBssEntries),
                    ctypes.POINTER(_WLAN_BSS_ENTRY * bss_list.dwNumberOfItems),
                ).contents
                return True, [
                    (
                        entry.dot11Ssid.text(),
                        int(entry.lRssi),
                        int(entry.ulChCenterFrequency),
                        ":".join(f"{b:02x}" for b in entry.dot11Bssid),
                    )
                    for entry in array
                ]
            finally:
                _free(pointer)
    except OSError:
        return False, []


def connection(description=None):
    """(ssid, qualidade 0-100) da conexao atual, ou None."""
    try:
        with _Session() as session:
            found = _interface_by_description(session, description)
            if not found or found[2] != STATE_CONNECTED:
                return None
            guid = found[0]

            size = wintypes.DWORD()
            pointer = ctypes.c_void_p()
            rc = wlanapi.WlanQueryInterface(
                session.handle, ctypes.byref(guid), _OPCODE_CURRENT_CONNECTION,
                None, ctypes.byref(size), ctypes.byref(pointer), None,
            )
            if rc != ERROR_SUCCESS or not pointer:
                return None
            try:
                attributes = ctypes.cast(
                    pointer, ctypes.POINTER(_WLAN_CONNECTION_ATTRIBUTES)
                ).contents
                association = attributes.wlanAssociationAttributes
                return association.dot11Ssid.text(), int(association.wlanSignalQuality)
            finally:
                _free(pointer)
    except OSError:
        return None
