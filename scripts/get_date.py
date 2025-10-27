import ntplib
import time
import os
from datetime import datetime

def consulta_ntp(server='200.160.0.8'):
    client = ntplib.NTPClient()
    resp = client.request(server, version=3)
    return resp.tx_time

if __name__ == "__main__":
    try:
        ts = consulta_ntp()
        dt = datetime.fromtimestamp(ts)
        formatted = time.strftime('%m%d%H%M%Y.%S', time.localtime(ts))
        print("Hora obtida via NTP:", formatted)
        os.system(f'sudo date {formatted} -03')
    except Exception as e:
        print("Erro ao consultar NTP:", e)
