# Exemplo de integração da câmera no alltests.py
# Adicione este código no seu arquivo alltests.py

# No início do arquivo, adicione o import:
from src.functions.camera import camera_test_step

# Defina a configuração SMB (coloque antes da função main()):
SMB_CONFIG = {
    'server': '192.168.1.100',      # IP do servidor SMB
    'share': 'fotos',                # Nome do compartilhamento
    'username': 'usuario',           # Usuário do SMB
    'password': 'senha',             # Senha do SMB
    'remote_path': 'cameras'         # Pasta dentro do compartilhamento
}

# Na função main(), adicione um novo estado para câmera:
# Exemplo de onde adicionar no fluxo de estados:

# ... (após os outros testes)

# ---------------- CAMERA ---------------- #
elif state == "CAMERA_STEP":
    add_log({"step":"CAMERA_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
    
    # Obter serial do dispositivo
    try:
        device_serial = subprocess.check_output(
            "cat /sys/class/dmi/id/product_serial", shell=True
        ).strip().decode("utf-8")
    except Exception:
        device_serial = "unknown"
    
    # Executar teste de câmera
    result = camera_test_step(SCREEN, FONT, device_serial, SMB_CONFIG)
    
    if result['success']:
        add_log({"step":"CAMERA_TEST","time":str(datetime.now()), "result":"APROVADO", "photo_path": result['photo_path']})
        draw_text(["✅ Foto capturada e enviada com sucesso!"], (0, 255, 0))
    else:
        add_log({"step":"CAMERA_TEST","time":str(datetime.now()), "result":"REPROVADO", "error": result['message']})
        draw_text([f"❌ Erro: {result['message']}"], (255, 0, 0))
    
    time.sleep(2)
    state = "DONE"  # ou próximo estado

# Para adicionar o estado CAMERA no fluxo, modifique a transição antes de "DONE":
# Por exemplo, após ETHERNET_STEP:

# elif state == "ETHERNET_STEP":
#     if HAS_ETHERNET_PORT:
#         add_log({"step":"ETHERNET_TEST_START","time":str(datetime.now()), "result":"APROVADO"})
#         ethernet_step()
#     state = "CAMERA_STEP"  # <-- Mudar de "DONE" para "CAMERA_STEP"
