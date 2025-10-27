import ntplib
import time
import os
from datetime import datetime, timezone, timedelta

# Fuso horário Brasil (UTC-3)
BR_TZ = timezone(timedelta(hours=-3))

def consulta_ntp(server='200.160.0.8'):
    client = ntplib.NTPClient()
    resp = client.request(server, version=3)
    return resp.tx_time

if __name__ == "__main__":
    try:
        ts = consulta_ntp()
        dt = datetime.fromtimestamp(ts, timezone.utc).astimezone(BR_TZ)
        formatted = dt.strftime('%m%d%H%M%Y.%S')
        print("Hora obtida via NTP (Brasil UTC-3):", dt.strftime('%Y-%m-%d %H:%M:%S'))
        os.system(f"sudo date {formatted}")
    except Exception as e:
        print("Erro ao consultar NTP:", e)
