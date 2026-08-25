from src import hal


def port_has_device(bus, port_id):
    """True se a porta cadastrada estiver com um pendrive conectado.

    A identificacao da porta fisica muda de forma entre os SOs -- sysfs no
    Linux, location path no Windows -- entao quem sabe ler o cadastro e' o
    backend de `src.hal`.
    """
    return hal.port_has_device(bus, port_id)
