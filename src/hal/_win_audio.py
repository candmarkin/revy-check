"""Deteccao de jack no Windows, equivalente ao `sink.port_active` do pulsectl.

O Windows mantem o estado de cada endpoint de audio no registro, em
`MMDevices\\Audio\\Render\\{GUID}`:

    DeviceState  1 = ACTIVE   (plugado)
    DeviceState  8 = UNPLUGGED (o jack existe e esta' vazio)
    FormFactor   3 = Headphones, 5 = Headset, 1 = Speakers

E' a mesma informacao que `IMMDeviceEnumerator` + `DEVICE_STATE_UNPLUGGED`
entregariam via Core Audio, sem precisar de `pycaw`/`comtypes`, e independente
do idioma do Windows -- o nome do endpoint e' traduzido ("Auscultadores",
"Fones de ouvido"), o FormFactor nao.
"""

import winreg

from src.hal import _win_cfgmgr as cm

_RENDER_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"

_FORMFACTOR_VALUE = "{1da5d803-d492-4edd-8c23-e0c0ffee7f0e},0"
_DESCRIPTION_VALUE = "{a45c254e-df1c-4efd-8020-67d146a850e0},2"
_INTERFACE_VALUE = "{b3f8fa53-0004-438e-9003-51a46e139bfc},6"

FORM_FACTOR_HEADPHONES = 3
FORM_FACTOR_HEADSET = 5

STATE_ACTIVE = 1
STATE_UNPLUGGED = 8

# O estado vem com bits altos setados em alguns drivers (0x10000004); so' o
# nibble baixo carrega o DEVICE_STATE_*.
_STATE_MASK = 0xF

# Endpoints cujo dispositivo pai e' Bluetooth ou um driver virtual tambem se
# declaram Headphones. Um headset pareado ficaria "conectado" desde o inicio do
# teste e a etapa passaria sem ninguem plugar nada no jack.
_PHYSICAL_PARENTS = ("HDAUDIO\\", "USB\\", "PCI\\")


def _value(key, name):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def _endpoints():
    """[(guid, estado, form factor, descricao)] dos endpoints de saida."""
    found = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _RENDER_KEY)
    except OSError:
        return found

    with root:
        index = 0
        while True:
            try:
                guid = winreg.EnumKey(root, index)
            except OSError:
                break
            index += 1

            try:
                with winreg.OpenKey(root, guid) as endpoint:
                    state = _value(endpoint, "DeviceState")
                    try:
                        with winreg.OpenKey(endpoint, "Properties") as props:
                            form_factor = _value(props, _FORMFACTOR_VALUE)
                            description = " ".join(
                                str(_value(props, name) or "")
                                for name in (_DESCRIPTION_VALUE, _INTERFACE_VALUE)
                            ).strip()
                    except OSError:
                        form_factor, description = None, ""
            except OSError:
                continue

            if state is None or form_factor is None:
                continue
            found.append((guid, state & _STATE_MASK, form_factor, description))
    return found


def _is_physical(guid):
    """True se o endpoint pertence ao codec da placa ou a um dispositivo USB.

    O no' PnP do endpoint (`SWD\\MMDEVAPI\\{0.0.0.00000000}.{GUID}`) tem como
    pai o dispositivo dono: `HDAUDIO\\...` no codec onboard, `BTHENUM\\...` num
    fone Bluetooth, `ROOT\\MEDIA\\...` num cabo virtual.
    """
    for device_id in cm.device_ids("SWD"):
        if guid.lower() not in device_id.lower():
            continue
        devinst = cm.locate(device_id)
        if devinst is None:
            return False
        parent = cm.parent(devinst)
        if parent is None:
            return False
        parent_id = (cm.instance_id(parent) or "").upper()
        return parent_id.startswith(_PHYSICAL_PARENTS)
    return False


def jack_detection_available():
    """True se o codec expoe um endpoint de headphone, plugado ou nao.

    Quando a maquina nao tem jack analogico -- ou o driver nao o declara -- o
    passo precisa saber disso para pedir confirmacao ao operador, em vez de
    esperar para sempre por um evento que nunca chega.
    """
    return any(
        form_factor in (FORM_FACTOR_HEADPHONES, FORM_FACTOR_HEADSET)
        and state in (STATE_ACTIVE, STATE_UNPLUGGED)
        for _, state, form_factor, _ in _endpoints()
    )


def headphone_connected():
    for guid, state, form_factor, _ in _endpoints():
        if state != STATE_ACTIVE:
            continue
        if form_factor not in (FORM_FACTOR_HEADPHONES, FORM_FACTOR_HEADSET):
            continue
        if _is_physical(guid):
            return True
    return False


def describe():
    """Linhas legiveis dos endpoints, para depurar na bancada."""
    names = {STATE_ACTIVE: "ATIVO", STATE_UNPLUGGED: "VAZIO", 4: "AUSENTE", 2: "DESABILITADO"}
    factors = {1: "Speakers", 2: "LineLevel", 3: "Headphones", 4: "Microphone", 5: "Headset"}
    return [
        f"{names.get(state, state)!s:12} {factors.get(form_factor, form_factor)!s:12} {description}"
        for _, state, form_factor, description in _endpoints()
        if state != 4
    ]
