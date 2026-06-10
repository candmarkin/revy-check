#!/usr/bin/env python3
"""
Captura c�digos de teclado usando pygame.
Pressione as teclas desejadas; pressione ESC para finalizar.
Salva um arquivo JSON `keycodes.json` com os c�digos capturados.
"""

import pygame
import json
import os
import time
from pathlib import Path


def main():
    pygame.init()
    screen = pygame.display.set_mode((680, 220))
    pygame.display.set_caption("Coletor de c�digos de teclado")
    try:
        font = pygame.font.SysFont(None, 22)
    except Exception:
        font = pygame.font.Font(None, 22)

    clock = pygame.time.Clock()
    keymap = {}
    instructions = [
        "Pressione todas as teclas que quiser (ESC para sair).",
        "Cada tecla � gravada (pygame key, scancode, name, unicode)."
    ]

    running = True
    last = "(nenhuma tecla ainda)"

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                key = int(event.key)
                scancode = getattr(event, 'scancode', None)
                name = pygame.key.name(key)
                uni = getattr(event, 'unicode', '')

                if str(key) not in keymap:
                    keymap[str(key)] = {
                        "pygame_key": key,
                        "scancode": scancode,
                        "name": name,
                        "unicode": uni,
                        "time": time.time(),
                    }

                last = f"{name}  pygame_key={key}  scancode={scancode}  unicode={repr(uni)}"

        screen.fill((18, 18, 18))
        y = 10
        for line in instructions:
            surf = font.render(line, True, (235, 235, 235))
            screen.blit(surf, (10, y))
            y += 26

        surf = font.render(f"�ltima: {last}", True, (250, 200, 60))
        screen.blit(surf, (10, y)); y += 26

        surf = font.render(f"Total capturados: {len(keymap)}", True, (200, 200, 200))
        screen.blit(surf, (10, y))

        pygame.display.flip()
        clock.tick(60)

    out = Path(os.getcwd()) / "keycodes.json"
    try:
        with out.open('w', encoding='utf-8') as f:
            json.dump(keymap, f, ensure_ascii=False, indent=2)
        print(f"Keycodes salvos em: {out}")
    except Exception as e:
        print("Erro ao salvar arquivo:", e)

    pygame.quit()


if __name__ == '__main__':
    main()
