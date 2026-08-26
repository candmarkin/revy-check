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
DEV_PASSWORD = ""  # preenchido por main.init_app_state a partir de src.config
DEV_HOTKEY = set()

LOG_DATA: List[Dict[str, Any]] = []
CONFIG: Dict[str, Any] = {}
SYSTEM_INFO: Dict[str, Any] = {}


def add_log(entry: Dict[str, Any]) -> None:
    if not any(e.get("step") == entry.get("step") for e in LOG_DATA):
        LOG_DATA.append(entry)


def now_iso() -> str:
    return str(datetime.now())
