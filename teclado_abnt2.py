import pygame
import sys

pygame.init()

# Config janela
WIDTH, HEIGHT = 1920, 1080
flags = pygame.FULLSCREEN
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), flags, display=0)
pygame.display.set_caption("Teste de Teclado ABNT2")
FONT = pygame.font.SysFont("Arial", 22)

# Cores
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)

# Define layout ABNT2
# Formato: (label, keycode, largura)
KEY_LAYOUT = [
    # Linha de funções
    [("Esc", pygame.K_ESCAPE, 58.5, 40), ("F1", pygame.K_F1, 58.5, 40), ("F2", pygame.K_F2, 58.5, 40), ("F3", pygame.K_F3, 58.5, 40),
     ("F4", pygame.K_F4, 58.5, 40), ("F5", pygame.K_F5, 58.5, 40), ("F6", pygame.K_F6, 58.5, 40), ("F7", pygame.K_F7, 58.5, 40),
     ("F8", pygame.K_F8, 58.5, 40), ("F9", pygame.K_F9, 58.5, 40), ("F10", pygame.K_F10, 58.5, 40), ("F11", pygame.K_F11, 58.5, 40),
     ("F12", pygame.K_F12, 58.5, 40), ("Insert", pygame.K_INSERT, 58.5, 40), ("Delete", pygame.K_DELETE, 58.5, 40)],
    
    # Números
    [("'", pygame.K_QUOTE, 60), ("1", pygame.K_1, 60), ("2", pygame.K_2, 60), ("3", pygame.K_3, 60),
     ("4", pygame.K_4, 60), ("5", pygame.K_5, 60), ("6", pygame.K_6, 60), ("7", pygame.K_7, 60),
     ("8", pygame.K_8, 60), ("9", pygame.K_9, 60), ("0", pygame.K_0, 60),
     ("-", pygame.K_MINUS, 60), ("=", pygame.K_EQUALS, 60), ("Backspace", pygame.K_BACKSPACE, 100)],

    # Linha QWERTY
    [("Tab", pygame.K_TAB, 100), ("Q", pygame.K_q, 60), ("W", pygame.K_w, 60), ("E", pygame.K_e, 60),
     ("R", pygame.K_r, 60), ("T", pygame.K_t, 60), ("Y", pygame.K_y, 60), ("U", pygame.K_u, 60),
     ("I", pygame.K_i, 60), ("O", pygame.K_o, 60), ("P", pygame.K_p, 60),
     ("´", 1073741824, 60), ("[", pygame.K_LEFTBRACKET, 60), ("Enter", pygame.K_RETURN, 60, 130)],

    # Linha ASDF
    [("Caps", pygame.K_CAPSLOCK, 110), ("A", pygame.K_a, 60), ("S", pygame.K_s, 60), ("D", pygame.K_d, 60),
     ("F", pygame.K_f, 60), ("G", pygame.K_g, 60), ("H", pygame.K_h, 60), ("J", pygame.K_j, 60),
     ("K", pygame.K_k, 60), ("L", pygame.K_l, 60), ("Ç", 231, 60),
     ("~", 1073741824, 60), ("]", pygame.K_RIGHTBRACKET, 60)],

    # Linha ZXCV
    [("Shift", pygame.K_LSHIFT, 80), (r"\\", pygame.K_BACKSLASH, 60), ("Z", pygame.K_z, 60), ("X", pygame.K_x, 60), ("C", pygame.K_c, 60),
     ("V", pygame.K_v, 60), ("B", pygame.K_b, 60), ("N", pygame.K_n, 60), ("M", pygame.K_m, 60),
     (",", pygame.K_COMMA, 60), (".", pygame.K_PERIOD, 60), (";", pygame.K_SEMICOLON, 60),
     ("Shift", pygame.K_RSHIFT, 145)],

    # Linha espaço
    [("Ctrl", pygame.K_LCTRL, 80), ("Fn", 1073741951, 60), ("Win", pygame.K_LSUPER, 60), ("Alt", pygame.K_LALT, 60),
     ("Espaço", pygame.K_SPACE, 320), ("AltGr", pygame.K_RALT, 60), ("/", pygame.K_SLASH, 60)],

     # Linha de navegação / setas
    [("←", pygame.K_LEFT, 60), 
    ("↑", pygame.K_UP, 80),
    ("↓", pygame.K_DOWN, 80), 
    ("→", pygame.K_RIGHT, 60)]

]   

pressed_keys = set()
already_pressed = set()


def draw_keyboard():
    SCREEN.fill(WHITE)
    y=20
    for row in KEY_LAYOUT:
        x = 20

        if KEY_LAYOUT.index(row) == len(KEY_LAYOUT) - 1: # LAYOUT DAS SETAS
            x += 735
            y-= 70

            # SETA ESQUERDA
            rect = pygame.Rect(x, y , row[0][2], h)
            if row[0][1] in pressed_keys:
                color = GREEN
            elif row[0][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(str(row[0][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            x+= 65

            # SETA CIMA
            rect = pygame.Rect(x, y , row[1][2], 28)
            if row[1][1] in pressed_keys:
                color = GREEN
            elif row[1][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(str(row[1][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            # SETA BAIXO
            rect = pygame.Rect(x, y + 32 , row[2][2], 28)
            if row[2][1] in pressed_keys:
                color = GREEN
            elif row[2][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(str(row[2][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)

            x += 85

             # SETA DIREITA
            rect = pygame.Rect(x, y, row[3][2], h)
            if row[3][1] in pressed_keys:
                color = GREEN
            elif row[3][1] in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(str(row[3][0]), True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)


            continue


        if KEY_LAYOUT.index(row) == 0:
            y += 10

        for key_def in row:

            if len(key_def) == 4:
                label, key, w, h = key_def
            else:
                label, key, w = key_def
                h = 60

            rect = pygame.Rect(x, y , w, h)

            if key in pressed_keys:
                color = GREEN
            elif key in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
                
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            pygame.draw.rect(SCREEN, BLACK, rect, 2, border_radius=5)
            text = FONT.render(label, True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)
            x += w + 5

        if KEY_LAYOUT.index(row) == 0:
            y += 50
            continue
        y += 70

    pygame.display.flip()



all_keys = {key for row in KEY_LAYOUT for *_, key, w in row}
print(all_keys)


button_rect = pygame.Rect(20, HEIGHT - 60, (WIDTH / 2) - 100, 40)

def draw_unlock_button():
    
    unlocked = all_keys.issubset(already_pressed)

    # Cor do botão
    color = (50,255,50) if unlocked else (200,200,200)
    bordercolor = (0,0,0) if unlocked else (100,100,100)

    pygame.draw.rect(SCREEN, color, button_rect, border_radius=5)
    pygame.draw.rect(SCREEN, bordercolor, button_rect, 2, border_radius=5)
    text = FONT.render("Enviar", True, bordercolor)
    text_rect = text.get_rect(center=button_rect.center)
    SCREEN.blit(text, text_rect)

    pygame.display.flip()

    return unlocked

def main():
    global pressed_keys
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                print(event.key)
                pressed_keys.add(event.key)
            if event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)
                    already_pressed.add(event.key)

        draw_keyboard()
        # unlocked = draw_unlock_button()

        # if unlocked:
        #     mouse_pos = pygame.mouse.get_pos()
        #     print(mouse_pos)

        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()



