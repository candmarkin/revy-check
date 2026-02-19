import os
from datetime import datetime, timedelta, timezone

import ntplib

BR_TZ = timezone(timedelta(hours=-3))


def consulta_ntp(server="200.160.0.8"):
    try:
        client = ntplib.NTPClient()
        resp = client.request(server, version=3)
        ts = resp.tx_time
        dt_brasil = datetime.fromtimestamp(ts, timezone.utc).astimezone(BR_TZ)
        formatted = dt_brasil.strftime("%m%d%H%M%Y.%S")
        print("Hora obtida via NTP (Brasil UTC-3):", dt_brasil.strftime("%Y-%m-%d %H:%M:%S"))
        os.system(f"sudo date {formatted}")
        return ts
    except Exception as e:
        print("Erro ao consultar NTP:", e)
        return None
