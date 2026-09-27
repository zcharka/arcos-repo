import os

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "arc-hello.desktop")

DESKTOP_ENTRY_CONTENT = """[Desktop Entry]
Type=Application
Name=Arc Hello
Comment=ArcOS Welcome and Setup Assistant
Exec=arc-hello
Icon=system-run-symbolic
Terminal=false
Categories=Utility;System;
X-GNOME-Autostart-enabled=true
"""

def is_autostart_enabled() -> bool:
    if not os.path.exists(AUTOSTART_FILE):
        return False
    try:
        with open(AUTOSTART_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if "X-GNOME-Autostart-enabled=false" in content or "Hidden=true" in content:
                return False
        return True
    except Exception:
        return False

def set_autostart_enabled(enabled: bool) -> bool:
    try:
        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        if enabled:
            with open(AUTOSTART_FILE, "w", encoding="utf-8") as f:
                f.write(DESKTOP_ENTRY_CONTENT)
        else:
            if os.path.exists(AUTOSTART_FILE):
                os.remove(AUTOSTART_FILE)
        return True
    except Exception as e:
        print(f"Error updating autostart status: {e}")
        return False

def ensure_autostart_default():
    if not os.path.exists(AUTOSTART_FILE):
        set_autostart_enabled(True)
