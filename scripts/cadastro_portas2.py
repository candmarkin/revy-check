#!/usr/bin/env python3
import subprocess
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
import mysql.connector
from mysql.connector import Error

# ----------------- FUNCOES AUXILIARES -----------------
def has_pendrive_connected():
    try:
        outputA = subprocess.check_output(["lsusb", "-t"], text=True)
        return "Class=Mass Storage" in str(outputA)
    except Exception:
        return False

def ask_yes_no(question):
    return messagebox.askyesno("Pergunta", question)

def ask_text(question, default=""):
    return simpledialog.askstring("Cadastro", question, initialvalue=default)

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

# ----------------- INICIO DA INTERFACE -----------------
root = tk.Tk()
root.withdraw()

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
                        PORT_MAP.append({"bus": bus, "port": f"Port: {port_id}:", "label": new_port})
                        wait_for_ok("Porta cadastrada com sucesso!\n\nRemova todos os pendrives conectados...")
        # espera remoção do pendrive
        temusb = has_pendrive_connected()
        while temusb:
            time.sleep(1)
            temusb = has_pendrive_connected()

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
