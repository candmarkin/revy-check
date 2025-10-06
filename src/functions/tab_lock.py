# DESATIVANDO ALT TAB
import subprocess

def disable_alt_tab():
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.wm.keybindings",
        "switch-applications", "[]"
    ])
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.wm.keybindings",
        "switch-windows", "[]"
    ])

def restore_alt_tab():
    subprocess.run([
        "gsettings", "reset",
        "org.gnome.desktop.wm.keybindings",
        "switch-applications"
    ])
    subprocess.run([
        "gsettings", "reset",
        "org.gnome.desktop.wm.keybindings",
        "switch-windows"
    ])
