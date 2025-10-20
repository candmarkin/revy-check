import time


def cpu_worker(stop_event):
    """Simple CPU-bound worker that runs until stop_event is set.
    Keep this module minimal so importing it in child processes doesn't run GUI code.
    """
    rng = range
    while not stop_event.is_set():
        # tight CPU-bound loop
        _ = sum(i * i for i in rng(30000))
        # small sleep can reduce wasteful busyspin if desired
        # time.sleep(0)
