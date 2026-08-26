import json
import sys
import time

import pygame

from src import api_client, app_state, config, hal
from src.functions.gui import draw_text


def _caminho_log_local():
    """Onde gravar a copia local do log.

    Caminho absoluto derivado do executavel, e nao relativo: rodando de um
    compartilhamento UNC o `cmd.exe` nao aceita UNC como diretorio atual e cai
    para `C:\\Windows`, entao o log ia parar num lugar indefinido da maquina
    que vai para o cliente.
    """
    return config.base_dir() / "checklist_log.json"


def save_log():
    destino = _caminho_log_local()
    try:
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(app_state.LOG_DATA, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        # Share somente-leitura e' o caso normal em producao; o envio para a
        # API e' que importa, a copia local e' conveniencia de depuracao.
        print(f"Nao foi possivel gravar {destino}: {exc}")

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

    def try_send_log():
        """Envia o log para /revy-check/testefinal.

        A API insere tudo numa transacao so', entao repetir depois de uma falha
        de rede nao duplica os passos que ja' entraram.
        """
        try:
            resposta = api_client.enviar_teste_final(
                hal.serial_number(), app_state.LOG_DATA
            )
        except api_client.ApiError as exc:
            return False, str(exc)

        gravados = resposta.get("inserted", 0)
        reprovados = resposta.get("reprovados", 0)
        return True, f"Log enviado: {gravados} passos, {reprovados} reprovados."

    while True:
        success, result = try_send_log()

        if success:
            draw_text(["✅ Log salvo com sucesso!"], (0, 180, 0))
            time.sleep(2)
            return result

        app_state.SCREEN.fill((255, 255, 255))
        retry_font = pygame.font.SysFont("Arial", 14, bold=True)
        retry_btn = pygame.Rect(app_state.WIDTH // 2 - 160, app_state.HEIGHT - 80, 140, 50)
        cancel_retry_btn = pygame.Rect(app_state.WIDTH // 2 + 20, app_state.HEIGHT - 80, 140, 50)

        if app_state.MODE == "DEV":
            msg_lines = ["Erro ao enviar o log:", str(result)]
        else:
            msg_lines = ["Erro ao enviar o log!"]

        draw_text(msg_lines, (255, 0, 0))

        pygame.draw.rect(app_state.SCREEN, (0, 120, 220), retry_btn, border_radius=10)
        pygame.draw.rect(app_state.SCREEN, (200, 0, 0), cancel_retry_btn, border_radius=10)
        app_state.SCREEN.blit(retry_font.render("Tentar novamente", True, (255, 255, 255)), retry_btn.move(14, 10))
        app_state.SCREEN.blit(retry_font.render("Cancelar", True, (255, 255, 255)), cancel_retry_btn.move(20, 10))
        pygame.display.flip()

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
            app_state.CLOCK.tick(30)
