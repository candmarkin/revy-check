from main import SCREEN, FONT, VIDEO_PORTS
import pygame
import os


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

