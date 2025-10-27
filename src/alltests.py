import pygame
import subprocess
import sys
import time
import numpy as np
import pulsectl
import sounddevice as sd
import os
import json
from datetime import datetime
import mysql.connector
import tkinter as tk
from tkinter import simpledialog, messagebox

# ---------------- APP CADASTRO ----------------
def has_pendrive_connected_cd():
    try:
        outputA = subprocess.check_output(["lsusb", "-t"], text=True)
        return "Class=Mass Storage" in str(outputA)
    except Exception:
        return False

def ask_yes_no(question):
    return messagebox.askyesno("Pergunta", question)

def ask_text(prompt):
    import tkinter as tk
    from tkinter import simpledialog

    # Janela oculta base
    root = tk.Tk()
    root.withdraw()

    # Criar diálogo manualmente para garantir foco e captura de input
    dialog = tk.Toplevel(root)
    dialog.title("Entrada")
    dialog.geometry("450x150")
    dialog.resizable(False, False)

    # Faz o diálogo ficar sempre no topo e receber foco
    dialog.attributes("-topmost", True)
    dialog.lift()
    dialog.focus_force()
    dialog.grab_set()   # bloqueia clique fora

    # Label
    label = tk.Label(dialog, text=prompt, anchor="w", justify="left", wraplength=430)
    label.pack(pady=(10, 5), padx=10)

    # Campo de texto
    entry = tk.Entry(dialog, width=45, font=("DejaVu Sans", 12))
    entry.pack(pady=5)
    entry.focus_set()  # força cursor dentro do input

    result = None

    def confirm():
        nonlocal result
        result = entry.get().strip()
        dialog.destroy()

    def cancel():
        nonlocal result
        result = ""
        dialog.destroy()

    # Botões
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="OK", width=10, command=confirm).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancelar", width=10, command=cancel).pack(side="left", padx=5)

    # Enter confirma, Esc cancela
    dialog.bind("<Return>", lambda e: confirm())
    dialog.bind("<Escape>", lambda e: cancel())

    # Loop modal (igual askstring, mas com foco garantido)
    dialog.wait_window()

    root.destroy()
    return result


def ask_password(question):
    return simpledialog.askstring("Senha", question, show="*")

def wait_for_ok(message):
    messagebox.showinfo("Ação necessária", message)

def try_connect_db(cfg):
    try:
        conn = mysql.connector.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database'],
            connection_timeout=5
        )
        if conn.is_connected():
            return True, conn
        else:
            return False, "Não conectado"
    except Exception as e:
        return False, str(e)

def send_to_db(conn, productname, has_screen, has_keyboard, has_eth, eth_interface, has_speaker, has_headphone, has_mic, port_map, video_ports):
    cursor = conn.cursor()
    try:
        # devices
        insert_device = (
            "INSERT INTO devices "
            "(name, type, has_embedded_screen, has_embedded_keyboard, has_ethernet, eth_interface, has_speaker, has_headphone_jack, has_microphone) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        device_vals = (
            productname, 'Notebook',
            1 if has_screen else 0,
            1 if has_keyboard else 0,
            1 if has_eth else 0,
            eth_interface,
            1 if has_speaker else 0,
            1 if has_headphone else 0,
            1 if has_mic else 0
        )
        cursor.execute(insert_device, device_vals)
        dev_id = cursor.lastrowid

        # usb ports
        if port_map:
            insert_usb = "INSERT INTO device_usb_ports (device_id, bus, port, label) VALUES (%s, %s, %s, %s)"
            usb_vals = [(dev_id, p['bus'], p['port'], p['label']) for p in port_map]
            cursor.executemany(insert_usb, usb_vals)

        # video ports
        if video_ports:
            insert_vid = "INSERT INTO device_video_ports (device_id, label, entry) VALUES (%s, %s, %s)"
            vid_vals = [(dev_id, v['label'], v['entry']) for v in video_ports]
            cursor.executemany(insert_vid, vid_vals)

        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()

def cadastro_portas():

    root = tk.Tk()
    root.withdraw()
    root.focus_force()
    root.update()

    messagebox.showinfo("Banco de Dados", "Antes de iniciar, vamos conectar ao banco MySQL.\n\nSe a rede não estiver ativa, conecte e clique em Tentar novamente.")



    db_cfg = {}
    connected = False
    db_conn = None

    while not connected:
        # pede dados do DB
        db_cfg['host'] = "revy.selbetti.com.br"
        db_cfg['port'] = 3306
        db_cfg['user'] = "drack"
        db_cfg['password'] = "jdVg2dF2@"
        db_cfg['database'] = "revycheck"

        ok, result = try_connect_db(db_cfg)
        if ok:
            connected = True
            db_conn = result
            messagebox.showinfo("OK", f"Conectado ao banco {db_cfg['host']}:{db_cfg['port']} -> {db_cfg['database']}")
            break
        else:
            retry = messagebox.askretrycancel("Erro de conexão", f"Falha ao conectar: {result}\n\nConecte a rede (ou verifique dados) e tente novamente.")
            if not retry:
                messagebox.showwarning("Cancelado", "Operação cancelada pelo usuário. Encerrando.")
                root.destroy()
                raise SystemExit(0)


    # ----------------- OBTÉM INFORMAÇÕES BÁSICAS DO SISTEMA -----------------
    try:
        manufacturer = subprocess.check_output("cat /sys/class/dmi/id/sys_vendor", shell=True).strip().decode("utf-8")
    except Exception:
        manufacturer = ""
    try:
        if "LENOVO" in str(manufacturer).upper():
            productname = subprocess.check_output("cat /sys/class/dmi/id/product_version", shell=True).strip().decode("utf-8")
        else:
            productname = subprocess.check_output("cat /sys/class/dmi/id/product_name", shell=True).strip().decode("utf-8")
    except Exception:
        productname = "UnknownDevice"

    PORT_MAP = []
    VIDEO_PORTS = []

    # ----------------- CADASTRO HARDWARE -----------------


    messagebox.showinfo("Início", f"Antes de cadastrar as portas, algumas perguntas sobre o hardware do seu {productname}:")


    HAS_EMBEDDED_SCREEN = ask_yes_no("Seu dispositivo possui tela embutida?")
    HAS_EMBEDDED_KEYBOARD = ask_yes_no("Seu dispositivo possui teclado embutido?")
    HAS_ETHERNET_PORT = ask_yes_no("Seu dispositivo possui porta Ethernet?")

    ETH_INTERFACE = ""
    if HAS_ETHERNET_PORT:
        try:
            ipaddr_output = subprocess.check_output("ip addr", shell=True).decode("utf-8")
            # mostra as infos
            messagebox.showinfo("Interfaces detectadas", ipaddr_output)
        except Exception:
            pass
        ETH_INTERFACE = ask_text("Qual é a interface Ethernet do seu dispositivo? (Ex.: eno2)") or ""

    HAS_SPEAKER = ask_yes_no("Seu dispositivo possui alto-falante?")
    HAS_HEADPHONE_JACK = ask_yes_no("Seu dispositivo possui entrada para fone de ouvido?")
    HAS_MICROPHONE = ask_yes_no("Seu dispositivo possui microfone embutido?")

    # ----------------- CADASTRO PORTAS DE VIDEO -----------------
    messagebox.showinfo("Cadastro", "Agora, vamos cadastrar as portas de vídeo onde você conecta os monitores externos.")

    new_video_port = ask_text("Dê um nome para a porta de vídeo que deseja cadastrar (Ex.: HDMI Esquerdo)\n\n** Deixe vazio para finalizar **")
    while new_video_port:
        wait_for_ok(f"Conecte o cabo de vídeo na porta {new_video_port} e clique em OK...")

        while True:
            try:
                videoports = subprocess.check_output("ls /sys/class/drm/", shell=True).decode("utf-8").split()
                videoports = [port for port in videoports if "-" in port]
                for port in videoports:
                    # segurança: tente ler o status com try/except
                    try:
                        isconnected = subprocess.check_output(f"cat /sys/class/drm/{port}/status", shell=True).decode("utf-8").strip()
                    except Exception:
                        isconnected = ""
                    if isconnected == "connected" and port not in [v.get('entry') for v in VIDEO_PORTS] and port != "card0-eDP-1":
                        confirm = messagebox.askyesno("Confirmação", f"Porta detectada: {port}\nLabel: {new_video_port}\n\nConfirmar cadastro?")
                        if confirm:
                            VIDEO_PORTS.append({"label": new_video_port, "entry": port})
                            wait_for_ok("Porta de vídeo cadastrada com sucesso!\n\nRemova todos os cabos de vídeo conectados...")
                            # espera até o cabo ser removido
                            while True:
                                try:
                                    still_connected = subprocess.check_output(f"cat /sys/class/drm/{port}/status", shell=True).decode("utf-8").strip()
                                except Exception:
                                    still_connected = ""
                                if still_connected == "connected":
                                    time.sleep(1)
                                else:
                                    break
            except Exception:
                # se ls /sys/class/drm falhar, apenas continue (ambiente pode variar)
                pass
            break
        new_video_port = ask_text("Dê um nome para a próxima porta de vídeo (ou vazio para finalizar)")

    # ----------------- CADASTRO PORTAS USB -----------------
    messagebox.showinfo("Cadastro", "Agora, vamos cadastrar as portas USB onde você conecta os pendrives.")

    new_port = ask_text("Dê um nome para a porta (Ex.: USB-C Esquerdo 1)\n\n** Deixe vazio para finalizar **")
    while new_port:
        wait_for_ok(f"Conecte o pendrive na porta {new_port} e clique em OK...")

        try:
            output = subprocess.check_output(["lsusb", "-t"], text=True)
            for bus_string in output.split("/:"):
                for line in bus_string.splitlines():
                    if "Class=Mass Storage" in line:
                        # tenta quebrar a linha para obter id/porta
                        try:
                            part = line.split(":")[0]
                            # fallback parsing
                            port_id = line.split(":")[0].split()[-1]
                        except Exception:
                            port_id = "unknown"
                        try:
                            bus = bus_string.splitlines()[0].split(":")[0].strip()
                        except Exception:
                            bus = "unknown"
                        confirm = messagebox.askyesno("Confirmação", f"Bus: {bus}\nPorta: {port_id}\nLabel: {new_port}\n\nConfirmar cadastro?")
                        if confirm:
                            PORT_MAP.append({"bus": bus, "port": f"Port {port_id}:", "label": new_port})
                            wait_for_ok("Porta cadastrada com sucesso!\n\nRemova todos os pendrives conectados...")
            # espera remoção do pendrive
            temusb = has_pendrive_connected_cd()
            while temusb:
                time.sleep(1)
                temusb = has_pendrive_connected_cd()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar lsusb: {e}")

        new_port = ask_text("Dê um nome para a próxima porta (ou vazio para finalizar)")

    # ----------------- RESUMO E CONFIRMAÇÃO -----------------
    resumo = "Resumo do cadastro:\n\n"
    for port in PORT_MAP:
        resumo += f"USB -> Bus: {port['bus']}, Porta: {port['port']}, Label: {port['label']}\n"
    for vport in VIDEO_PORTS:
        resumo += f"Vídeo -> Porta: {vport['entry']}, Label: {vport['label']}\n"

    resumo += f"\nTela embutida? {'Sim' if HAS_EMBEDDED_SCREEN else 'Não'}"
    resumo += f"\nTeclado embutido? {'Sim' if HAS_EMBEDDED_KEYBOARD else 'Não'}"
    resumo += f"\nEthernet? {'Sim' if HAS_ETHERNET_PORT else 'Não'}"
    resumo += f"\nAlto-falante? {'Sim' if HAS_SPEAKER else 'Não'}"
    resumo += f"\nFone de ouvido? {'Sim' if HAS_HEADPHONE_JACK else 'Não'}"
    resumo += f"\nMicrofone? {'Sim' if HAS_MICROPHONE else 'Não'}"
    resumo += f"\nInterface Ethernet: {ETH_INTERFACE}"
    resumo += f"\nNome do produto: {productname}"

    confirm = messagebox.askyesno("Resumo", resumo + "\n\nEstá tudo correto?")

    if confirm:
        # envia direto para o DB
        success, err = send_to_db(db_conn, productname, HAS_EMBEDDED_SCREEN, HAS_EMBEDDED_KEYBOARD, HAS_ETHERNET_PORT, ETH_INTERFACE, HAS_SPEAKER, HAS_HEADPHONE_JACK, HAS_MICROPHONE, PORT_MAP, VIDEO_PORTS)
        if success:
            messagebox.showinfo("Sucesso", "Dados inseridos no banco com sucesso!")
        else:
            messagebox.showerror("Erro ao inserir", f"Erro ao inserir no banco: {err}")
    else:
        messagebox.showinfo("Cancelado", "Cadastro cancelado pelo usuário. Nenhum dado foi enviado ao banco.")

    # fecha conexao e finaliza
    try:
        if db_conn:
            db_conn.close()
    except Exception:
        pass

    root.destroy()





# ----------------- APP TESTES -----------------

# Cores
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)


import mysql.connector

def fetch_device_info():


    conn = mysql.connector.connect(
        host="revy.selbetti.com.br",
        user="drack",
        password="jdVg2dF2@",
        database="revycheck"
    )

    try:
        manufacturer = subprocess.check_output("cat /sys/class/dmi/id/sys_vendor", shell=True).strip().decode("utf-8")
    except Exception:
        manufacturer = ""
    try:
        if "LENOVO" in str(manufacturer).upper():
            productname = subprocess.check_output("cat /sys/class/dmi/id/product_version", shell=True).strip().decode("utf-8")
        else:
            productname = subprocess.check_output("cat /sys/class/dmi/id/product_name", shell=True).strip().decode("utf-8")
    except Exception:
        productname = "UnknownDevice"

    with conn.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute("select id from devices where name=%s", (productname,))
        device = cursor.fetchone()
        if not device:
            print(f"Device '{productname}' not found in database.")
            cadastro_portas()
            fetch_device_info()  # tenta novamente após cadastro

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

    conn.close()

    
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



import ntplib
from datetime import timezone, timedelta

BR_TZ = timezone(timedelta(hours=-3))

def consulta_ntp(server='200.160.0.8'):
    try:
        client = ntplib.NTPClient()
        resp = client.request(server, version=3)
        ts = resp.tx_time
        dt_brasil = datetime.fromtimestamp(ts, timezone.utc).astimezone(BR_TZ)
        formatted = dt_brasil.strftime('%m%d%H%M%Y.%S')
        print("Hora obtida via NTP (Brasil UTC-3):", dt_brasil.strftime('%Y-%m-%d %H:%M:%S'))
        os.system(f"sudo date {formatted}")
        return ts

    except Exception as e:
        print("Erro ao consultar NTP:", e)
        return None


# Dev / Prod mode
MODE = "PROD"
DEV_PASSWORD = "dev123"

# Audio
SAMPLE_RATE = 44100
DURATION = 0.8
BIP_FREQ = 4000  # Hz
FREQUENCIES = [2000, 4000]

# Log
log_data = []


# ---------------- INIT PYGAME ---------------- #
pygame.init()

# Detecta resolução da tela e usa fullscreen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Checklist Técnico Completo")
pygame.mouse.set_visible(True)
FONT = pygame.font.SysFont("Arial", 20)
CLOCK = pygame.time.Clock()
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)

def wait_for_db_connection():
    while True:
        try:
            conn = mysql.connector.connect(
                host="revy.selbetti.com.br",
                user="drack",
                password="jdVg2dF2@",
                database="revycheck"
            )
            conn.close()
            return  # SUCESSO → sai do loop
        except:
            # Desenha tela de aviso
            SCREEN.fill((0, 0, 0))
            text = FONT.render("Conecte-se à rede corporativa", True, (255, 255, 255))
            SCREEN.blit(text, ((WIDTH - text.get_width()) // 2, (HEIGHT - text.get_height()) // 2))
            pygame.display.flip()

            # Evita 100% CPU
            CLOCK.tick(1)

wait_for_db_connection()

# ---------------- DEV HOTKEY ---------------- #
DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d, pygame.K_v} # conjunto de teclas

config = fetch_device_info()
consulta_ntp()

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


def add_log(entry: dict):
    if not any(e.get("step") == entry.get("step") for e in log_data):
        log_data.append(entry)


# DESATIVANDO ALT TAB
import subprocess

def disable_alt_tab():
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.wm.keybindings",
        "switch-applications", "[]"
    ])
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.wm.keybindings",
        "switch-windows", "[]"
    ])

def restore_alt_tab():
    subprocess.run([
        "gsettings", "reset",
        "org.gnome.desktop.wm.keybindings",
        "switch-applications"
    ])
    subprocess.run([
        "gsettings", "reset",
        "org.gnome.desktop.wm.keybindings",
        "switch-windows"
    ])



# ---------------- AUDIO FUNCTIONS ---------------- #
def generate_tone(freq, duration=DURATION, channel="both"):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    if channel == "left":
        stereo_wave = np.column_stack((wave, np.zeros_like(wave)))
    elif channel == "right":
        stereo_wave = np.column_stack((np.zeros_like(wave), wave))
    else:
        stereo_wave = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo_wave)

def play_headphone_sequence():
    for freq in FREQUENCIES:
        draw_text([f"🔊 {freq} Hz - HEADPHONE ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.2)
        draw_text([f"🔊 {freq} Hz - HEADPHONE DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.2)
        draw_text([f"🔊 {freq} Hz - HEADPHONE AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.5)

def play_speaker_sequence():
    draw_text(["🔊 Teste de alto-falantes - sem headphone"])
    time.sleep(1)
    for freq in FREQUENCIES:
        draw_text([f"🔊 {freq} Hz - SPEAKER DIREITA"])
        generate_tone(freq, DURATION, "right").play()
        time.sleep(DURATION + 0.3)
        draw_text([f"🔊 {freq} Hz - SPEAKER ESQUERDA"])
        generate_tone(freq, DURATION, "left").play()
        time.sleep(DURATION + 0.3)
        draw_text([f"🔊 {freq} Hz - SPEAKER AMBOS"])
        generate_tone(freq, DURATION, "both").play()
        time.sleep(DURATION + 0.3)
    draw_text(["✅ Teste de alto-falantes concluído!"], (0, 255, 0))
    add_log({"step":"SPEAKER_TEST","time":str(datetime.now()), "result":"APROVADO"})
    time.sleep(1)

def test_microphone_bip():
    threshold = 0.01
    duration_record = 1.0
    draw_text(["🎤 Teste do microfone: ouvindo bip 4kHz"])
    time.sleep(0.5)
    sound = generate_tone(BIP_FREQ, DURATION, "both")
    sound.play()
    recording = sd.rec(int(duration_record * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    amplitude = float(np.max(np.abs(recording)))
    draw_text([f"Amplitude detectada: {amplitude:.3f}"])
    time.sleep(1)
    passed = amplitude > threshold
    if passed:
        draw_text(["✅ Microfone detectou o bip!"], (0, 255, 0))
        add_log({"step":"MICROPHONE_TEST","time":str(datetime.now()), "result":"APROVADO"})
    else:
        draw_text(["❌ Microfone não detectou o bip!"], (255, 0, 0))
        add_log({"step":"MICROPHONE_TEST","time":str(datetime.now()), "result":"REPROVADO"})
    time.sleep(2)

# ---------------- PULSEAUDIO ---------------- #
pulse = pulsectl.Pulse('headphone-monitor')
def headphone_connected():
    for sink in pulse.sink_list():
        port_name = sink.port_active.name.lower()
        if 'headphone' in port_name or 'analog-output-headphones' in port_name:
            return True
    return False


# ---------------- KEYBOARD ---------------- #
KEY_LAYOUT = [
    # Linha de funções
    [("Esc", pygame.K_ESCAPE, 58.5, 40), ("F1", pygame.K_F1, 58.5, 40), ("F2", pygame.K_F2, 58.5, 40), ("F3", pygame.K_F3, 58.5, 40),
     ("F4", pygame.K_F4, 58.5, 40), ("F5", pygame.K_F5, 58.5, 40), ("F6", pygame.K_F6, 58.5, 40), ("F7", pygame.K_F7, 58.5, 40),
     ("F8", pygame.K_F8, 58.5, 40), ("F9", pygame.K_F9, 58.5, 40), ("F10", pygame.K_F10, 58.5, 40), ("F11", pygame.K_F11, 58.5, 40),
     ("F12", pygame.K_F12, 58.5, 40), ("Insert", pygame.K_INSERT, 58.5, 40), ("Delete", pygame.K_DELETE, 58.5, 40)],
    
    # Números
    [("'", pygame.K_QUOTE, 60), ("1", pygame.K_1, 60), ("2", pygame.K_2, 60), ("3", pygame.K_3, 60),
     ("4", pygame.K_4, 60), ("5", pygame.K_5, 60), ("6", pygame.K_6, 60), ("7", pygame.K_7, 60),
     ("8", pygame.K_8, 60), ("9", pygame.K_9, 60), ("0", pygame.K_0, 60),
     ("-", pygame.K_MINUS, 60), ("=", pygame.K_EQUALS, 60), ("Backspace", pygame.K_BACKSPACE, 100)],

    # Linha QWERTY
    [("Tab", pygame.K_TAB, 100), ("Q", pygame.K_q, 60), ("W", pygame.K_w, 60), ("E", pygame.K_e, 60),
     ("R", pygame.K_r, 60), ("T", pygame.K_t, 60), ("Y", pygame.K_y, 60), ("U", pygame.K_u, 60),
     ("I", pygame.K_i, 60), ("O", pygame.K_o, 60), ("P", pygame.K_p, 60),
     ("´", 1073741824, 60), ("[", pygame.K_LEFTBRACKET, 60), ("Enter", pygame.K_RETURN, 60, 130)],

    # Linha ASDF
    [("Caps", pygame.K_CAPSLOCK, 110), ("A", pygame.K_a, 60), ("S", pygame.K_s, 60), ("D", pygame.K_d, 60),
     ("F", pygame.K_f, 60), ("G", pygame.K_g, 60), ("H", pygame.K_h, 60), ("J", pygame.K_j, 60),
     ("K", pygame.K_k, 60), ("L", pygame.K_l, 60), ("Ç", 231, 60),
     ("~", 1073741824, 60), ("]", pygame.K_RIGHTBRACKET, 60)],

    # Linha ZXCV
    [("Shift", pygame.K_LSHIFT, 80), (r"\\", pygame.K_BACKSLASH, 60), ("Z", pygame.K_z, 60), ("X", pygame.K_x, 60), ("C", pygame.K_c, 60),
     ("V", pygame.K_v, 60), ("B", pygame.K_b, 60), ("N", pygame.K_n, 60), ("M", pygame.K_m, 60),
     (",", pygame.K_COMMA, 60), (".", pygame.K_PERIOD, 60), (";", pygame.K_SEMICOLON, 60),
     ("Shift", pygame.K_RSHIFT, 145)],

    # Linha espaço
    [("Ctrl", pygame.K_LCTRL, 80), ("Fn", 1073741951, 60), ("Win", pygame.K_LSUPER, 60), ("Alt", pygame.K_LALT, 60),
     ("Espaço", pygame.K_SPACE, 320), ("AltGr", pygame.K_RALT, 60), ("/", pygame.K_SLASH, 60)],

     # Linha de navegação / setas
    [("←", pygame.K_LEFT, 60), 
    ("↑", pygame.K_UP, 80),
    ("↓", pygame.K_DOWN, 80), 
    ("→", pygame.K_RIGHT, 60),
    ("Pg Up", pygame.K_PAGEUP, 60),
    ("Pg Down", pygame.K_PAGEDOWN, 60),
    ]

] 

pressed_keys = set()
already_pressed = []
all_keys = []
for row in KEY_LAYOUT:
    for key in row:
        all_keys.append(key[1])

kb_button_rect = pygame.Rect(20, HEIGHT - 60, 200, 50)

def draw_keyboard():
    SCREEN.fill(WHITE)
    y = 80
    for row_idx, row in enumerate(KEY_LAYOUT):
        # Calcular largura total da linha para centralizar
        total_width = 0
        for key_def in row:
            if len(key_def) == 4:
                _, _, w, _ = key_def
            else:
                _, _, w = key_def
            total_width += w + 5
        total_width -= 5  # remover último espaçamento extra
        x = (WIDTH - total_width) // 2

        if row_idx == len(KEY_LAYOUT) - 1: # LAYOUT DAS SETAS
            x += 735 - ((WIDTH - total_width) // 2)  # manter alinhamento relativo

            # PAGEUP
            rect = pygame.Rect(x, y, row[4][2], 28)
            if row[4][1] in pressed_keys:
                color = GREEN
            elif row[4][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[4][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # SETA ESQUERDA
            rect = pygame.Rect(x, y + 32 , row[0][2], 28)
            if row[0][1] in pressed_keys:
                color = GREEN
            elif row[0][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[0][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            x+= 65

            # SETA CIMA
            rect = pygame.Rect(x, y , row[1][2], 28)
            if row[1][1] in pressed_keys:
                color = GREEN
            elif row[1][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[1][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # SETA BAIXO
            rect = pygame.Rect(x, y + 32 , row[2][2], 28)
            if row[2][1] in pressed_keys:
                color = GREEN
            elif row[2][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[2][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            x += 85

             # SETA DIREITA
            rect = pygame.Rect(x, y + 32, row[3][2], 28)
            if row[3][1] in pressed_keys:
                color = GREEN
            elif row[3][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[3][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # PAGEDOWN
            rect = pygame.Rect(x, y, row[5][2], 28)
            if row[5][1] in pressed_keys:
                color = GREEN
            elif row[5][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = pygame.font.SysFont("Arial", 15).render(str(row[5][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)


            continue


        for key_def in row:

            if len(key_def) == 4:
                label, key, w, h = key_def
            else:
                label, key, w = key_def
                h = 60

            rect = pygame.Rect(x, y , w, h)

            if key in pressed_keys:
                color = GREEN
            elif key in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
                
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(label, True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)
            x += w + 5

        if KEY_LAYOUT.index(row) == 0:
            y += 50
            continue
        y += 70



def draw_kb_unlock_button():
    unlocked = set(all_keys).issubset(set(already_pressed))
    color = (50, 255, 50) if unlocked else (200, 200, 200)
    bordercolor = (0, 0, 0) if unlocked else (100, 100, 100)
    pygame.draw.rect(SCREEN, color, kb_button_rect, border_radius=5)
    pygame.draw.rect(SCREEN, bordercolor, kb_button_rect, 2, border_radius=5)
    text = FONT.render("Aprovar", True, bordercolor)
    SCREEN.blit(text, text.get_rect(center=kb_button_rect.center))
    return unlocked

def keyboard_step():
    global MODE
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE=="DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                pressed_keys.add(event.key)
                already_pressed.append(event.key)
                print(event.key)
                if DEV_HOTKEY.issubset(pressed_keys) and MODE=="PROD":
                    print("DEV MODE UNLOCKED via hotkey!")
                    MODE = "DEV"
            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)

        SCREEN.fill((240, 240, 240))
        draw_keyboard()
        unlocked = draw_kb_unlock_button()
        pygame.display.flip()
        CLOCK.tick(60)

        if unlocked:
            draw_text(["✅ Teste de teclado concluído!"], (0, 255, 0))
            add_log({"step":"KEYBOARD_TEST","time":str(datetime.now()), "result":"APROVADO"})
            time.sleep(1)
            running = False


def screen_step():
    colors = [
        (0, 0, 0),       # PRETO
        (255, 255, 255), # BRANCO
        (255, 0, 0),     # VERMELHO
        (0, 255, 0),     # VERDE
        (0, 0, 255),     # AZUL
        (255, 255, 0),   # AMARELO
    ]
    global MODE
    color_index = 0

    running = True
    test_done = False
    approved = None


    legend_font = pygame.font.SysFont("Arial", 18)
    legend_text = "Pressione ENTER para alternar cores e ESPAÇO para finalizar o teste"

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE == "DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.KEYDOWN:
                if not test_done:
                    if event.key == pygame.K_RETURN:
                        color_index = (color_index + 1) % len(colors)
                    elif event.key == pygame.K_SPACE:
                        SCREEN.fill((0, 0, 0))
                        draw_text(["Teste concluído!",
                                   "Aperte Y para APROVAR",
                                   "ou N para REPROVAR"], (0, 255, 0))
                        pygame.display.flip()
                        test_done = True
                else:
                    if event.key == pygame.K_y:
                        approved = True
                        running = False
                    elif event.key == pygame.K_n:
                        approved = False
                        running = False

        if not test_done:
            SCREEN.fill(colors[color_index])

            legend_surface = legend_font.render(legend_text, True, (255, 255, 255))
            legend_rect = legend_surface.get_rect()
            legend_rect.topright = (WIDTH - 30, 20)
            SCREEN.blit(legend_surface, legend_rect)
            pygame.display.flip()

        CLOCK.tick(60)


    result = "APROVADO" if approved else "REPROVADO"
    add_log({"step": "SCREEN_TEST", "time": str(datetime.now()), "result": result})


# ---------------- USB ---------------- #
def port_has_device(bus, port_id):
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        for bus_string in output.split("/:"):
            for line in bus_string.splitlines():
                if port_id in line and "Class=Mass Storage" in line and bus in bus_string:
                    return True
    except Exception as e:
        print("Erro ao executar lsusb:", e)
    return False

# ---------------- VIDEO ---------------- #
video_aprovado = {porta["entry"]: False for porta in VIDEO_PORTS}
def get_video_status():
    drm_path = "/sys/class/drm"
    status_list = []
    all_approved = True
    for porta in VIDEO_PORTS:
        status_file = os.path.join(drm_path, porta["entry"], "status")
        status = "unknown"
        if os.path.isfile(status_file):
            with open(status_file, "r") as f:
                status = f.read().strip()
        if status == "connected":
            video_aprovado[porta["entry"]] = True
        status_list.append({"name": porta["label"], "status": status, "aprovado": video_aprovado[porta["entry"]]})
        if not video_aprovado[porta["entry"]]:
            all_approved = False
    return status_list, all_approved

def draw_video(outputs):
    SCREEN.fill((30, 30, 30))
    y = 50
    all_approved = True
    for o in outputs:
        if o['aprovado']:
            color = (0, 255, 0)
        elif o['status'] == 'connected':
            color = (0, 200, 0)
        else:
            color = (200, 0, 0)
            all_approved = False
        text = FONT.render(f"{o['name']}: {o['status']} {'(aprovado)' if o['aprovado'] else ''}", True, color)
        SCREEN.blit(text, (50, y))
        y += 50
    if all_approved:
        msg = FONT.render("Todas as portas conectadas! Pressione ESC para continuar.", True, (255, 255, 0))
    else:
        msg = FONT.render("Conecte os monitores desconectados...", True, (255, 255, 0))
    SCREEN.blit(msg, (50, y + 20))
    pygame.display.flip()
    return all_approved

# ---------------- ETHERNET ---------------- #
def ethernet_connected():
    carrier_file = f"/sys/class/net/{ETH_INTERFACE}/carrier"
    if os.path.isfile(carrier_file):
        with open(carrier_file, "r") as f:
            status = f.read().strip()
        return status == "1"
    return False

def ethernet_step():
    waiting_remove = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT and MODE=="DEV":
                return
        if not waiting_remove:
            draw_text([f"Conecte o cabo Ethernet ({ETH_INTERFACE})..."])
            if ethernet_connected():
                waiting_remove = True
                time.sleep(0.5)
        else:
            draw_text([f"Remova o cabo Ethernet ({ETH_INTERFACE})..."])
            if not ethernet_connected():
                draw_text([f"Conecte o cabo Ethernet ({ETH_INTERFACE})..."])
                if ethernet_connected():
                    waiting_remove = True
                    time.sleep(0.5)
                    draw_text(["✅ Teste Ethernet concluído!"], (0, 255, 0))
                    add_log({"step":"ETHERNET_TEST","time":str(datetime.now()), "result":"APROVADO"})
                    time.sleep(1)
                    break
        CLOCK.tick(5)

# ---------------- GUI ---------------- #
def draw_text(lines, color=(255, 255, 255)):
    SCREEN.fill((0, 0, 0))
    y = HEIGHT // 3
    for text in lines:
        rendered = FONT.render(text, True, color)
        rect = rendered.get_rect(center=(WIDTH // 2, y))
        SCREEN.blit(rendered, rect)
        y += 50
    pygame.display.flip()

# ---------------- DEV BUTTON ---------------- #
button_rect = pygame.Rect(WIDTH - 180, 20, 200, 200)
button_color = (200, 0, 0)
button_text = FONT.render("DEV MODE", True, (255, 255, 255))


def prompt_password():
    input_text = ""
    active = True
    while active:
        SCREEN.fill((50, 50, 50))
        prompt = FONT.render("Digite senha DEV:", True, (255, 255, 0))
        SCREEN.blit(prompt, (50, 200))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT and MODE=="DEV":
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
    return input_text

# ---------------- MAIN ---------------- #

def start_step():
    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 40, 300, 70)
    waiting = True
    while waiting:
        SCREEN.fill((30, 30, 30))
        # Mensagem de boas-vindas
        title = FONT.render("Bem-vindo ao RevyCheck", True, (255, 255, 255))
        SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 60))
        # Botão
        pygame.draw.rect(SCREEN, (0, 180, 0), button_rect, border_radius=12)
        btn_text = FONT.render("Iniciar testes", True, (255,255,255))
        SCREEN.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2, button_rect.centery - btn_text.get_height()//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    waiting = False
        CLOCK.tick(30)

def main():
    global MODE
    clock = pygame.time.Clock()
    state = "START_STEP"
    step = 0
    waiting_remove = False

    running = True
    while running:

        SCREEN.fill((0,0,0))
        legend_font = pygame.font.SysFont("Arial", 8)  
        legend_surface = legend_font.render(state, True, (255, 255, 255))
        legend_rect = legend_surface.get_rect()
        legend_rect.topright = (WIDTH - 30, 20)
        SCREEN.blit(legend_surface, legend_rect)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if MODE=="DEV":
                    save_log()
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if MODE=="DEV":
                        save_log()
                        pygame.quit()
                        sys.exit()

                pressed_keys.add(event.key)
                print(event.key)

                if DEV_HOTKEY.issubset(pressed_keys) and MODE=="PROD":
                    pswd = prompt_password()
                    if pswd == DEV_PASSWORD:
                        print("DEV MODE UNLOCKED via hotkey!")
                        MODE = "DEV"
                    else:
                        print("Senha incorreta!")
                        pressed_keys.clear()

            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)

        # ---------------- START ---------------- #
        if state == "START_STEP":
            start_step()
            add_log({"step":"TEST_START","time":str(datetime.now()), "result":"APROVADO"})
            state = "SCREEN_STEP"
            continue

        # ---------------- TELA ---------------- #
        if state == "SCREEN_STEP":
            if HAS_EMBEDDED_SCREEN:
                add_log({"step":"SCREEN_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
                screen_step()
            state = "KEYBOARD_STEP"
        # ---------------- TECLADO ---------------- #
        if state == "KEYBOARD_STEP":
            if HAS_EMBEDDED_KEYBOARD:
                add_log({"step":"KEYBOARD_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
                keyboard_step()
            state = "USB_STEP"
        # ---------------- USB ---------------- #
        elif state == "USB_STEP" and step < len(PORT_MAP):
            bus, port_id, port_name = PORT_MAP[step]
            if not waiting_remove:
                add_log({"step":f"USB_CONNECT_TEST_START_{port_name}","time":str(datetime.now()), "result":"APROVADO"})
                draw_text([f"Conecte o pendrive na {port_name}..."])
                if port_has_device(bus, port_id):
                    waiting_remove = True
                    add_log({"step":f"USB_CONNECT_{port_name}","time":str(datetime.now()), "result":"APROVADO"})
                    time.sleep(0.5)
            else:
                draw_text([f"Remova o pendrive da {port_name}..."])
                add_log({"step":f"USB_REMOVE_TEST_START{port_name}","time":str(datetime.now()), "result":"APROVADO"})
                if not port_has_device(bus, port_id):
                    step += 1
                    waiting_remove = False
                    add_log({"step":f"USB_REMOVE_{port_name}","time":str(datetime.now()), "result":"APROVADO"})
                    time.sleep(0.5)
            if step >= len(PORT_MAP):
                state = "VIDEO_STEP"

        # ---------------- VIDEO ---------------- #
        elif state == "VIDEO_STEP":
            add_log({"step":"VIDEO_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
            outputs, all_done = get_video_status()
            draw_video(outputs)
            if all_done:
                draw_text(["Video test ok!"], (0, 255, 0))
                time.sleep(1)
                state = "HEADPHONE_STEP" if HAS_HEADPHONE_JACK else "SPEAKER_STEP"

        # ---------------- HEADPHONE ---------------- #
        elif state == "HEADPHONE_STEP":
            add_log({"step":"HEADPHONE_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
            draw_text(["Conecte o headphone..."])
            if headphone_connected():
                add_log({"step":"HEADPHONE_CONNECT","time":str(datetime.now()), "result":"APROVADO"})
                state = "HEADPHONE_TESTING"
                time.sleep(0.5)

        elif state == "HEADPHONE_TESTING":
            add_log({"step":"HEADPHONE_TESTING","time":str(datetime.now()), "result":"APROVADO"})
            play_headphone_sequence()
            state = "HEADPHONE_REMOVE"

        elif state == "HEADPHONE_REMOVE":
            draw_text(["Remova o headphone..."])
            if not headphone_connected():
                add_log({"step":"HEADPHONE_REMOVE","time":str(datetime.now()), "result":"APROVADO"})
                state = "SPEAKER_STEP"
                time.sleep(0.5)

        # ---------------- SPEAKER ---------------- #
        elif state == "SPEAKER_STEP":
            if HAS_SPEAKER:
                add_log({"step":"SPEAKER_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
                play_speaker_sequence()
            state = "MIC_STEP"

        # ---------------- MICROFONE ---------------- #
        elif state == "MIC_STEP":
            if HAS_MICROPHONE:
                add_log({"step":"MICROPHONE_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
                test_microphone_bip()
            state = "ETHERNET_STEP"

        # ---------------- ETHERNET ---------------- #
        elif state == "ETHERNET_STEP":
            if HAS_ETHERNET_PORT:
                add_log({"step":"ETHERNET_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
                ethernet_step()
            state = "DONE"

        # ---------------- DONE ---------------- #
        elif state == "DONE":
            draw_text(["Todos os testes concluídos! Salvando log..."], (0, 255, 0))
            add_log({"step": "TEST_STOP", "time": str(datetime.now()), "result": "APROVADO"})
            save_log()
            SCREEN.fill(WHITE)
            draw_text(["Todos os testes concluídos!"], (0, 0, 0))
            pygame.display.flip()
            time.sleep(5)
            running = False
            

        CLOCK.tick(10)

def save_log():

    with open("checklist_log.json","w") as f:
        json.dump(log_data, f, indent=2)


    try:
        conn2 = mysql.connector.connect(
            host="revy.selbetti.com.br",
            user="drack",
            password="jdVg2dF2@",
            database="revycheck"
        )
        cursor = conn2.cursor()

        try:
            device_serial = subprocess.check_output("cat /sys/class/dmi/id/product_serial", shell=True).strip().decode("utf-8")
        except Exception:
            device_serial = "unknown"
        for entry in log_data:
            step = entry.get("step", "")
            time_str = entry.get("time", None)

            if time_str:
                try:
                    time_val = datetime.fromisoformat(time_str)
                except Exception:
                    time_val = datetime.now()
            else:
                time_val = datetime.now()
            approved = entry.get("result", "REPROVADO") == "APROVADO"
            print(f"Salvando log: {device_serial}, {step}, {time_val}, {approved}")

            cursor.execute(
                "INSERT INTO logs (device_serial, step, time, approved) VALUES (%s, %s, %s, %s)",
                (device_serial, step, time_val, approved)
            )
        conn2.commit()
        cursor.close()
        conn2.close()
        return "Log salvo com sucesso!"
    except Exception as e:
        return f"Erro ao salvar log no banco: {e}"


if __name__ == "__main__":
    disable_alt_tab()
    try:
        main()
    finally:
        restore_alt_tab()
        pygame.quit()
        sys.exit()