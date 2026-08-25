"""Trava dos atalhos que tirariam o operador da tela cheia.

A implementação é do backend: `gsettings` no GNOME, hook `WH_KEYBOARD_LL` no
Windows.
"""

from src import hal


def disable_alt_tab():
    hal.lock_hotkeys()


def restore_alt_tab():
    hal.unlock_hotkeys()
