import pygame, os, time
from datetime import datetime
from functions.gui import draw_text
from ..main import log_data, CLOCK, MODE

def ethernet_connected(ETH_INTERFACE):

    carrier_file = f"/sys/class/net/{ETH_INTERFACE}/carrier"
    if os.path.isfile(carrier_file):
        with open(carrier_file, "r") as f:
            status = f.read().strip()
        return status == "1"
    return False

def ethernet_step(ETH_INTERFACE):

    waiting_remove = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT and MODE=="DEV":
                return
        if not waiting_remove:
            draw_text([f"Conecte o cabo Ethernet ({ETH_INTERFACE})..."])
            if ethernet_connected():
                waiting_remove = True
                time.sleep(0.5)
        else:
            draw_text([f"Remova o cabo Ethernet ({ETH_INTERFACE})..."])
            if not ethernet_connected():
                draw_text(["✅ Teste Ethernet concluído!"], (0, 255, 0))
                log_data.append({"step":"ETHERNET_TEST","time":str(datetime.now())})
                time.sleep(1)
                break
        CLOCK.tick(5)