import time

import mysql.connector
import tkinter as tk
from tkinter import messagebox, simpledialog

from src import hal


def has_pendrive_connected_cd():
    return bool(hal.mass_storage_port_ids())


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
    vendor,
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
        # As portas sao gravadas no formato do SO onde o cadastro foi feito, e
        # os formatos nao se traduzem entre Linux e Windows -- por isso a
        # coluna `platform` entra junto. Bancos anteriores a
        # scripts/add_platform_column.sql caem no INSERT sem ela.
        columns = (
            "name, cpu_vendor, type, has_embedded_screen, has_embedded_keyboard, "
            "has_ethernet, eth_interface, has_speaker, has_headphone_jack, "
            "has_microphone, has_wifi, has_touchpad, has_camera"
        )
        device_vals = (
            productname,
            vendor,
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
        try:
            cursor.execute(
                f"INSERT INTO devices ({columns}, platform) "
                f"VALUES ({', '.join(['%s'] * (len(device_vals) + 1))})",
                device_vals + (hal.PLATFORM,),
            )
        except mysql.connector.Error as exc:
            if exc.errno != 1054:  # ER_BAD_FIELD_ERROR
                raise
            print(
                "AVISO: tabela devices sem a coluna 'platform'. "
                "Rode scripts/add_platform_column.sql."
            )
            cursor.execute(
                f"INSERT INTO devices ({columns}) "
                f"VALUES ({', '.join(['%s'] * len(device_vals))})",
                device_vals,
            )
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


def list_connected_video_ports():
    """Saidas de video externas conectadas agora, no formato do backend."""
    return hal.connected_video_ports()


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

    manufacturer, productname = hal.dmi()

    # Distingue as variantes Intel e AMD do mesmo modelo comercial: o DMI e'
    # identico nas duas, mas a topologia USB e os connectors DRM nao sao.
    vendor = hal.cpu_vendor()

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
        detectadas = hal.ethernet_interfaces()
        if detectadas:
            messagebox.showinfo(
                "Interfaces detectadas",
                "\n".join(f"{name}  --  {desc}" for name, desc in detectadas),
            )
        # Quando so' existe uma placa cabeada ela ja' vem preenchida: no
        # Windows o nome ('Ethernet 6') nao e' obvio para quem esta' na
        # bancada, e digitar errado reprova o teste de rede inteiro.
        sugestao = detectadas[0][0] if len(detectadas) == 1 else ""
        pergunta = "Qual é a interface Ethernet do seu dispositivo?"
        if sugestao:
            pergunta += f"\n\n(Detectada apenas uma: {sugestao})"
        eth_interface = ask_text(pergunta) or sugestao

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
        # Fotografa as portas ja conectadas ANTES de pedir o novo cabo. Se uma
        # porta nova aparecer depois do OK, ela e' a certa mesmo com outros
        # cabos plugados. Cabo que ja estava conectado antes de comecar (a
        # maquina foi ligada com ele) nao gera delta -- ver fallback abaixo.
        baseline = list_connected_video_ports()
        wait_for_ok(f"Conecte o cabo de vídeo na porta {new_video_port} e clique em OK...")

        if not hal.video_available():
            messagebox.showerror(
                "Sem driver de vídeo",
                f"{hal.NO_VIDEO_DRIVER_HINT}\n\n"
                "Não é possível cadastrar portas de vídeo neste estado.",
            )
            break

        while True:
            time.sleep(1)  # tempo para o SO atualizar o status da saida de video
            registradas = {hal.video_connector_name(v.get("entry")) for v in video_ports}
            conectadas = list_connected_video_ports()
            novas = (conectadas - baseline) - registradas

            if len(novas) > 1:
                if not messagebox.askretrycancel(
                    "Mais de uma porta detectada",
                    "Foram detectadas várias portas novas:\n\n"
                    + ", ".join(sorted(novas))
                    + "\n\nConecte apenas um cabo por vez e tente novamente.",
                ):
                    break
                baseline = list_connected_video_ports()
                continue

            if novas:
                connector = novas.pop()
            else:
                # Nenhum delta: ou o cabo ja estava conectado desde o boot, ou
                # nao foi conectado nada.
                candidatas = conectadas - registradas
                if len(candidatas) == 1:
                    connector = next(iter(candidatas))
                elif candidatas:
                    # Varios cabos ja plugados e nenhum delta: identifica pela
                    # remocao, que e' a unica pista possivel nesse estado.
                    wait_for_ok(
                        f"Não foi possível identificar a porta '{new_video_port}' automaticamente "
                        "(o cabo já estava conectado).\n\n"
                        f"DESCONECTE o cabo da porta {new_video_port} e clique em OK..."
                    )
                    time.sleep(1)
                    removidas = candidatas - list_connected_video_ports()
                    if len(removidas) != 1:
                        if not messagebox.askretrycancel(
                            "Porta não identificada",
                            "Não foi possível identificar a porta pela remoção do cabo.\n\n"
                            f"Reconecte o cabo apenas na porta {new_video_port} e tente novamente.",
                        ):
                            break
                        baseline = list_connected_video_ports()
                        continue
                    connector = removidas.pop()
                else:
                    todas_cadastradas = bool(conectadas) and not (conectadas - registradas)
                    detalhe = (
                        "Todas as portas conectadas já estão cadastradas: "
                        + ", ".join(sorted(conectadas))
                        + "."
                        if todas_cadastradas
                        else "Verifique se o cabo está conectado."
                    )
                    if not messagebox.askretrycancel(
                        "Nenhuma porta nova",
                        f"Nenhuma porta de vídeo nova foi detectada para '{new_video_port}'.\n\n"
                        + detalhe
                        + "\n\nTente novamente.",
                    ):
                        break
                    continue

            confirm = messagebox.askyesno(
                "Confirmação",
                f"Porta detectada: {connector}\nLabel: {new_video_port}\n\nConfirmar cadastro?",
            )
            if confirm:
                video_ports.append({"label": new_video_port, "entry": connector})
                messagebox.showinfo(
                    "Cadastro",
                    "Porta de vídeo cadastrada com sucesso!\n\n"
                    "Você pode manter o cabo conectado para cadastrar as próximas portas.",
                )
                break

            if not messagebox.askretrycancel(
                "Cadastro cancelado",
                f"A porta {connector} não foi cadastrada.\n\nDeseja tentar novamente?",
            ):
                break
            baseline = list_connected_video_ports()
        new_video_port = ask_text("Dê um nome para a próxima porta de vídeo (ou vazio para finalizar)")

    messagebox.showinfo(
        "Cadastro",
        "Agora, vamos cadastrar as portas USB onde você conecta os pendrives.",
    )

    new_port = ask_text("Dê um nome para a porta (Ex.: USB-C Esquerdo 1)\n\n** Deixe vazio para finalizar **")
    while new_port:
        wait_for_ok(f"Conecte o pendrive na porta {new_port} e clique em OK...")

        # A porta e' identificada pelo caminho fisico -- sysfs no Linux,
        # location path no Windows -- e nao por indice de enumeracao: os
        # numeros de bus mudam entre variantes Intel e AMD do mesmo modelo e
        # chegam a mudar entre boots, conforme a ordem de probe dos
        # controladores xHCI. O formato do ID muda entre os dois SOs, por isso
        # o cadastro e' por plataforma (scripts/add_platform_column.sql).
        ja_cadastradas = {f"{p['bus']}/{p['port']}" for p in port_map}
        encontradas = hal.mass_storage_ports()
        detectadas = sorted(pid for pid in encontradas if pid not in ja_cadastradas)

        if not detectadas:
            messagebox.showwarning(
                "Nada detectado",
                "Nenhum pendrive novo encontrado.\n\n"
                "Confirme que o dispositivo está conectado e é de armazenamento.",
            )

        for port_id in detectadas:
            controlador, cadeia = port_id.split("/", 1)
            # Dica de posicao no chassi: ACPI _PLD no Linux (kernel >= 5.18),
            # ultimo no' ACPI do location path no Windows ('HS10'). Ajuda o
            # operador a conferir se rotulou o lado certo; nem toda maquina
            # preenche.
            painel = encontradas.get(port_id)
            lado = f"Lado (ACPI): {painel}" if painel else "Lado (ACPI): nao informado"
            confirm = messagebox.askyesno(
                "Confirmação",
                f"Controlador: {controlador}\nPorta física: {cadeia}\n{lado}\nLabel: {new_port}\n\nConfirmar cadastro?",
            )
            if confirm:
                port_map.append({"bus": controlador, "port": cadeia, "label": new_port})
                wait_for_ok("Porta cadastrada com sucesso!\n\nRemova todos os pendrives conectados...")
                while port_id in hal.mass_storage_port_ids():
                    time.sleep(1)

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
    resumo += f"\nCPU: {vendor or 'desconhecida'}"

    confirm = messagebox.askyesno("Resumo", resumo + "\n\nEstá tudo correto?")

    if confirm:
        success, err = send_to_db(
            db_conn,
            productname,
            vendor,
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
