from datetime import datetime, timedelta, timezone

import ntplib

from src import hal

BR_TZ = timezone(timedelta(hours=-3))


def consulta_ntp(server="200.160.0.8"):
    try:
        client = ntplib.NTPClient()
        resp = client.request(server, version=3)
        ts = resp.tx_time
        dt_brasil = datetime.fromtimestamp(ts, timezone.utc).astimezone(BR_TZ)
        print("Hora obtida via NTP (Brasil UTC-3):", dt_brasil.strftime("%Y-%m-%d %H:%M:%S"))
        if not hal.set_system_time(dt_brasil):
            print("Aviso: nao foi possivel ajustar o relogio do sistema.")
        return ts
    except Exception as e:
        print("Erro ao consultar NTP:", e)
        return None
