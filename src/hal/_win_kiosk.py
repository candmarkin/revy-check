"""Trava de atalhos do Windows, equivalente ao `gsettings` do backend GNOME.

Um hook `WH_KEYBOARD_LL` engole Win, Alt+Tab, Alt+Esc, Ctrl+Esc e Alt+F4 antes
que o shell os veja. O hook roda numa thread propria com bomba de mensagens: LL
hooks sao entregues na thread que os instalou, e a thread precisa estar
processando mensagens -- pendurar isso no loop do pygame deixaria o hook mudo
sempre que um passo bloqueasse esperando hardware.

Ctrl+Alt+Del continua funcionando: o SO nao permite intercepta-lo, por design.
Para fechar a maquina de verdade (substituir o shell) o caminho e' o Shell
Launcher do Windows Enterprise/IoT, fora do escopo do app.
"""

import ctypes
import threading
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_QUIT = 0x0012

VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_F4 = 0x73
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_CONTROL = 0x11

LLKHF_ALTDOWN = 0x20


class _KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


_HOOKPROC = ctypes.WINFUNCTYPE(
    wintypes.LPARAM, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int, _HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD
]
user32.CallNextHookEx.restype = wintypes.LPARAM
user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
]

_state = {"thread": None, "thread_id": None, "hook": None}


def _ctrl_down():
    return bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)


def _should_block(key, message):
    alt_down = bool(key.flags & LLKHF_ALTDOWN)

    if key.vkCode in (VK_LWIN, VK_RWIN):
        return True
    if key.vkCode == VK_TAB and alt_down:
        return True
    if key.vkCode == VK_ESCAPE and (alt_down or _ctrl_down()):
        return True
    if key.vkCode == VK_F4 and alt_down:
        return True
    return False


@_HOOKPROC
def _hook_proc(code, wparam, lparam):
    if code == HC_ACTION and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
        key = ctypes.cast(lparam, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents
        if _should_block(key, wparam):
            return 1  # engole a tecla: nao chega em ninguem
    return user32.CallNextHookEx(None, code, wparam, lparam)


def _pump():
    _state["thread_id"] = kernel32.GetCurrentThreadId()
    _state["hook"] = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _hook_proc, None, 0)
    if not _state["hook"]:
        print("Aviso: nao foi possivel instalar o hook de teclado",
              ctypes.get_last_error())
        return

    message = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(message))
        user32.DispatchMessageW(ctypes.byref(message))

    user32.UnhookWindowsHookEx(_state["hook"])
    _state["hook"] = None


def lock_hotkeys():
    if _state["thread"] and _state["thread"].is_alive():
        return
    thread = threading.Thread(target=_pump, name="revy-kiosk-hook", daemon=True)
    _state["thread"] = thread
    thread.start()


def unlock_hotkeys():
    thread_id = _state["thread_id"]
    if thread_id:
        user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)
    thread = _state["thread"]
    if thread:
        thread.join(timeout=2)
    _state.update({"thread": None, "thread_id": None})
