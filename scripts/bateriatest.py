import threading
import time
import multiprocessing

def cpu_load(duration):
    # Function to simulate CPU load for a given duration
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = 10**5  # Perform a simple calculation to keep the CPU busy

def memory_load(size_mb, duration):
    # Function to allocate memory and hold it for a given duration
    memory = []
    for _ in range(size_mb):
        memory.append(bytearray(1024 * 1024))  # Allocate 1 MB at a time
    time.sleep(duration)
    del memory  # Free up memory after the duration

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    multiprocessing.freeze_support()
    print("Enter the type of load to simulate: ")
    print("1. CPU load")
    print("2. Memory load")
    choice = int(input("Your choice: "))

    if choice == 1:
        print(multiprocessing.cpu_count())
        cpu_cores = int(input("Enter the number of CPU cores to stress: "))
        duration = int(input("Enter the duration of the test (in seconds): "))
        processes = []
        for _ in range(cpu_cores):
            p = multiprocessing.Process(target=cpu_load, args=(duration,))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
    elif choice == 2:
        size_mb = int(input("Enter the size of memory to allocate (in MB): "))
        duration = int(input("Enter the duration of the test (in seconds): "))
        memory_thread = threading.Thread(target=memory_load, args=(size_mb, duration))
        memory_thread.start()
        memory_thread.join()
    else:
        print("Invalid choice!")