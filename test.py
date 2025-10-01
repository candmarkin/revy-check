import mysql.connector
import subprocess



def fetch_device_info():
    conn = mysql.connector.connect(
        host="revy.selbetti.com.br",
        user="drack",
        password="jdVg2dF2@",
        database="revycheck"
    )

    try:
        manufacturer = subprocess.check_output("dmidecode -s system-manufacturer", shell=True).strip().decode("utf-8")
    except Exception:
        manufacturer = ""
    try:
        if "LENOVO" in str(manufacturer).upper():
            productname = subprocess.check_output("dmidecode -s system-version", shell=True).strip().decode("utf-8")
        else:
            productname = subprocess.check_output("dmidecode -s system-product-name", shell=True).strip().decode("utf-8")
    except Exception:
        productname = "UnknownDevice"

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("select id from devices where name=%s", (productname,))
        device = cursor.fetchone()
        if not device:
            raise ValueError(f"Device '{productname}' not found in database.")
        device_id = device['id']
        print(f"Device ID for '{productname}': {device_id}")

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("SELECT bus, port, label FROM device_usb_ports WHERE device_id=%s", (device_id,))
        port_map = [(row['bus'], row['port'], row['label']) for row in cursor.fetchall()]

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("SELECT label, entry FROM device_video_ports WHERE device_id=%s", (device_id,))
        video_ports = [{"label": row['label'], "entry": row['entry']} for row in cursor.fetchall()]

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("SELECT * FROM devices WHERE id=%s", (device_id,))
        device = cursor.fetchone()

    
    return {
        "PORT_MAP": port_map,
        "VIDEO_PORTS": video_ports,
        "HAS_EMBEDDED_SCREEN": device.get("has_embedded_screen", False),
        "HAS_EMBEDDED_KEYBOARD": device.get("has_embedded_keyboard", False),
        "HAS_ETHERNET_PORT": device.get("has_ethernet_port", False),
        "ETH_INTERFACE": device.get("eth_interface", "eth0"),
        "HAS_SPEAKER": device.get("has_speaker", False),
        "HAS_HEADPHONE_JACK": device.get("has_headphone_jack", False),
        "HAS_MICROPHONE": device.get("has_microphone", False)
    }


config = fetch_device_info()

PORT_MAP = config["PORT_MAP"]
VIDEO_PORTS = config["VIDEO_PORTS"]
HAS_EMBEDDED_SCREEN = config["HAS_EMBEDDED_SCREEN"]
HAS_EMBEDDED_KEYBOARD = config["HAS_EMBEDDED_KEYBOARD"]
HAS_ETHERNET_PORT = config["HAS_ETHERNET_PORT"]
ETH_INTERFACE = config["ETH_INTERFACE"]
HAS_SPEAKER = config["HAS_SPEAKER"]
HAS_HEADPHONE_JACK = config["HAS_HEADPHONE_JACK"]
HAS_MICROPHONE = config["HAS_MICROPHONE"]


print(VIDEO_PORTS)