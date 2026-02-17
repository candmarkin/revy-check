# Exemplo de integração do teste WiFi no alltests.py

# No início do arquivo, adicione o import:
from src.functions.wifi import wifi_test_step

# Na função main(), adicione o estado WiFI_STEP:
# Exemplo de onde adicionar no fluxo de estados:

# ... (após outros testes, antes de DONE)

# ---------------- WIFI ---------------- #
elif state == "WIFI_STEP":
    add_log({"step":"WIFI_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
    
    # Executar teste de WiFi
    result = wifi_test_step(SCREEN, FONT)
    
    if result['success']:
        add_log({
            "step":"WIFI_TEST",
            "time":str(datetime.now()), 
            "result":"APROVADO",
            "interface": result.get('interface'),
            "networks_found": result.get('networks_found'),
            "top_networks": [n.get('ssid') for n in result.get('networks', [])]
        })
        draw_text([
            "✅ WiFi detectado e funcionando!",
            f"Interface: {result.get('interface')}",
            f"Redes encontradas: {result.get('networks_found')}"
        ], (0, 255, 0))
    else:
        add_log({
            "step":"WIFI_TEST",
            "time":str(datetime.now()), 
            "result":"REPROVADO",
            "error": result.get('message')
        })
        draw_text([
            f"❌ {result.get('message')}",
            "Verifique se o dispositivo possui WiFi"
        ], (255, 0, 0))
    
    time.sleep(2)
    state = "CAMERA_STEP"  # ou próximo estado

# Para adicionar o teste WiFi no fluxo, modifique a transição:
# Por exemplo, após o teste de Ethernet:

# elif state == "ETHERNET_STEP":
#     if HAS_ETHERNET_PORT:
#         add_log({"step":"ETHERNET_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
#         ethernet_step()
#     state = "WIFI_STEP"  # <-- Adicionar aqui

# Ou você pode adicionar uma verificação condicional:
# Adicione no início do arquivo, após fetch_device_info():

# Verificar se tem WiFi
def has_wifi_hardware():
    """Verifica se o dispositivo possui hardware WiFi"""
    try:
        output = subprocess.check_output(["lshw", "-C", "network"], text=True, stderr=subprocess.DEVNULL)
        return "wireless" in output.lower() or "wi-fi" in output.lower()
    except:
        try:
            output = subprocess.check_output(["iw", "dev"], text=True, stderr=subprocess.DEVNULL)
            return "Interface" in output
        except:
            return False

HAS_WIFI = has_wifi_hardware()

# E no fluxo:
# elif state == "ETHERNET_STEP":
#     if HAS_ETHERNET_PORT:
#         ethernet_step()
#     if HAS_WIFI:
#         state = "WIFI_STEP"
#     else:
#         state = "CAMERA_STEP"  # pula para o próximo
