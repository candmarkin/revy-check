import pygame

from src import app_state
from src.functions.hw_paths import drm_available, drm_connector_status
from src.functions.system_info import draw_system_info

# Status sintetico usado quando nao existe nenhum connector em /sys/class/drm:
# sem isso o teste reprovava as portas em silencio, escondendo que o problema
# e' o driver de video e nao o cabo.
NO_DRM = "driver de video ausente"

video_aprovado = {}


def init_video_state(video_ports):
    global video_aprovado
    video_aprovado = {porta["entry"]: False for porta in video_ports}


def get_video_status(video_ports):
    driver_ok = drm_available()
    status_list = []
    all_approved = True
    for porta in video_ports:
        entry = porta["entry"]
        # O connector e' procurado pelo nome ('HDMI-A-1'), nao pela entrada
        # completa ('card0-HDMI-A-1'): o indice do card muda conforme o driver
        # que carregou.
        status = drm_connector_status(entry) if driver_ok else NO_DRM
        if status == "connected":
            video_aprovado[entry] = True
        status_list.append({"name": porta["label"], "status": status, "aprovado": video_aprovado[entry]})
        if not video_aprovado[entry]:
            all_approved = False
    return status_list, all_approved


def draw_video(outputs):
    app_state.SCREEN.fill((30, 30, 30))
    draw_system_info(app_state.SYSTEM_INFO)

    y = 100
    all_approved = True
    sem_driver = False
    for o in outputs:
        if o["aprovado"]:
            color = (0, 255, 0)
        elif o["status"] == "connected":
            color = (0, 200, 0)
        else:
            color = (200, 0, 0)
            all_approved = False
            if o["status"] == NO_DRM:
                sem_driver = True
        text = app_state.FONT.render(
            f"{o['name']}: {o['status']} {'(aprovado)' if o['aprovado'] else ''}",
            True,
            color,
        )
        app_state.SCREEN.blit(text, (50, y))
        y += 50
    if sem_driver:
        msg = app_state.FONT.render(
            "Nenhum connector em /sys/class/drm. Verifique: dmesg | grep -i 'firmware load'",
            True,
            (255, 80, 80),
        )
    elif all_approved:
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
