import time
from datetime import datetime

import pygame

from src import app_state, hal
from src.functions.gui import draw_text
from src.functions import dev_mode


def ethernet_connected(eth_interface):
    return hal.ethernet_connected(eth_interface)


def ethernet_step(eth_interface):
    waiting_remove = False
    while True:
        for event in pygame.event.get():
            dev_mode.handle(event)
            if event.type == pygame.QUIT and app_state.MODE == "DEV":
                return
        if not waiting_remove:
            draw_text([f"Conecte o cabo Ethernet ({eth_interface})..."])
            if ethernet_connected(eth_interface):
                waiting_remove = True
                time.sleep(0.5)
        else:
            draw_text([f"Remova o cabo Ethernet ({eth_interface})..."])
            if not ethernet_connected(eth_interface):
                draw_text([f"Conecte o cabo Ethernet ({eth_interface})..."])
                if ethernet_connected(eth_interface):
                    waiting_remove = True
                    time.sleep(0.5)
                    draw_text(["✅ Teste Ethernet concluído!"], (0, 255, 0))
                    app_state.add_log({"step": "ETHERNET_TEST", "time": str(datetime.now()), "result": "APROVADO"})
                    time.sleep(1)
                    break
        app_state.CLOCK.tick(5)
