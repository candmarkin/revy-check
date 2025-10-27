import pulsectl

pulse = pulsectl.Pulse('headphone-monitor')

def headphone_connected():

    print("Available sinks:")
    print(pulse.sink_list())

    for sink in pulse.sink_list():
        try:
            port_name = sink.port_active.name.lower()
            if 'headphone' in port_name or 'analog-output-headphones' in port_name:
                return True
        except Exception:
            continue
    return False

if __name__ == "__main__":
    if headphone_connected():
        print("Headphones are connected.")
    else:
        print("Headphones are not connected.")