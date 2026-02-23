import subprocess
import time

import mysql.connector
import tkinter as tk
from tkinter import messagebox, simpledialog


def has_pendrive_connected_cd():
    try:
        outputA = subprocess.check_output(["lsusb", "-t"], text=True)
        return "Class=Mass Storage" in str(outputA)
    except Exception:
        return False


def ask_yes_no(question):
    return messagebox.askyesno("Pergunta", question)


def ask_text(prompt):
    root = tk.Tk()
    root.withdraw()

    dialog = tk.Toplevel(root)
    dialog.title("Entrada")
    dialog.geometry("450x150")
    dialog.resizable(False, False)

    dialog.attributes("-topmost", True)
    dialog.lift()
    dialog.focus_force()
    dialog.grab_set()

    label = tk.Label(dialog, text=prompt, anchor="w", justify="left", wraplength=430)
    label.pack(pady=(10, 5), padx=10)

    entry = tk.Entry(dialog, width=45, font=("DejaVu Sans", 12))
    entry.pack(pady=5)
    entry.focus_set()

    result = None

    def confirm():
        nonlocal result
        result = entry.get().strip()
        dialog.destroy()

    def cancel():
        nonlocal result
        result = ""
        dialog.destroy()

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="OK", width=10, command=confirm).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancelar", width=10, command=cancel).pack(side="left", padx=5)

    dialog.bind("<Return>", lambda e: confirm())
    dialog.bind("<Escape>", lambda e: cancel())

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
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            connection_timeout=5,
        )
        if conn.is_connected():
            return True, conn
        return False, "Não conectado"
    except Exception as e:
        return False, str(e)


def send_to_db(
    conn,
    productname,
    has_screen,
    has_keyboard,
    has_eth,
    eth_interface,
    has_speaker,
    has_headphone,
    has_mic,
    has_wifi,
    has_touchpad,
    has_camera,
    port_map,
    video_ports,
):
    cursor = conn.cursor()
    try:
        insert_device = (
            "INSERT INTO devices "
            "(name, type, has_embedded_screen, has_embedded_keyboard, has_ethernet, "
            "eth_interface, has_speaker, has_headphone_jack, has_microphone, "
            "has_wifi, has_touchpad, has_camera) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        device_vals = (
            productname,
            "Notebook",
            1 if has_screen else 0,
            1 if has_keyboard else 0,
            1 if has_eth else 0,
            eth_interface,
            1 if has_speaker else 0,
            1 if has_headphone else 0,
            1 if has_mic else 0,
            1 if has_wifi else 0,
            1 if has_touchpad else 0,
            1 if has_camera else 0,
        )
        cursor.execute(insert_device, device_vals)
        dev_id = cursor.lastrowid

        if port_map:
            insert_usb = "INSERT INTO device_usb_ports (device_id, bus, port, label) VALUES (%s, %s, %s, %s)"
            usb_vals = [(dev_id, p["bus"], p["port"], p["label"]) for p in port_map]
            cursor.executemany(insert_usb, usb_vals)

        if video_ports:
            insert_vid = "INSERT INTO device_video_ports (device_id, label, entry) VALUES (%s, %s, %s)"
            vid_vals = [(dev_id, v["label"], v["entry"]) for v in video_ports]
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

    messagebox.showinfo(
        "Banco de Dados",
        "Antes de iniciar, vamos conectar ao banco MySQL.\n\n"
        "Se a rede não estiver ativa, conecte e clique em Tentar novamente.",
    )

    db_cfg = {}
    connected = False
    db_conn = None

    while not connected:
        db_cfg["host"] = "10.3.0.12"
        db_cfg["port"] = 3306
        db_cfg["user"] = "drack"
        db_cfg["password"] = "jdVg2dF2@"
        db_cfg["database"] = "revycheck"

        ok, result = try_connect_db(db_cfg)
        if ok:
            connected = True
            db_conn = result
            messagebox.showinfo(
                "OK",
                f"Conectado ao banco {db_cfg['host']}:{db_cfg['port']} -> {db_cfg['database']}",
            )
            break
        retry = messagebox.askretrycancel(
            "Erro de conexão",
            f"Falha ao conectar: {result}\n\nConecte a rede (ou verifique dados) e tente novamente.",
        )
        if not retry:
            messagebox.showwarning("Cancelado", "Operação cancelada pelo usuário. Encerrando.")
            root.destroy()
            raise SystemExit(0)

    try:
        manufacturer = subprocess.check_output(
            "cat /sys/class/dmi/id/sys_vendor", shell=True
        ).strip().decode("utf-8")
    except Exception:
        manufacturer = ""
    try:
        if "LENOVO" in str(manufacturer).upper():
            productname = subprocess.check_output(
                "cat /sys/class/dmi/id/product_version", shell=True
            ).strip().decode("utf-8")
        else:
            productname = subprocess.check_output(
                "cat /sys/class/dmi/id/product_name", shell=True
            ).strip().decode("utf-8")
    except Exception:
        productname = "UnknownDevice"

    port_map = []
    video_ports = []

    messagebox.showinfo(
        "Início",
        f"Antes de cadastrar as portas, algumas perguntas sobre o hardware do seu {productname}:",
    )

    has_screen = ask_yes_no("Seu dispositivo possui tela embutida?")
    has_keyboard = ask_yes_no("Seu dispositivo possui teclado embutido?")
    has_eth = ask_yes_no("Seu dispositivo possui porta Ethernet?")

    eth_interface = ""
    if has_eth:
        try:
            ipaddr_output = subprocess.check_output("ip addr", shell=True).decode("utf-8")
            messagebox.showinfo("Interfaces detectadas", ipaddr_output)
        except Exception:
            pass
        eth_interface = ask_text("Qual é a interface Ethernet do seu dispositivo? (Ex.: eno2)") or ""

    has_speaker = ask_yes_no("Seu dispositivo possui alto-falante?")
    has_headphone = ask_yes_no("Seu dispositivo possui entrada para fone de ouvido?")
    has_microphone = ask_yes_no("Seu dispositivo possui microfone embutido?")
    has_wifi = ask_yes_no("Seu dispositivo possui WiFi?")
    has_touchpad = ask_yes_no("Seu dispositivo possui touchpad?")
    has_camera = ask_yes_no("Seu dispositivo possui camera?")

    messagebox.showinfo(
        "Cadastro",
        "Agora, vamos cadastrar as portas de vídeo onde você conecta os monitores externos.",
    )

    new_video_port = ask_text(
        "Dê um nome para a porta de vídeo que deseja cadastrar (Ex.: HDMI Esquerdo)\n\n** Deixe vazio para finalizar **"
    )
    while new_video_port:
        wait_for_ok(f"Conecte o cabo de vídeo na porta {new_video_port} e clique em OK...")

        while True:
            try:
                videoports = subprocess.check_output("ls /sys/class/drm/", shell=True).decode("utf-8").split()
                videoports = [port for port in videoports if "-" in port]
                for port in videoports:
                    try:
                        isconnected = subprocess.check_output(
                            f"cat /sys/class/drm/{port}/status", shell=True
                        ).decode("utf-8").strip()
                    except Exception:
                        isconnected = ""
                    if (
                        isconnected == "connected"
                        and port not in [v.get("entry") for v in video_ports]
                        and port != "card0-eDP-1"
                    ):
                        confirm = messagebox.askyesno(
                            "Confirmação",
                            f"Porta detectada: {port}\nLabel: {new_video_port}\n\nConfirmar cadastro?",
                        )
                        if confirm:
                            video_ports.append({"label": new_video_port, "entry": port})
                            wait_for_ok(
                                "Porta de vídeo cadastrada com sucesso!\n\nRemova todos os cabos de vídeo conectados..."
                            )
                            while True:
                                try:
                                    if port == "card1-eDP-1":
                                        break
                                    still_connected = subprocess.check_output(
                                        f"cat /sys/class/drm/{port}/status", shell=True
                                    ).decode("utf-8").strip()
                                except Exception:
                                    still_connected = ""
                                if still_connected == "connected":
                                    time.sleep(1)
                                else:
                                    break
            except Exception:
                pass
            break
        new_video_port = ask_text("Dê um nome para a próxima porta de vídeo (ou vazio para finalizar)")

    messagebox.showinfo(
        "Cadastro",
        "Agora, vamos cadastrar as portas USB onde você conecta os pendrives.",
    )

    new_port = ask_text("Dê um nome para a porta (Ex.: USB-C Esquerdo 1)\n\n** Deixe vazio para finalizar **")
    while new_port:
        wait_for_ok(f"Conecte o pendrive na porta {new_port} e clique em OK...")

        try:
            output = subprocess.check_output(["lsusb", "-t"], text=True)
            for bus_string in output.split("/:"):
                bus_list = bus_string.splitlines()
                for line in bus_list:
                    if "Class=Mass Storage" in line and "Bus 002.Port 001" not in bus_list[bus_list.index(line) - 1]:
                        try:
                            port_id = line.split(":")[0].split()[-1]
                        except Exception:
                            port_id = "unknown"
                        try:
                            bus = bus_string.splitlines()[0].split(":")[0].strip()
                        except Exception:
                            bus = "unknown"
                        confirm = messagebox.askyesno(
                            "Confirmação",
                            f"Bus: {bus}\nPorta: {port_id}\nLabel: {new_port}\n\nConfirmar cadastro?",
                        )
                        if confirm:
                            port_map.append({"bus": bus, "port": f"Port {port_id}:", "label": new_port})
                            wait_for_ok(
                                "Porta cadastrada com sucesso!\n\nRemova todos os pendrives conectados..."
                            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar lsusb: {e}")

        new_port = ask_text("Dê um nome para a próxima porta (ou vazio para finalizar)")

    resumo = "Resumo do cadastro:\n\n"
    for port in port_map:
        resumo += f"USB -> Bus: {port['bus']}, Porta: {port['port']}, Label: {port['label']}\n"
    for vport in video_ports:
        resumo += f"Vídeo -> Porta: {vport['entry']}, Label: {vport['label']}\n"

    resumo += f"\nTela embutida? {'Sim' if has_screen else 'Não'}"
    resumo += f"\nTeclado embutido? {'Sim' if has_keyboard else 'Não'}"
    resumo += f"\nEthernet? {'Sim' if has_eth else 'Não'}"
    resumo += f"\nAlto-falante? {'Sim' if has_speaker else 'Não'}"
    resumo += f"\nFone de ouvido? {'Sim' if has_headphone else 'Não'}"
    resumo += f"\nMicrofone? {'Sim' if has_microphone else 'Não'}"
    resumo += f"\nWiFi? {'Sim' if has_wifi else 'Não'}"
    resumo += f"\nTouchpad? {'Sim' if has_touchpad else 'Não'}"
    resumo += f"\nCamera? {'Sim' if has_camera else 'Não'}"
    resumo += f"\nInterface Ethernet: {eth_interface}"
    resumo += f"\nNome do produto: {productname}"

    confirm = messagebox.askyesno("Resumo", resumo + "\n\nEstá tudo correto?")

    if confirm:
        success, err = send_to_db(
            db_conn,
            productname,
            has_screen,
            has_keyboard,
            has_eth,
            eth_interface,
            has_speaker,
            has_headphone,
            has_microphone,
            has_wifi,
            has_touchpad,
            has_camera,
            port_map,
            video_ports,
        )
        if success:
            messagebox.showinfo("Sucesso", "Dados inseridos no banco com sucesso!")
        else:
            messagebox.showerror("Erro ao inserir", f"Erro ao inserir no banco: {err}")
    else:
        messagebox.showinfo("Cancelado", "Cadastro cancelado pelo usuário. Nenhum dado foi enviado ao banco.")

    try:
        if db_conn:
            db_conn.close()
    except Exception:
        pass

    root.destroy()
