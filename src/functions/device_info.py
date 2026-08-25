import mysql.connector

from src import hal
from src.functions.cadastro import cadastro_portas


class DeviceNotRegistered(Exception):
    """O modelo lido do DMI nao existe na tabela devices."""


def fetch_device_info(max_cadastros=1):
    """Config do device, cadastrando o modelo se ele ainda nao existir.

    O cadastro roda no maximo `max_cadastros` vezes: antes isto se chamava de
    volta sem limite, entao cadastro cancelado ou com erro recursava ate'
    estourar a pilha.
    """
    for tentativa in range(max_cadastros + 1):
        try:
            return _fetch_device_info_once()
        except DeviceNotRegistered as exc:
            if tentativa >= max_cadastros:
                raise
            print(exc)
            cadastro_portas()

    raise DeviceNotRegistered("cadastro do device nao concluido")


_WITH_PLATFORM = (
    "SELECT id, cpu_vendor, platform FROM devices "
    "WHERE name=%s AND (cpu_vendor=%s OR cpu_vendor IS NULL OR cpu_vendor='') "
    "AND (platform=%s OR platform IS NULL OR platform='') "
    "ORDER BY (cpu_vendor IS NULL OR cpu_vendor=''), (platform IS NULL OR platform='') "
    "LIMIT 1"
)

_WITHOUT_PLATFORM = (
    "SELECT id, cpu_vendor FROM devices "
    "WHERE name=%s AND (cpu_vendor=%s OR cpu_vendor IS NULL OR cpu_vendor='') "
    "ORDER BY (cpu_vendor IS NULL OR cpu_vendor='') LIMIT 1"
)


def _find_device(cursor, productname, vendor):
    """Registro do modelo, preferindo a linha da variante correta.

    Dois eixos desempatam o mesmo nome de modelo:

    - `cpu_vendor`: o DMI nao distingue as variantes Intel e AMD do mesmo
      modelo comercial (um T14 Gen 1 se identifica como 'ThinkPad T14 Gen 1'
      nos dois casos), mas a topologia USB e os connectors de video sao
      diferentes.
    - `platform`: a mesma porta fisica tem nomes diferentes em cada SO
      ('0000:00:14.0/3.2' no Linux, 'PCIROOT(0)#PCI(1400)/3.2' no Windows).
      Um cadastro do outro SO reprovaria todas as portas.

    Em ambos, a linha preenchida ganha e a vazia serve de fallback para os
    cadastros feitos antes da coluna existir.
    """
    try:
        cursor.execute(_WITH_PLATFORM, (productname, vendor, hal.PLATFORM))
        return cursor.fetchone()
    except mysql.connector.Error as exc:
        # Banco ainda sem a migracao (scripts/add_platform_column.sql). Sem o
        # filtro o cadastro do outro SO pode ser escolhido -- por isso o aviso.
        if exc.errno != 1054:  # ER_BAD_FIELD_ERROR
            raise
        print(
            "AVISO: tabela devices sem a coluna 'platform'. "
            "Rode scripts/add_platform_column.sql: sem ela um cadastro feito "
            "em outro sistema operacional pode ser usado por engano."
        )
        cursor.execute(_WITHOUT_PLATFORM, (productname, vendor))
        return cursor.fetchone()


def _fetch_device_info_once():
    manufacturer, productname = hal.dmi()
    vendor = hal.cpu_vendor()

    conn = mysql.connector.connect(
        host="10.3.0.12",
        user="drack",
        password="jdVg2dF2@",
        database="revycheck",
        connection_timeout=10,
    )

    try:
        with conn.cursor(dictionary=True, buffered=True) as cursor:
            device = _find_device(cursor, productname, vendor)
            if not device:
                raise DeviceNotRegistered(
                    f"Device '{productname}' (CPU {vendor or 'desconhecida'}) not found in database."
                )

            device_id = device["id"]
            print(f"Device ID for '{productname}' (CPU {vendor or '?'}): {device_id}")
            if not device.get("cpu_vendor"):
                print(
                    f"AVISO: cadastro de '{productname}' nao tem cpu_vendor. "
                    "Portas USB/video podem estar erradas se este modelo tiver variante Intel e AMD."
                )
            if "platform" in device and not device.get("platform"):
                print(
                    f"AVISO: cadastro de '{productname}' nao tem platform. "
                    f"Se ele foi feito em outro SO, as portas nao vao casar em {hal.PLATFORM}."
                )

        with conn.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute("SELECT bus, port, label FROM device_usb_ports WHERE device_id=%s", (device_id,))
            port_map = [(row["bus"], row["port"], row["label"]) for row in cursor.fetchall()]

        with conn.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute("SELECT label, entry FROM device_video_ports WHERE device_id=%s", (device_id,))
            video_ports = [{"label": row["label"], "entry": row["entry"]} for row in cursor.fetchall()]

        with conn.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute("SELECT * FROM devices WHERE id=%s", (device_id,))
            device = cursor.fetchone()
    finally:
        # Antes so' fechava no caminho feliz: qualquer erro vazava a conexao.
        conn.close()

    return {
        "MANUFACTURER": manufacturer,
        "PRODUCT_NAME": productname,
        "CPU_VENDOR": vendor,
        "PORT_MAP": port_map,
        "VIDEO_PORTS": video_ports,
        "HAS_EMBEDDED_SCREEN": device.get("has_embedded_screen", False),
        "HAS_EMBEDDED_KEYBOARD": device.get("has_embedded_keyboard", False),
        "HAS_ETHERNET_PORT": device.get("has_ethernet_port", False),
        "ETH_INTERFACE": device.get("eth_interface", "eth0"),
        "HAS_SPEAKER": device.get("has_speaker", False),
        "HAS_HEADPHONE_JACK": device.get("has_headphone_jack", False),
        "HAS_MICROPHONE": device.get("has_microphone", False),
        "HAS_WIFI": device.get("has_wifi", False),
        "HAS_TOUCHPAD": device.get("has_touchpad", False),
        "HAS_CAMERA": device.get("has_camera", False),
    }
