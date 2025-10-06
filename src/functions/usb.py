import subprocess

# ---------------- USB ---------------- #
def port_has_device(bus, port_id):
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        for bus_string in output.split("/:"):
            for line in bus_string.splitlines():
                if port_id in line and "Class=Mass Storage" in line and bus in bus_string:
                    return True
    except Exception as e:
        print("Erro ao executar lsusb:", e)
    return False