"""
Funções de banco de dados
"""
import mysql.connector
import time


def wait_for_db_connection(max_retries=5, retry_delay=3):
    """
    Aguarda conexão com banco de dados
    
    Returns:
        mysql.connector.connection: Conexão ou None
    """
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host="revy.selbetti.com.br",
                user="drack",
                password="dR@ck#2024!",
                database="revycheck"
            )
            print(f"✅ Conectado ao banco de dados (tentativa {attempt + 1})")
            return conn
        except mysql.connector.Error as e:
            print(f"❌ Erro ao conectar (tentativa {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Aguardando {retry_delay}s antes de tentar novamente...")
                time.sleep(retry_delay)
    
    print("❌ Não foi possível conectar ao banco de dados após todas as tentativas")
    return None


def fetch_device_info(serial):
    """
    Busca informações do dispositivo no banco de dados
    
    Args:
        serial: Número de série do dispositivo
    
    Returns:
        dict: Informações do dispositivo ou None
    """
    conn = wait_for_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                manufacturer, 
                has_headphone,
                has_speaker,
                has_mic,
                usb_left,
                usb_right,
                has_hdmi,
                has_displayport,
                has_ethernet,
                has_wifi,
                has_touchpad,
                has_camera
            FROM devices 
            WHERE serial = %s
        """
        cursor.execute(query, (serial,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Dispositivo encontrado: {result.get('manufacturer', 'Unknown')}")
            return result
        else:
            print(f"❌ Dispositivo com serial '{serial}' não encontrado")
            return None
            
    except mysql.connector.Error as e:
        print(f"❌ Erro ao buscar informações do dispositivo: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def send_to_db(serial, screen_ok, keyboard_ok, usb_ok, video_ok, 
               headphone_ok, speaker_ok, mic_ok, ethernet_ok,
               wifi_ok, touchpad_ok, camera_ok, approval):
    """
    Envia resultados dos testes para o banco de dados
    
    Args:
        serial: Número de série
        screen_ok: Teste de tela OK
        keyboard_ok: Teste de teclado OK
        usb_ok: Teste de USB OK
        video_ok: Teste de vídeo OK
        headphone_ok: Teste de fone OK
        speaker_ok: Teste de alto-falante OK
        mic_ok: Teste de microfone OK
        ethernet_ok: Teste de Ethernet OK
        wifi_ok: Teste de WiFi OK
        touchpad_ok: Teste de touchpad OK
        camera_ok: Teste de câmera OK
        approval: Aprovação geral
    
    Returns:
        bool: True se sucesso
    """
    conn = wait_for_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO test_results 
            (serial, screen_ok, keyboard_ok, usb_ok, video_ok, 
             headphone_ok, speaker_ok, mic_ok, ethernet_ok,
             wifi_ok, touchpad_ok, camera_ok, approval, test_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        values = (
            serial, screen_ok, keyboard_ok, usb_ok, video_ok,
            headphone_ok, speaker_ok, mic_ok, ethernet_ok,
            wifi_ok, touchpad_ok, camera_ok, approval
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        print(f"✅ Resultados salvos no banco de dados para serial {serial}")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Erro ao salvar no banco de dados: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
