import json
import subprocess
import sys
import time
from datetime import datetime

import mysql.connector
import pygame

from src import app_state
from src.functions.gui import draw_text


def save_log():
    with open("checklist_log.json", "w") as f:
        json.dump(app_state.LOG_DATA, f, indent=2)

    app_state.SCREEN.fill((255, 255, 255))
    font_small = pygame.font.SysFont("Consolas", 10)
    font_big = pygame.font.SysFont("Arial", 14, bold=True)

    y = 50
    app_state.SCREEN.blit(font_big.render("Pré-visualização do log:", True, (0, 0, 0)), (50, y))
    y += 40

    for entry in app_state.LOG_DATA[-15:]:
        text = f"{entry.get('step', '?')} | {entry.get('result', '?')} | {entry.get('time', '')}"
        app_state.SCREEN.blit(font_small.render(text, True, (0, 0, 0)), (60, y))
        y += 25
        if y > app_state.HEIGHT - 120:
            app_state.SCREEN.blit(font_small.render("... (log truncado) ...", True, (150, 0, 0)), (60, y))
            break

    send_btn = pygame.Rect(app_state.WIDTH // 2 - 160, app_state.HEIGHT - 80, 140, 50)
    cancel_btn = pygame.Rect(app_state.WIDTH // 2 + 20, app_state.HEIGHT - 80, 140, 50)
    pygame.draw.rect(app_state.SCREEN, (0, 200, 0), send_btn, border_radius=10)
    pygame.draw.rect(app_state.SCREEN, (200, 0, 0), cancel_btn, border_radius=10)
    app_state.SCREEN.blit(font_big.render("Enviar", True, (255, 255, 255)), send_btn.move(25, 10))
    app_state.SCREEN.blit(font_big.render("Cancelar", True, (255, 255, 255)), cancel_btn.move(10, 10))
    pygame.display.flip()

    decision = None
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if send_btn.collidepoint(event.pos):
                    decision = "enviar"
                    waiting = False
                elif cancel_btn.collidepoint(event.pos):
                    decision = "cancelar"
                    waiting = False
        app_state.CLOCK.tick(30)

    if decision == "cancelar":
        draw_text(["❌ Envio cancelado pelo usuário."], (200, 0, 0))
        time.sleep(2)
        return "Envio cancelado"

    try:
        conn2 = mysql.connector.connect(
            host="10.3.0.12",
            user="drack",
            password="jdVg2dF2@",
            database="revycheck",
        )
        cursor = conn2.cursor()

        try:
            device_serial = subprocess.check_output(
                "cat /sys/class/dmi/id/product_serial", shell=True
            ).strip().decode("utf-8")
        except Exception:
            device_serial = "unknown"

        for entry in app_state.LOG_DATA:
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

            cursor.execute(
                "INSERT INTO logs (device_serial, step, time, approved) VALUES (%s, %s, %s, %s)",
                (device_serial, step, time_val, approved),
            )

        conn2.commit()
        cursor.close()
        conn2.close()
        draw_text(["✅ Log salvo com sucesso!"], (0, 180, 0))
        time.sleep(2)
        return "Log salvo com sucesso!"

    except Exception as e:
        color = (255, 0, 0)
        if app_state.MODE == "DEV":
            msg = f"Erro ao salvar log no BD:\n{e}"
        else:
            msg = "Erro ao salvar log no BD!"
        app_state.SCREEN.fill((255, 255, 255))
        draw_text([msg], color)
        pygame.display.flip()
        time.sleep(3)
        return str(e)
