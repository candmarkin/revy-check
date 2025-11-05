#!/usr/bin/env python3
import time, sys, os, psutil

def cpu_load(duration: int):
    """Carga total da CPU por X segundos"""
    end = time.time() + duration
    while time.time() < end:
        _ = 10 ** 5  # operação simples, mas constante

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: worker_cpu.py <duracao_segundos>")
        sys.exit(1)

    duration = int(sys.argv[1])
    cpu_load(duration)
