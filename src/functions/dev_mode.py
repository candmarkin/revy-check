"""Atalhos de DEV: escolher em que passo comecar e aprovar passos na mao.

Em PROD nada disto existe -- todas as funcoes checam `app_state.MODE` e saem
sem fazer nada. O alvo e' a bancada de desenvolvimento: sem isto, mexer na
etapa de ethernet exige passar por tela, teclado, touchpad, wifi, camera, USB,
video e audio antes, toda vez.

O controle de fluxo usa excecao porque os passos tem loop de evento proprio e
bloqueiam em profundidade (`ask_operator` dentro de `play_speaker_sequence`
dentro do passo). Devolver um valor especial exigiria propagar a checagem por
toda a pilha; a excecao desenrola sozinha ate' o `main`.
"""

from datetime import datetime

import pygame

from src import app_state

# Ordem do fluxo em `main.py`. Cada entrada e' (estado, rotulo no menu).
STEPS = [
    ("SCREEN_STEP", "Tela"),
    ("KEYBOARD_STEP", "Teclado"),
    ("TOUCHPAD_STEP", "Touchpad"),
    ("WIFI_STEP", "WiFi"),
    ("CAMERA_STEP", "Camera"),
    ("USB_STEP", "USB"),
    ("VIDEO_STEP", "Video"),
    ("HEADPHONE_STEP", "Headphone"),
    ("SPEAKER_STEP", "Alto-falante"),
    ("MIC_STEP", "Microfone"),
    ("ETHERNET_STEP", "Ethernet"),
    ("DONE", "Finalizar e salvar log"),
]

# Para onde ir ao aprovar um passo na mao. Os sub-estados do headphone caem
# todos no proximo passo de verdade: aprovar "headphone" nao pode largar o
# fluxo no meio da propria sequencia de headphone.
NEXT_ON_SKIP = {
    "SCREEN_STEP": "KEYBOARD_STEP",
    "KEYBOARD_STEP": "TOUCHPAD_STEP",
    "TOUCHPAD_STEP": "WIFI_STEP",
    "WIFI_STEP": "CAMERA_STEP",
    "CAMERA_STEP": "USB_STEP",
    "USB_STEP": "VIDEO_STEP",
    "VIDEO_STEP": "HEADPHONE_STEP",
    "HEADPHONE_STEP": "SPEAKER_STEP",
    "HEADPHONE_TESTING": "SPEAKER_STEP",
    "HEADPHONE_REMOVE": "SPEAKER_STEP",
    "SPEAKER_STEP": "MIC_STEP",
    "MIC_STEP": "ETHERNET_STEP",
    "ETHERNET_STEP": "DONE",
}

APPROVE_KEY = pygame.K_a
JUMP_KEY = pygame.K_j

LEGEND = "DEV: Ctrl+Shift+A aprova o passo | Ctrl+Shift+J salta de passo"

# Quem pode destravar o DEV. Vem do `role` que a API devolve no login, nao de
# senha em arquivo: senha compartilhada em bancada vira folclore, e o DEV
# permite aprovar teste na mao -- ou seja, aprovar equipamento sem testar.
# Revogar agora e' mudar o papel do usuario no cadastro, sem tocar em bancada.
ROLES_DEV = ("admin",)

_AVISO_MS = 4000
_aviso = None  # (texto, cor, expira_em_ticks)


class DevSkip(Exception):
    """Passo aprovado na mao; o fluxo segue para o proximo."""


class DevJump(Exception):
    """Salto para um estado escolhido no menu."""

    def __init__(self, state):
        super().__init__(state)
        self.state = state


def active():
    return app_state.MODE == "DEV"


def pode_destravar(usuario=None):
    """O papel do usuario logado autoriza o DEV?"""
    usuario = usuario if usuario is not None else (app_state.USER or {})
    return usuario.get("role") in ROLES_DEV


def destravar():
    """Liga o DEV para quem esta' logado, se o papel permitir.

    Antes disto era senha compartilhada no `revycheck.env` -- e o teste de
    teclado nem pedia senha, so' ligava o DEV na hotkey. Agora a decisao e' uma
    so', aqui, com base no `role` que veio do login, e cada liberacao entra no
    log do checklist com nome e papel.
    """
    global _aviso
    if app_state.MODE == "DEV":
        return True

    usuario = app_state.USER or {}
    nome = usuario.get("name") or "sem login"
    papel = usuario.get("role") or "sem papel"

    if not pode_destravar(usuario):
        _aviso = (f"DEV negado: {nome} ({papel})", (255, 120, 120),
                  pygame.time.get_ticks() + _AVISO_MS)
        print(f"DEV negado para {nome} ({papel}); precisa de {'/'.join(ROLES_DEV)}")
        return False

    app_state.MODE = "DEV"
    app_state.add_log({
        "step": "DEV_MODE",
        "time": app_state.now_iso(),
        "result": "APROVADO",
        "detalhe": f"destravado por {nome} ({papel})",
    })
    _aviso = (f"DEV liberado: {nome}", (120, 255, 160),
              pygame.time.get_ticks() + _AVISO_MS)
    print(f"DEV MODE UNLOCKED por {nome} ({papel})")
    return True


def aplicar_pedido_de_cli():
    """Resolve o `--dev` da linha de comando, depois do login.

    O flag e' pedido, nao permissao: numa bancada, um atalho com `--dev` daria
    DEV a qualquer um que clicasse nele.
    """
    if not app_state.DEV_REQUESTED:
        return False
    return destravar()


def draw_aviso():
    """Faixa curta com o resultado da ultima tentativa de destravar.

    Existe porque o `.exe` e' `console=False`: sem isto, negar o DEV nao dava
    sinal nenhum na tela e parecia que a hotkey nao funcionou.
    """
    global _aviso
    if not _aviso or app_state.SCREEN is None:
        return
    texto, cor, expira = _aviso
    if pygame.time.get_ticks() > expira:
        _aviso = None
        return
    fonte = pygame.font.SysFont("Consolas", 18, bold=True)
    render = fonte.render(texto, True, cor)
    app_state.SCREEN.blit(render, render.get_rect(center=(app_state.WIDTH // 2, 30)))


def _is_combo(event, key):
    """Ctrl+Shift+<key>, com qualquer um dos dois Ctrl/Shift."""
    if event.type != pygame.KEYDOWN or event.key != key:
        return False
    mods = pygame.key.get_mods()
    return bool(mods & pygame.KMOD_CTRL) and bool(mods & pygame.KMOD_SHIFT)


def handle(event):
    """Processa os atalhos de DEV. Chamar dentro de todo loop de evento.

    Levanta `DevSkip` ou `DevJump`, que o `main` captura. Em PROD nao faz nada,
    entao pode ser chamada sem condicional em qualquer passo.
    """
    if not active():
        return

    if _is_combo(event, APPROVE_KEY):
        raise DevSkip()

    if _is_combo(event, JUMP_KEY):
        target = pick_step("Saltar para qual passo?")
        if target:
            raise DevJump(target)


def approve(state):
    """Registra a aprovacao manual e devolve o proximo estado.

    O log guarda o passo com prefixo `DEV_APROVADO_`: uma execucao aprovada na
    mao nao pode ficar indistinguivel de uma que passou de verdade.
    """
    app_state.add_log({
        "step": f"DEV_APROVADO_{state}",
        "time": str(datetime.now()),
        "result": "APROVADO",
    })
    print(f"DEV: passo {state} aprovado manualmente")
    return NEXT_ON_SKIP.get(state, "DONE")


def draw_legend():
    """Faixa com os atalhos, no rodape. So' aparece em DEV."""
    if not active() or app_state.SCREEN is None:
        return
    font = pygame.font.SysFont("Arial", 14)
    surface = font.render(LEGEND, True, (255, 200, 0))
    rect = surface.get_rect()
    rect.bottomleft = (20, app_state.HEIGHT - 10)
    app_state.SCREEN.blit(surface, rect)


def pick_step(title="Comecar em qual passo?"):
    """Menu de passos. Devolve o estado escolhido, ou None se cancelado.

    Tem loop de evento proprio e nao chama `handle`: abrir o menu de dentro do
    proprio menu nao faria sentido, e ESC ja' cancela.
    """
    if not active():
        return None

    font_title = pygame.font.SysFont("Arial", 26, bold=True)
    font_item = pygame.font.SysFont("Arial", 20)
    font_hint = pygame.font.SysFont("Arial", 16)
    clock = app_state.CLOCK or pygame.time.Clock()

    # Duas colunas: a lista inteira nao cabe em altura util numa tela de
    # bancada de 768 linhas.
    per_column = (len(STEPS) + 1) // 2
    button_height = 46
    button_width = 360
    top = 150

    typed = ""
    buttons = []
    for index, (state, label) in enumerate(STEPS):
        column, row = divmod(index, per_column)
        x = app_state.WIDTH // 2 - button_width - 20 + column * (button_width + 40)
        rect = pygame.Rect(x, top + row * (button_height + 10), button_width, button_height)
        buttons.append((state, f"{index + 1}. {label}", rect))

    while True:
        app_state.SCREEN.fill((20, 20, 35))

        heading = font_title.render(title, True, (255, 255, 255))
        app_state.SCREEN.blit(
            heading, (app_state.WIDTH // 2 - heading.get_width() // 2, 70)
        )

        mouse = pygame.mouse.get_pos()
        for _, label, rect in buttons:
            hovered = rect.collidepoint(mouse)
            pygame.draw.rect(
                app_state.SCREEN,
                (0, 150, 220) if hovered else (45, 45, 70),
                rect,
                border_radius=8,
            )
            text = font_item.render(label, True, (255, 255, 255))
            app_state.SCREEN.blit(
                text, (rect.x + 16, rect.centery - text.get_height() // 2)
            )

        if typed:
            echo = font_item.render(f"> {typed}", True, (255, 220, 0))
            app_state.SCREEN.blit(
                echo,
                (app_state.WIDTH // 2 - echo.get_width() // 2, app_state.HEIGHT - 110),
            )

        hint = font_hint.render(
            "Clique, ou digite o numero e ENTER.   ESC = seguir o fluxo normal",
            True,
            (200, 200, 200),
        )
        app_state.SCREEN.blit(
            hint, (app_state.WIDTH // 2 - hint.get_width() // 2, app_state.HEIGHT - 70)
        )
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for state, _, rect in buttons:
                    if rect.collidepoint(event.pos):
                        return state
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_BACKSPACE:
                    typed = typed[:-1]
                elif event.unicode.isdigit():
                    # Numero digitado, e nao salto direto na tecla: senao os
                    # passos de 10 em diante ficariam inalcancaveis pelo teclado.
                    typed = (typed + event.unicode)[:2]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    index = int(typed) - 1 if typed else -1
                    if 0 <= index < len(STEPS):
                        return STEPS[index][0]
                    typed = ""

        clock.tick(30)
