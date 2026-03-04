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

    def try_save_log_to_db(force_error=False):
        conn2 = None
        cursor = None

        try:
            conn2 = mysql.connector.connect(
            host="revycheck.mysql.uhserver.com",
            user="drack",
            password="AkonShowLA2002@",
            database="revycheck",
        )
            cursor = conn2.cursor()
            
            # fake error for testing retry logic
            if force_error:
                raise Exception("Simulated database error for testing")

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
            return True, "Log salvo com sucesso!"
        except Exception as e:
            return False, str(e)
        finally:
            if cursor is not None:
                cursor.close()
            if conn2 is not None:
                conn2.close()

    # Retry loop: user can click 'Tentar novamente' to attempt save; show status while attempting
    attempt = 1
    while True:
        # Attempt to save only after user requests a retry (or first auto-attempt)
        # Show saving status before attempting so user sees change
        saving_msg = [f"Salvando no banco de dados...", f"Tentativa {attempt}"]
        draw_text(saving_msg, (0, 120, 220))
        pygame.display.flip()

        # Let the event queue process so UI stays responsive
        pygame.event.pump()

        success, result = try_save_log_to_db(force_error=False)

        if success:
            draw_text(["✅ Log salvo com sucesso!"], (0, 180, 0))
            time.sleep(2)
            return result

        # Failed - show error and present retry/cancel buttons with updated message
        app_state.SCREEN.fill((255, 255, 255))
        retry_font = pygame.font.SysFont("Arial", 14, bold=True)
        retry_btn = pygame.Rect(app_state.WIDTH // 2 - 160, app_state.HEIGHT - 80, 140, 50)
        cancel_retry_btn = pygame.Rect(app_state.WIDTH // 2 + 20, app_state.HEIGHT - 80, 140, 50)

        if app_state.MODE == "DEV":
            msg_lines = ["Erro ao salvar log no BD:", str(result), "Clique em 'Tentar novamente' para nova tentativa."]
        else:
            msg_lines = ["Erro ao salvar log no BD!", "Clique em 'Tentar novamente' para nova tentativa."]

        # Display error lines plus attempt counter
        msg_lines.append(f"Tentativa: {attempt}")
        draw_text(msg_lines, (255, 0, 0))

        pygame.draw.rect(app_state.SCREEN, (0, 120, 220), retry_btn, border_radius=10)
        pygame.draw.rect(app_state.SCREEN, (200, 0, 0), cancel_retry_btn, border_radius=10)
        app_state.SCREEN.blit(retry_font.render("Tentar novamente", True, (255, 255, 255)), retry_btn.move(14, 10))
        app_state.SCREEN.blit(retry_font.render("Cancelar", True, (255, 255, 255)), cancel_retry_btn.move(20, 10))
        pygame.display.flip()

        # Wait for user action (retry or cancel)
        retry_waiting = True
        while retry_waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if retry_btn.collidepoint(event.pos):
                        retry_waiting = False
                    elif cancel_retry_btn.collidepoint(event.pos):
                        draw_text(["❌ Envio cancelado após falha."], (200, 0, 0))
                        time.sleep(2)
                        return result
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        retry_waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        draw_text(["❌ Envio cancelado após falha."], (200, 0, 0))
                        time.sleep(2)
                        return result
            app_state.CLOCK.tick(30)

        attempt += 1
