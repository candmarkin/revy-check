# pygame que mostra o codigo das teclas pressionadas
import pygame

def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Teclado Keycode Viewer")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                print(f"Tecla pressionada: {event.key} (Keycode: {pygame.key.name(event.key)})")

    pygame.quit()

if __name__ == "__main__":
    main()