"""Shared application state configured by main."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

SCREEN = None
WIDTH = 0
HEIGHT = 0
FONT = None
CLOCK = None
MODE = "PROD"
DEV_PASSWORD = "dev123"
DEV_HOTKEY = set()

LOG_DATA: List[Dict[str, Any]] = []
CONFIG: Dict[str, Any] = {}
SYSTEM_INFO: Dict[str, Any] = {}

GAT_QUALITY = None          # qualidade lida de gat.dbo.ESAL (SQL Server)
GAT_ALLOWS_REPROVE = False  # True so' em D/Dp/Drp; o padrao trava
REPROVED_STEP = None        # primeiro step REPROVADO quando a qualidade trava


def add_log(entry: Dict[str, Any]) -> None:
    global REPROVED_STEP

    if any(e.get("step") == entry.get("step") for e in LOG_DATA):
        return
    LOG_DATA.append(entry)

    # Gate central: todo veredicto de todo teste passa por aqui, entao um unico
    # ponto cobre tela, teclado, touchpad, wifi, camera, video e audio.
    if (
        REPROVED_STEP is None
        and entry.get("result") == "REPROVADO"
        and not GAT_ALLOWS_REPROVE
    ):
        REPROVED_STEP = entry.get("step")


def now_iso() -> str:
    return str(datetime.now())
