#!/usr/bin/env python3
"""Smoke test do RevyCheck, headless, em Linux e Windows.

Valida as dependencias e a parte NAO interativa de cada passo do app
(conexao com banco, NTP, deteccao de hardware, etc.) sem abrir a tela
fullscreen. Cada checagem tem timeout proprio, entao nunca trava - os
passos interativos do app (*_step, wait_for_db_connection) tem loop
infinito e por isso aqui testamos as funcoes de deteccao por baixo deles.

A deteccao de hardware passa por `src.hal`, entao este script exercita o
mesmo caminho que o app usa em cada SO.

Uso:
    python3 scripts/smoke_test.py      # Linux (pode rodar por SSH)
    python scripts/smoke_test.py       # Windows

Codigo de saida: 0 se nenhum FAIL, 1 se houver qualquer FAIL.
FAIL  = bloqueia o app (precisa consertar).
WARN  = pode falhar sem hardware/audio/display presente (informativo).
"""

import os
import sys
import threading
from pathlib import Path

# --- headless: pygame/mixer/font funcionam sem servidor X ---
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# --------------------------------------------------------------------------
# infra
# --------------------------------------------------------------------------
class StepTimeout(Exception):
    pass


RESULTS = []


def run_with_timeout(fn, seconds):
    """Roda `fn` numa thread e desiste depois de `seconds`.

    A versao anterior usava SIGALRM, que so existe no Unix -- no Windows o
    timeout ficava desligado e uma checagem travada segurava o script inteiro.
    A thread fica orfa se estourar o tempo (e daemon), mas o relatorio sai.
    """
    box = {}

    def target():
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 - o smoke test relata tudo
            box["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        raise StepTimeout(f"timeout apos {seconds}s")
    if "error" in box:
        raise box["error"]
    return box.get("value")


def check(name, fn, timeout=10, severity="FAIL"):
    """Roda fn(); registra PASS, ou (WARN|FAIL) conforme `severity`."""
    try:
        detail = run_with_timeout(fn, timeout)
        RESULTS.append(("PASS", name, detail or "ok"))
    except Exception as exc:  # noqa: BLE001 - smoke test quer capturar tudo
        RESULTS.append((severity, name, f"{type(exc).__name__}: {exc}"))


# --------------------------------------------------------------------------
# checagens
# --------------------------------------------------------------------------
def c_deps():
    import cv2
    import ntplib  # noqa: F401
    import requests  # noqa: F401
    import numpy
    import pygame
    import sounddevice  # noqa: F401
    return (
        f"pygame {pygame.__version__}, numpy {numpy.__version__}, "
        f"opencv {cv2.__version__}"
    )


def c_pygame_init():
    import pygame
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 20)
    surf = pygame.Surface((640, 480))
    _ = font.render("smoke", True, (255, 255, 255))
    return f"init ok, surface {surf.get_size()}"


def c_api():
    """A API substituiu o acesso direto ao MySQL: nenhuma credencial de banco
    vive mais no agente, so' a chave de /revy-check/*."""
    from src import api_client, config
    if not api_client.disponivel():
        raise RuntimeError(f"sem resposta de {config.api_url()}")
    return f"respondeu em {config.api_url()}"


def c_device_info():
    # Se o device nao estiver cadastrado, fetch_device_info chama cadastro_portas
    # (tkinter) -> sem display isso levanta erro em vez de travar. O timeout cobre.
    from src.functions.device_info import fetch_device_info
    info = fetch_device_info()
    return f"{info.get('PRODUCT_NAME')} | {len(info.get('PORT_MAP', []))} USB, {len(info.get('VIDEO_PORTS', []))} video"


def c_system_info():
    from src.functions.system_info import get_system_info
    info = get_system_info()
    return f"serial={info.get('serial')!r} ip={info.get('ip')!r}"


def c_ntp():
    from src.functions.ntp import consulta_ntp
    import datetime as _dt
    ts = consulta_ntp()
    return _dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")


def c_audio_mixer():
    import pygame
    from src.functions.audio import generate_tone
    if not pygame.get_init():
        pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    snd = generate_tone(4000, 0.1, "both")
    return f"mixer ok, tom gerado ({snd.get_length():.2f}s)"


def c_sounddevice():
    import sounddevice as sd
    devs = sd.query_devices()
    ins = sum(1 for d in devs if d["max_input_channels"] > 0)
    outs = sum(1 for d in devs if d["max_output_channels"] > 0)
    return f"{len(devs)} devices ({ins} in, {outs} out)"


def c_jack():
    from src.functions.audio import headphone_connected, jack_detection_available
    if not jack_detection_available():
        raise RuntimeError("sem deteccao de jack; o app vai perguntar ao operador")
    return f"headphone_connected() -> {headphone_connected()}"


def c_camera():
    import cv2
    from src import hal
    cap = cv2.VideoCapture(0, hal.camera_backend())
    try:
        if not cap.isOpened():
            raise RuntimeError("camera 0 nao abriu")
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("nao leu frame")
        return f"frame {frame.shape[1]}x{frame.shape[0]}"
    finally:
        cap.release()


def c_ethernet():
    from src import hal
    interfaces = hal.ethernet_interfaces()
    if not interfaces:
        raise RuntimeError("nenhuma interface cabeada detectada")
    return ", ".join(
        f"{name} carrier={hal.ethernet_connected(name)}" for name, _ in interfaces
    )


def c_usb():
    from src import hal
    lines = hal.usb_topology()
    ports = hal.mass_storage_ports()
    return f"{len(lines)} nos USB; mass storage em {sorted(ports) or 'nenhuma porta'}"


def c_video_ports():
    from src import hal
    if not hal.video_available():
        raise RuntimeError(hal.NO_VIDEO_DRIVER_HINT)
    externas = [e for e in hal.video_entries() if not hal.is_internal_panel(e)]
    conectadas = hal.connected_video_ports()
    return f"{len(externas)} saidas, conectadas: {sorted(conectadas) or 'nenhuma'}"


def c_wifi():
    import pygame
    from src.functions.wifi import WiFiTest
    if not pygame.get_init():
        pygame.init()
    surf = pygame.Surface((640, 480))
    font = pygame.font.SysFont("Arial", 18)
    wt = WiFiTest(surf, font)
    iface = wt.detect_wifi_interface()
    status = wt.check_wifi_status()
    return f"interface={iface} status={status}"


# --------------------------------------------------------------------------
# execucao
# --------------------------------------------------------------------------
def main():
    from src import hal

    print("=" * 64)
    print(f"RevyCheck - smoke test (headless) - backend: {hal.PLATFORM}")
    print("=" * 64)

    # ordem = ordem do fluxo real do app (main.py)
    check("deps            (imports)",        c_deps,           timeout=20)
    check("pygame          (init+font)",      c_pygame_init,    timeout=15)
    check("api             (/revy-check)",     c_api,           timeout=10)
    check("device_info     (fetch_device_info)", c_device_info, timeout=12)
    check("system_info     (get_system_info)", c_system_info,   timeout=10)
    check("ntp             (consulta_ntp)",   c_ntp,            timeout=8)
    check("audio           (mixer+tom)",      c_audio_mixer,    timeout=10, severity="WARN")
    check("audio_devices   (sounddevice)",    c_sounddevice,    timeout=10, severity="WARN")
    check("audio_headphone (jack)",           c_jack,           timeout=8,  severity="WARN")
    check("camera          (cv2 VideoCapture)", c_camera,       timeout=12, severity="WARN")
    check("ethernet        (carrier)",        c_ethernet,       timeout=8,  severity="WARN")
    check("usb             (portas fisicas)", c_usb,            timeout=8)
    check("video_ports     (saidas de video)", c_video_ports,   timeout=8,  severity="WARN")
    check("wifi            (detect+status)",  c_wifi,           timeout=15, severity="WARN")

    print()
    fails = warns = passes = 0
    for status, name, detail in RESULTS:
        if status == "PASS":
            passes += 1
        elif status == "WARN":
            warns += 1
        else:
            fails += 1
        print(f"[{status:4}] {name:34} {detail}")

    print()
    print("-" * 64)
    print(f"resumo: {passes} PASS, {warns} WARN, {fails} FAIL")
    print("-" * 64)
    if fails:
        print("!! Ha FAIL(s) que bloqueiam o app. Corrija antes de rodar o main.py.")
    else:
        print("OK: nenhum bloqueador. WARN sao esperados sem hw/audio/display.")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
