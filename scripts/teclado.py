#!/usr/bin/env python3
import pygame
import sys

# Inicializa o Pygame sem mostrar janela
pygame.display.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)
pygame.key.set_repeat(1, 50)

print("Pressione qualquer tecla (Ctrl+C para sair):")

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                print(f"Tecla pressionada: {pygame.key.name(event.key)} (código: {event.key})")
            elif event.type == pygame.KEYUP:
                print(f"Tecla liberada: {pygame.key.name(event.key)} (código: {event.key})")
except KeyboardInterrupt:
    print("\nEncerrando...")
    pygame.quit()
    sys.exit(0)
