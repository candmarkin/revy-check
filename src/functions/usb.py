import subprocess

from src.functions.hw_paths import is_physical_port_id, mass_storage_port_ids


def port_has_device(bus, port_id):
    """True se a porta cadastrada estiver com um pendrive conectado.

    Aceita os dois formatos de cadastro: o novo, por caminho fisico no sysfs
    (bus='0000:00:14.0', port_id='3.2'), e o legado, que gravava o texto do
    `lsusb -t` (bus='Bus 002', port_id='Port 003:'). O formato legado quebra
    entre variantes Intel/AMD do mesmo modelo porque a numeracao de bus muda
    com o chipset, mas continua sendo lido para nao invalidar cadastros antigos.
    """
    if is_physical_port_id(bus):
        return f"{bus}/{port_id}" in mass_storage_port_ids()
    return _legacy_port_has_device(bus, port_id)


def _legacy_port_has_device(bus, port_id):
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        for bus_string in output.split("/:"):
            for line in bus_string.splitlines():
                if port_id in line and "Class=Mass Storage" in line and bus in bus_string:
                    return True
    except Exception as e:
        print("Erro ao executar lsusb:", e)
    return False
