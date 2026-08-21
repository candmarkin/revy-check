"""Roda so' o teste de teclado, em janela, sem banco e sem o fluxo completo.

Uso:
    python -m src.keyboardinit
    python src/keyboardinit.py

Imprime o log gerado no fim, para conferir o veredito sem subir o app inteiro.
"""

import json
import sys
from pathlib import Path

import pygame

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src import app_state
from src.functions.keyboard import keyboard_step


def init_state(width=1280, height=720):
    """Deixa app_state no mesmo estado que main.init_app_state deixaria.

    Os modulos de teste indexam app_state.COLORS e app_state.CONFIG direto; se
    faltar qualquer um deles o passo quebra no primeiro frame.
    """
    pygame.init()

    app_state.WIDTH = width
    app_state.HEIGHT = height
    app_state.SCREEN = pygame.display.set_mode((width, height))
    app_state.CLOCK = pygame.time.Clock()
    app_state.FONT = pygame.font.SysFont("Arial", 20)

    app_state.COLORS = {
        "WHITE": (240, 240, 240),
        "BLACK": (0, 0, 0),
        "GRAY": (180, 180, 180),
        "GREEN": (0, 200, 0),
    }
    app_state.SYSTEM_INFO = {}
    app_state.CONFIG = {}

    # Precisa ser nao-vazio: set().issubset(qualquer coisa) e' True, e o DEV
    # ligaria sozinho na primeira tecla.
    app_state.DEV_HOTKEY = {pygame.K_LCTRL, pygame.K_LSHIFT, pygame.K_d, pygame.K_v}


if __name__ == "__main__":
    init_state()
    try:
        keyboard_step()
    finally:
        pygame.quit()

    print(json.dumps(app_state.LOG_DATA, indent=2, ensure_ascii=False))
