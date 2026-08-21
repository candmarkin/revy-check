#!/usr/bin/env python3
"""Smoke test do RevyCheck para rodar via SSH (headless, sem X).

Valida as dependencias e a parte NAO interativa de cada passo do app
(conexao com banco, NTP, deteccao de hardware, etc.) sem abrir a tela
fullscreen. Cada checagem tem timeout proprio, entao nunca trava - os
passos interativos do app (*_step, wait_for_db_connection) tem loop
infinito e por isso aqui testamos as funcoes de deteccao por baixo deles.

Uso:
    ssh vistoria@bancada
    cd ~/revy-check
    python3 scripts/smoke_test.py

Codigo de saida: 0 se nenhum FAIL, 1 se houver qualquer FAIL.
FAIL  = bloqueia o app (precisa consertar).
WARN  = pode falhar no SSH sem hardware/audio/display (informativo).
"""

import contextlib
import os
import signal
import sys
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


# SIGALRM so existe no Unix. Sem ele nao ha' timeout nenhum, e uma checagem
# travada segura o script inteiro - por isso o aviso no cabecalho.
TIMEOUTS_ENABLED = hasattr(signal, "SIGALRM")


@contextlib.contextmanager
def time_limit(seconds):
    """Aborta a checagem se passar de `seconds` (usa SIGALRM, so Linux)."""
    def _handler(signum, frame):
        raise StepTimeout(f"timeout apos {seconds}s")

    if TIMEOUTS_ENABLED:
        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
    try:
        yield
    finally:
        if TIMEOUTS_ENABLED:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)


RESULTS = []


def check(name, fn, timeout=10, severity="FAIL"):
    """Roda fn(); registra PASS, ou (WARN|FAIL) conforme `severity`."""
    try:
        with time_limit(timeout):
            detail = fn()
        RESULTS.append(("PASS", name, detail or "ok"))
    except Exception as exc:  # noqa: BLE001 - smoke test quer capturar tudo
        RESULTS.append((severity, name, f"{type(exc).__name__}: {exc}"))


# --------------------------------------------------------------------------
# checagens
# --------------------------------------------------------------------------
def c_deps():
    import cv2
    import mysql.connector  # noqa: F401
    import ntplib  # noqa: F401
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


DB = dict(host="10.3.0.12", user="drack", password="jdVg2dF2@", database="revycheck")


def c_db():
    import mysql.connector
    conn = mysql.connector.connect(connection_timeout=5, **DB)
    conn.close()
    return f"conectou em {DB['host']}"


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


def c_pulse_headphone():
    from src.functions.audio import headphone_connected
    return f"headphone_connected() -> {headphone_connected()}"


def c_camera():
    import cv2
    cap = cv2.VideoCapture(0)
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
    import subprocess
    from src.functions.ethernet import ethernet_connected
    out = subprocess.check_output(["ip", "-o", "link", "show"], text=True)
    ifaces = [ln.split(":")[1].strip() for ln in out.splitlines()]
    eth = next((i for i in ifaces if i.startswith(("en", "eth"))), None)
    if not eth:
        raise RuntimeError(f"nenhuma interface eth/en em {ifaces}")
    return f"{eth} carrier={ethernet_connected(eth)}"


def c_usb():
    import subprocess
    out = subprocess.check_output(["lsusb", "-t"], text=True)
    return f"lsusb -t ok ({len(out.splitlines())} linhas)"


def c_video_ports():
    drm = Path("/sys/class/drm")
    if not drm.is_dir():
        raise RuntimeError("/sys/class/drm ausente")
    entries = []
    for st in drm.glob("*/status"):
        entries.append(f"{st.parent.name}={st.read_text().strip()}")
    if not entries:
        raise RuntimeError("nenhum conector DRM")
    return ", ".join(entries)


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
    print("=" * 64)
    print("RevyCheck - smoke test (headless / SSH)")
    if not TIMEOUTS_ENABLED:
        print(f"AVISO: sem SIGALRM em {sys.platform} - timeouts DESATIVADOS.")
        print("       Uma checagem travada nao aborta sozinha.")
    print("=" * 64)

    # ordem = ordem do fluxo real do app (main.py)
    check("deps            (imports)",        c_deps,           timeout=20)
    check("pygame          (init+font)",      c_pygame_init,    timeout=15)
    check("db              (mysql 10.3.0.12)", c_db,            timeout=8)
    check("device_info     (fetch_device_info)", c_device_info, timeout=12)
    check("system_info     (get_system_info)", c_system_info,   timeout=10)
    check("ntp             (consulta_ntp)",   c_ntp,            timeout=8)
    check("audio           (mixer+tom)",      c_audio_mixer,    timeout=10, severity="WARN")
    check("audio_devices   (sounddevice)",    c_sounddevice,    timeout=10, severity="WARN")
    check("audio_headphone (pulsectl)",       c_pulse_headphone, timeout=8, severity="WARN")
    check("camera          (cv2 VideoCapture)", c_camera,       timeout=12, severity="WARN")
    check("ethernet        (carrier)",        c_ethernet,       timeout=8,  severity="WARN")
    check("usb             (lsusb -t)",       c_usb,            timeout=8)
    check("video_ports     (/sys/class/drm)", c_video_ports,    timeout=8,  severity="WARN")
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
        print("!! Ha FAIL(s) que bloqueiam o app. Corrija antes do startx.")
    else:
        print("OK: nenhum bloqueador. WARN sao esperados no SSH sem hw/audio/display.")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
