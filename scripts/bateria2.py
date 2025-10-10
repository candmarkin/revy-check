#!/usr/bin/env python3
import subprocess, time, re, os, sys
from datetime import datetime

# -------------------------------
# Funções utilitárias
# -------------------------------

def run(cmd, capture=True):
    try:
        if capture:
            return subprocess.check_output(cmd, shell=True, text=True)
        else:
            subprocess.run(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        return e.output if capture else None

def get_battery_info():
    output = run("upower -i $(upower -e | grep BAT)")
    energy_now = re.search(r"energy:\s+([\d\.]+)", output)
    energy_full = re.search(r"energy-full:\s+([\d\.]+)", output)
    rate = re.search(r"energy-rate:\s+([\d\.]+)", output)

    if energy_now and rate and energy_full:
        return {
            "energy_now": float(energy_now.group(1)),
            "energy_full": float(energy_full.group(1)),
            "rate": float(rate.group(1)),
        }
    return None

def estimate_runtime(info):
    if info["rate"] == 0:
        return "∞"
    hours = info["energy_now"] / info["rate"]
    return f"{hours:.1f}h (~{hours*60:.0f} min)"

# -------------------------------
# Teste de bateria automatizado
# -------------------------------

def measure_phase(name, duration, command):
    print(f"\n🔋 Iniciando fase: {name} ({duration}s)")
    time.sleep(2)

    # Captura consumo antes
    info_before = get_battery_info()

    # Inicia powertop em background para medir média
    report_file = f"{name.lower()}.html"
    powertop_proc = subprocess.Popen(
        f"sudo powertop --time={duration} --html={report_file}",
        shell=True
    )

    # Roda o comando principal (stress ou vídeo)
    subprocess.run(command, shell=True)

    # Aguarda powertop terminar
    powertop_proc.wait()

    # Captura consumo depois
    info_after = get_battery_info()

    # Cálculo básico
    used = info_before["energy_now"] - info_after["energy_now"]
    avg_rate = used / (duration / 3600)
    print(f"⚙️  Fase {name} concluída: {avg_rate:.2f} W médios")

    return {
        "fase": name,
        "consumo_medio": round(avg_rate, 2),
        "arquivo": report_file,
        "runtime_est": estimate_runtime(info_after),
    }

# -------------------------------
# Execução principal
# -------------------------------

def main():
    print("\n=== 🔋 Teste Automático de Bateria ===\n")
    print("Certifique-se de que o notebook está RODANDO NA BATERIA.\n")
    time.sleep(3)

    os.makedirs("battery_reports", exist_ok=True)
    os.chdir("battery_reports")

    phases = []

    # Fase 1 – Stress total
    phases.append(measure_phase(
        "Stress",
        300,
        f"stress --cpu $(nproc) --io 4 --vm 2 --vm-bytes 512M --timeout 300"
    ))

    # Fase 2 – Vídeo playback
    video_path = input("\n🎬 Caminho do vídeo (ex: /home/user/video.mp4): ").strip()
    if not os.path.exists(video_path):
        print("❌ Vídeo não encontrado.")
        sys.exit(1)

    phases.append(measure_phase(
        "Video",
        300,
        f"mpv --quiet --vo=gpu --hwdec=auto --loop=inf --really-quiet {video_path} --length=300"
    ))

    # Gera relatório final
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open("relatorio_final.html", "w") as f:
        f.write(f"""
        <html><head><title>Relatório de Teste de Bateria</title></head>
        <body style='font-family:sans-serif'>
        <h2>🔋 Relatório de Teste de Bateria ({now})</h2>
        <table border=1 cellspacing=0 cellpadding=6>
        <tr><th>Fase</th><th>Consumo Médio (W)</th><th>Autonomia Estimada</th><th>Relatório Powertop</th></tr>
        {''.join(f"<tr><td>{p['fase']}</td><td>{p['consumo_medio']}</td><td>{p['runtime_est']}</td><td><a href='{p['arquivo']}'>Ver</a></td></tr>" for p in phases)}
        </table>
        </body></html>
        """)

    print("\n✅ Teste completo! Relatório salvo em: battery_reports/relatorio_final.html")

if __name__ == "__main__":
    main()
