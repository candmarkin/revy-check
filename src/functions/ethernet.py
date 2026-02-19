import os
import time
from datetime import datetime

import pygame

from src import app_state
from src.functions.gui import draw_text


def ethernet_connected(eth_interface):
    carrier_file = f"/sys/class/net/{eth_interface}/carrier"
    if os.path.isfile(carrier_file):
        with open(carrier_file, "r") as f:
            status = f.read().strip()
        return status == "1"
    return False


def ethernet_step(eth_interface):
    waiting_remove = False
    while True:
        for event in pygame.event.get():
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
