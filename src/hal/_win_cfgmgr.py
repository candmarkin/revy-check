"""Acesso ao device tree do Windows via `cfgmgr32.dll`, com `ctypes`.

E' o equivalente do sysfs: enumera os nos de dispositivo presentes e le
propriedades tipadas (`DEVPKEY_*`). Sem dependencia externa de proposito --
`pyusb`/`libusb` exigiriam trocar o driver da porta por WinUSB (Zadig) e nao
suportam hotplug no Windows, e `Get-PnpDeviceProperty` custaria um subprocess
PowerShell por dispositivo.
"""

import ctypes
from ctypes import wintypes

cfgmgr32 = ctypes.WinDLL("cfgmgr32", use_last_error=True)

CR_SUCCESS = 0
CR_BUFFER_SMALL = 26

CM_LOCATE_DEVNODE_NORMAL = 0x00000000

CM_GETIDLIST_FILTER_ENUMERATOR = 0x00000001
CM_GETIDLIST_FILTER_PRESENT = 0x00000100

DEVPROP_TYPE_UINT32 = 0x00000007
DEVPROP_TYPE_STRING = 0x00000012
DEVPROP_TYPE_STRING_LIST = 0x00002012


class DEVPROPKEY(ctypes.Structure):
    _fields_ = [("fmtid", ctypes.c_byte * 16), ("pid", wintypes.ULONG)]


def _fmtid(data1, data2, data3, rest):
    """GUID no layout binario do Windows (os tres primeiros campos little-endian)."""
    raw = (
        data1.to_bytes(4, "little")
        + data2.to_bytes(2, "little")
        + data3.to_bytes(2, "little")
        + bytes(rest)
    )
    return (ctypes.c_byte * 16).from_buffer_copy(raw)


_DEVICE_FMTID = _fmtid(
    0xA45C254E, 0xDF1C, 0x4EFD, (0x80, 0x20, 0x67, 0xD1, 0x46, 0xA8, 0x50, 0xE0)
)

DEVPKEY_Device_Service = DEVPROPKEY(_DEVICE_FMTID, 6)
DEVPKEY_Device_Class = DEVPROPKEY(_DEVICE_FMTID, 9)
DEVPKEY_Device_FriendlyName = DEVPROPKEY(_DEVICE_FMTID, 14)
DEVPKEY_Device_LocationInfo = DEVPROPKEY(_DEVICE_FMTID, 15)
DEVPKEY_Device_LocationPaths = DEVPROPKEY(_DEVICE_FMTID, 37)

DEVPKEY_Device_InstanceId = DEVPROPKEY(
    _fmtid(0x78C34FC8, 0x104A, 0x4ACA, (0x9E, 0xA4, 0x52, 0x4D, 0x52, 0x99, 0x6E, 0x57)), 256
)


def device_ids(enumerator, present_only=True):
    """IDs de instancia sob um enumerador ('USB', 'SWD', 'DISPLAY'...)."""
    flags = CM_GETIDLIST_FILTER_ENUMERATOR
    if present_only:
        flags |= CM_GETIDLIST_FILTER_PRESENT

    size = wintypes.ULONG()
    rc = cfgmgr32.CM_Get_Device_ID_List_SizeW(
        ctypes.byref(size), ctypes.c_wchar_p(enumerator), flags
    )
    if rc != CR_SUCCESS or size.value == 0:
        return []

    buf = ctypes.create_unicode_buffer(size.value)
    rc = cfgmgr32.CM_Get_Device_ID_ListW(
        ctypes.c_wchar_p(enumerator), buf, size.value, flags
    )
    if rc != CR_SUCCESS:
        return []
    return [s for s in buf[: size.value].split("\0") if s]


def locate(device_id):
    """Handle (devinst) do no de dispositivo, ou None se ele nao existe mais."""
    devinst = wintypes.DWORD()
    rc = cfgmgr32.CM_Locate_DevNodeW(
        ctypes.byref(devinst), ctypes.c_wchar_p(device_id), CM_LOCATE_DEVNODE_NORMAL
    )
    return devinst.value if rc == CR_SUCCESS else None


def parent(devinst):
    handle = wintypes.DWORD()
    rc = cfgmgr32.CM_Get_Parent(ctypes.byref(handle), devinst, 0)
    return handle.value if rc == CR_SUCCESS else None


def instance_id(devinst):
    return prop(devinst, DEVPKEY_Device_InstanceId)


def prop(devinst, key):
    """Valor de uma propriedade do no: str, list[str] ou int, conforme o tipo."""
    ptype = wintypes.ULONG()
    size = wintypes.ULONG(0)
    rc = cfgmgr32.CM_Get_DevNode_PropertyW(
        devinst, ctypes.byref(key), ctypes.byref(ptype), None, ctypes.byref(size), 0
    )
    if rc != CR_BUFFER_SMALL or size.value == 0:
        return None

    buf = (ctypes.c_byte * size.value)()
    rc = cfgmgr32.CM_Get_DevNode_PropertyW(
        devinst, ctypes.byref(key), ctypes.byref(ptype), buf, ctypes.byref(size), 0
    )
    if rc != CR_SUCCESS:
        return None

    if ptype.value == DEVPROP_TYPE_UINT32:
        return int.from_bytes(bytes(buf[:4]), "little")

    if ptype.value in (DEVPROP_TYPE_STRING, DEVPROP_TYPE_STRING_LIST):
        raw = ctypes.wstring_at(ctypes.cast(buf, ctypes.c_wchar_p), size.value // 2)
        if ptype.value == DEVPROP_TYPE_STRING_LIST:
            return [s for s in raw.split("\0") if s]
        return raw.rstrip("\0")

    return None
