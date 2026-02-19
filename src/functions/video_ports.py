import os

import pygame

from src import app_state
from src.functions.system_info import draw_system_info

video_aprovado = {}


def init_video_state(video_ports):
    global video_aprovado
    video_aprovado = {porta["entry"]: False for porta in video_ports}


def get_video_status(video_ports):
    drm_path = "/sys/class/drm"
    status_list = []
    all_approved = True
    for porta in video_ports:
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
    app_state.SCREEN.fill((30, 30, 30))
    draw_system_info(app_state.SYSTEM_INFO)

    y = 100
    all_approved = True
    for o in outputs:
        if o["aprovado"]:
            color = (0, 255, 0)
        elif o["status"] == "connected":
            color = (0, 200, 0)
        else:
            color = (200, 0, 0)
            all_approved = False
        text = app_state.FONT.render(
            f"{o['name']}: {o['status']} {'(aprovado)' if o['aprovado'] else ''}",
            True,
            color,
        )
        app_state.SCREEN.blit(text, (50, y))
        y += 50
    if all_approved:
        msg = app_state.FONT.render(
            "Todas as portas conectadas! Pressione ESC para continuar.",
            True,
            (255, 255, 0),
        )
    else:
        msg = app_state.FONT.render("Conecte os monitores desconectados...", True, (255, 255, 0))
    app_state.SCREEN.blit(msg, (50, y + 20))
    pygame.display.flip()
    return all_approved
