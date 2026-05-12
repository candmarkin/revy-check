import argparse
import io
import sys
import time
import threading
import os

import mss
import requests
import pydirectinput
from PIL import Image

try:
    import tkinter as tk
    from tkinter import font as tkfont
except Exception:
    tk = None


def take_screenshot_bytes():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img_pil = Image.frombytes("RGB", img.size, img.rgb)
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG")
        buf.seek(0)
        return buf


def post_screenshot(url, screenshot_buf, force=None, timeout=10):
    params = {}
    if force:
        params['force'] = force
    files = {'screenshot': ('s.png', screenshot_buf, 'image/png')}
    resp = requests.post(url, params=params, files=files, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def show_fullscreen_reprovado(duration=7):
    if tk is None:
        print('Tkinter not available; cannot show fullscreen. Exiting.')
        return

    root = tk.Tk()
    root.title('REPROVADO')
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='black')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    f = tkfont.Font(family='Helvetica', size=int(min(screen_width, screen_height) / 6), weight='bold')
    lbl = tk.Label(root, text='REPROVADO', fg='red', bg='black', font=f)
    lbl.pack(expand=True)

    def close(event=None):
        try:
            root.destroy()
        except Exception:
            pass

    root.bind('<Key>', close)
    root.bind('<Button>', close)

    def delayed_close():
        time.sleep(duration)
        try:
            root.quit()
        except Exception:
            pass

    t = threading.Thread(target=delayed_close, daemon=True)
    t.start()
    root.mainloop()


def show_fullscreen_aprovado(duration=7):
    if tk is None:
        print('Tkinter not available; cannot show fullscreen approved. Exiting.')
        return

    root = tk.Tk()
    root.title('APROVADO')
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='black')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    f = tkfont.Font(family='Helvetica', size=int(min(screen_width, screen_height) / 6), weight='bold')
    lbl = tk.Label(root, text='APROVADO', fg='lime', bg='black', font=f)
    lbl.pack(expand=True)

    def close(event=None):
        try:
            root.destroy()
        except Exception:
            pass

    root.bind('<Key>', close)
    root.bind('<Button>', close)

    def delayed_close():
        time.sleep(duration)
        try:
            root.quit()
        except Exception:
            pass

    t = threading.Thread(target=delayed_close, daemon=True)
    t.start()
    root.mainloop()


def send_hotkey_ctrl_shift_f3():
    pydirectinput.FAILSAFE = False
    pydirectinput.PAUSE = 0.1
    try:
        pydirectinput.hotkey('ctrl', 'shift', 'f3')
    except Exception:
        # fallback to pressing keys separately
        try:
            pydirectinput.keyDown('ctrl')
            pydirectinput.keyDown('shift')
            pydirectinput.press('f3')
            pydirectinput.keyUp('shift')
            pydirectinput.keyUp('ctrl')
        except Exception:
            pass
    
    
def show_fullscreen_ask_approval():
    if tk is None:
        print('Tkinter not available; cannot ask for approval.')
        return None

    def show_approved_screen(duration=5):
        # show a temporary fullscreen "APROVADO" screen and send the hotkey
        try:
            # send hotkey first (non-blocking)
            try:
                send_hotkey_ctrl_shift_f3()
            except Exception as e:
                print('Failed to send approval hotkey:', e)

            approved_root = tk.Tk()
            approved_root.title('APROVADO')
            approved_root.attributes('-fullscreen', True)
            approved_root.attributes('-topmost', True)
            approved_root.configure(bg='black')

            sw = approved_root.winfo_screenwidth()
            sh = approved_root.winfo_screenheight()
            f = tkfont.Font(family='Helvetica', size=int(min(sw, sh) / 6), weight='bold')
            lbl = tk.Label(approved_root, text='APROVADO', fg='lime', bg='black', font=f)
            lbl.pack(expand=True)

            def close_app(event=None):
                try:
                    approved_root.destroy()
                except Exception:
                    pass

            approved_root.bind('<Key>', close_app)
            approved_root.bind('<Button>', close_app)

            def delayed():
                time.sleep(duration)
                try:
                    approved_root.quit()
                except Exception:
                    pass

            t = threading.Thread(target=delayed, daemon=True)
            t.start()
            approved_root.mainloop()
        except Exception as e:
            print('Failed to show approved screen:', e)

    root = tk.Tk()
    root.title('Resultado Desconhecido')
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='black')
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # big font
    f = tkfont.Font(family='Helvetica', size=int(min(screen_width, screen_height) / 10), weight='bold')

    lbl = tk.Label(root, text='Resultado desconhecido\nEscolha uma opção', fg='white', bg='black', font=tkfont.Font(size=24))
    lbl.pack(pady=40)

    btn_frame = tk.Frame(root, bg='black')
    btn_frame.pack(expand=True)

    def on_approve():
        try:
            root.destroy()
        except Exception:
            pass
        show_fullscreen_aprovado()
        nonlocal_choice[0] = 'ok'

    def on_reprove():
        try:
            root.destroy()
        except Exception:
            pass
        show_fullscreen_reprovado()
        nonlocal_choice[0] = 'reprovado'

    approve_btn = tk.Button(btn_frame, text='APROVADO', bg='green', fg='black', font=f, width=12, height=2, command=on_approve)
    approve_btn.pack(side='left', padx=40)

    reprove_btn = tk.Button(btn_frame, text='REPROVADO', bg='red', fg='white', font=f, width=12, height=2, command=on_reprove)
    reprove_btn.pack(side='right', padx=40)

    # allow escape to close
    def on_key(event=None):
        try:
            root.destroy()
        except Exception:
            pass

    root.bind('<Escape>', on_key)
    # use a mutable to capture the button choice from nested functions
    nonlocal_choice = [None]
    root.mainloop()
    return nonlocal_choice[0]

def execute_actions(actions):
    for key in actions:
        try:
            if '+' in key:
                parts = key.split('+')
                pydirectinput.hotkey(*parts)
            else:
                pydirectinput.press(key)
            time.sleep(0.1)
        except Exception as e:
            print('Failed to send key', key, e)


def analyze_step(base_analyze_url, step_name, screenshot_buf, force=None, timeout=10):
    # step_name optional; if provided, add as query param
    if step_name:
        url = base_analyze_url + f"?step={step_name}"
    else:
        url = base_analyze_url
    return post_screenshot(url, screenshot_buf, force=force, timeout=timeout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default=os.getenv('API_URL', 'http://192.168.3.118:5000/oobe_analyze'), help='API URL')
    parser.add_argument('--force', choices=['reprovado', 'ok'], help='Force API response (for testing)')
    parser.add_argument('--show-duration', type=int, default=7, help='Seconds to show fullscreen message')
    parser.add_argument('--interval', type=float, default=5.0, help='Seconds between screenshots when looping')
    args = parser.parse_args()

    # Main loop: post screenshots to /oobe_analyze and react to server decisions.
    # Always send the current running step to the API.
    current_step = 'step1'
    while True:
        try:
            buf = take_screenshot_bytes()
        except Exception as e:
            print('Failed to take screenshot:', e)
            sys.exit(2)

        try:
            resp = analyze_step(args.url, current_step, buf, force=args.force)
        except Exception as e:
            print('Analyze request failed:', e)
            time.sleep(args.interval)
            continue

        print('Analyze returned:', resp)
        result = (resp.get('result') or '').lower()

        # If server reports a matched text for a step, execute actions from analyze response.
        matched_step = resp.get('step')
        matched_text = resp.get('matched')
        next_step = resp.get('next')
        if matched_step and matched_text:
            print(f"Server matched step '{matched_step}' (matched: {matched_text})")

            actions = resp.get('action', []) or []
            if actions:
                execute_actions(actions)

            if next_step:
                print('Advancing to next step:', next_step)
                current_step = next_step
                # continue polling; server will indicate future matches
                time.sleep(args.interval)
                continue

            # no next -> final
            if result in ('ok', 'aprovado'):
                show_fullscreen_aprovado(duration=args.show_duration)
                sys.exit(0)
            if result == 'reprovado':
                show_fullscreen_reprovado(duration=args.show_duration)
                sys.exit(0)

        if result in ('aguardando',):
            print('Result is aguardando -> retrying in', args.interval)
            time.sleep(args.interval)
            continue

        if result == 'unknown':
            try:
                choice = show_fullscreen_ask_approval()
            except Exception as e:
                print('Failed to show approval prompt:', e)
                choice = None

            if choice == 'ok':
                show_fullscreen_aprovado(duration=args.show_duration)
                sys.exit(0)
            elif choice == 'reprovado':
                show_fullscreen_reprovado(duration=args.show_duration)
                sys.exit(0)
            else:
                time.sleep(args.interval)
                continue

        # generic final handlers
        if result == 'reprovado':
            show_fullscreen_reprovado(duration=args.show_duration)
            sys.exit(0)
        if result in ('ok', 'aprovado'):
            show_fullscreen_aprovado(duration=args.show_duration)
            send_hotkey_ctrl_shift_f3()
            sys.exit(0)

        print('Unexpected analyze response, retrying in', args.interval)
        time.sleep(args.interval)

if __name__ == '__main__':
    main()