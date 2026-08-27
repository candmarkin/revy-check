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
# `--dev` na linha de comando: pedido de DEV, resolvido depois do login por
# functions.dev_mode. Flag sozinho nao libera nada.
DEV_REQUESTED = False
DEV_HOTKEY = set()

# Técnico logado ({id, name, role, key}) ou None. Quem preenche é
# functions.login; a chave existe só aqui, em memória, nunca em disco.
USER: Dict[str, Any] | None = None

LOG_DATA: List[Dict[str, Any]] = []
CONFIG: Dict[str, Any] = {}
SYSTEM_INFO: Dict[str, Any] = {}


def add_log(entry: Dict[str, Any]) -> None:
    if not any(e.get("step") == entry.get("step") for e in LOG_DATA):
        LOG_DATA.append(entry)


def now_iso() -> str:
    return str(datetime.now())
