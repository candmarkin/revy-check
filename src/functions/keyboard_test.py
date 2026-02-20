"""
Funções de teste de teclado
"""
import pygame
import time
from datetime import datetime


# Layout do teclado
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
    ("→", pygame.K_RIGHT, 60),
    ("Pg Up", pygame.K_PAGEUP, 60),
    ("Pg Down", pygame.K_PAGEDOWN, 60),
    ]
]


# Cores
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)


def get_all_keys():
    """Retorna lista de todas as teclas"""
    all_keys = []
    for row in KEY_LAYOUT:
        for key in row:
            all_keys.append(key[1])
    return all_keys


def draw_keyboard(screen, width, height, pressed_keys, already_pressed, font):
    """Desenha o teclado na tela"""
    screen.fill(WHITE)
    y = 80
    
    for row_idx, row in enumerate(KEY_LAYOUT):
        # Calcular largura total da linha para centralizar
        total_width = 0
        for key_def in row:
            if len(key_def) == 4:
                _, _, w, _ = key_def
            else:
                _, _, w = key_def
            total_width += w + 5
        total_width -= 5
        x = (width - total_width) // 2

        if row_idx == len(KEY_LAYOUT) - 1:  # LAYOUT DAS SETAS
            x += 735 - ((width - total_width) // 2)
            
            # Desenhar setas e page up/down
            _draw_arrow_keys(screen, x, y, row, pressed_keys, already_pressed)
            continue

        for key_def in row:
            if len(key_def) == 4:
                label, key, w, h = key_def
            else:
                label, key, w = key_def
                h = 60

            rect = pygame.Rect(x, y, w, h)

            if key in pressed_keys:
                color = GREEN
            elif key in already_pressed:
                color = (100, 255, 100)
            else:
                color = WHITE
                
            pygame.draw.rect(screen, color, rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
            text = font.render(label, True, BLACK)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
            x += w + 5

        if KEY_LAYOUT.index(row) == 0:
            y += 50
            continue
        y += 70


def _draw_arrow_keys(screen, x, y, row, pressed_keys, already_pressed):
    """Desenha as teclas de seta e page up/down"""
    # PAGEUP
    rect = pygame.Rect(x, y, row[4][2], 28)
    color = GREEN if row[4][1] in pressed_keys else (100, 255, 100) if row[4][1] in already_pressed else WHITE
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
    text = pygame.font.SysFont("Arial", 15).render(str(row[4][0]), True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))

    # SETA ESQUERDA
    rect = pygame.Rect(x, y + 32, row[0][2], 28)
    color = GREEN if row[0][1] in pressed_keys else (100, 255, 100) if row[0][1] in already_pressed else WHITE
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
    text = pygame.font.SysFont("Arial", 15).render(str(row[0][0]), True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))

    x += 65

    # SETA CIMA
    rect = pygame.Rect(x, y, row[1][2], 28)
    color = GREEN if row[1][1] in pressed_keys else (100, 255, 100) if row[1][1] in already_pressed else WHITE
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
    text = pygame.font.SysFont("Arial", 15).render(str(row[1][0]), True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))

    # SETA BAIXO
    rect = pygame.Rect(x, y + 32, row[2][2], 28)
    color = GREEN if row[2][1] in pressed_keys else (100, 255, 100) if row[2][1] in already_pressed else WHITE
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
    text = pygame.font.SysFont("Arial", 15).render(str(row[2][0]), True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))

    x += 85

    # SETA DIREITA
    rect = pygame.Rect(x, y + 32, row[3][2], 28)
    color = GREEN if row[3][1] in pressed_keys else (100, 255, 100) if row[3][1] in already_pressed else WHITE
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
    text = pygame.font.SysFont("Arial", 15).render(str(row[3][0]), True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))

    # PAGEDOWN
    rect = pygame.Rect(x, y, row[5][2], 28)
    color = GREEN if row[5][1] in pressed_keys else (100, 255, 100) if row[5][1] in already_pressed else WHITE
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
    text = pygame.font.SysFont("Arial", 15).render(str(row[5][0]), True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))


def draw_kb_unlock_button(screen, height, font, already_pressed, all_keys):
    """Desenha o botão de aprovação do teclado"""
    kb_button_rect = pygame.Rect(20, height - 60, 200, 50)
    unlocked = set(all_keys).issubset(set(already_pressed))
    color = (50, 255, 50) if unlocked else (200, 200, 200)
    bordercolor = (0, 0, 0) if unlocked else (100, 100, 100)
    pygame.draw.rect(screen, color, kb_button_rect, border_radius=5)
    pygame.draw.rect(screen, bordercolor, kb_button_rect, 2, border_radius=5)
    text = font.render("Aprovar", True, bordercolor)
    screen.blit(text, text.get_rect(center=kb_button_rect.center))
    return unlocked


def keyboard_step(screen, width, height, font, clock, manufacturer, mode_dict, draw_text_func, add_log_func, draw_system_info_func, get_system_info_func, dev_hotkey, save_log_func):
    """
    Executa o teste de teclado
    
    Returns:
        bool: True se aprovado
    """
    pressed_keys = set()
    already_pressed = []
    all_keys = get_all_keys()
    running = True
    last_key_info = ""
    system_info = get_system_info_func()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if mode_dict["MODE"] == "DEV":
                    save_log_func()
                    pygame.quit()
                    import sys
                    sys.exit()

            elif event.type == pygame.KEYDOWN:
                if manufacturer == "LENOVO":
                    if event.key == 1073742052:  # Tecla / do lenovo
                        pressed_keys.add(pygame.K_SLASH)
                        already_pressed.append(pygame.K_SLASH)
                
                pressed_keys.add(event.key)
                already_pressed.append(event.key)
                key_name = pygame.key.name(event.key)
                last_key_info = f"Tecla: {key_name} | Código: {event.key}"
                print(last_key_info)
                
                # Hotkey secreta para DEV
                if dev_hotkey.issubset(pressed_keys) and mode_dict["MODE"] == "PROD":
                    print("DEV MODE UNLOCKED via hotkey!")
                    mode_dict["MODE"] = "DEV"

            elif event.type == pygame.KEYUP:
                if event.key in pressed_keys:
                    pressed_keys.remove(event.key)

        screen.fill((240, 240, 240))
        draw_keyboard(screen, width, height, pressed_keys, already_pressed, font)
        unlocked = draw_kb_unlock_button(screen, height, font, already_pressed, all_keys)
        
        # Desenhar informações do sistema
        draw_system_info_func(system_info)

        # Mostrar tecla pressionada no modo DEV
        if mode_dict["MODE"] == "DEV" and last_key_info:
            dev_font = pygame.font.SysFont("Consolas", 22)
            text_surf = dev_font.render(last_key_info, True, (0, 100, 255))
            screen.blit(text_surf, (20, 20))

        pygame.display.flip()
        clock.tick(60)

        if unlocked:
            draw_text_func(["✅ Teste de teclado concluído!"], (0, 255, 0))
            add_log_func({"step": "KEYBOARD_TEST", "time": str(datetime.now()), "result": "APROVADO"})
            time.sleep(1)
            running = False
    
    return True
