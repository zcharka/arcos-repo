import os
import sys
import subprocess
import json
import shutil
from typing import Callable, List, Dict, Optional
from arc_hello.auth.sudo_manager import get_sudo_manager

STEAM_SETTINGS_FILE = os.path.expanduser("~/.config/arc-hello/steam_settings.json")

PACKAGE_MAP = {
    "vtrt-manager": ["virt-manager", "qemu-desktop", "libvirt", "dnsmasq"],
    "virt-manager": ["virt-manager", "qemu-desktop", "libvirt", "dnsmasq"],
    "blockbench": ["blockbench"],
    "blender": ["blender"],
    "opera": ["opera"],
    "sober": ["sober"],
    "ogulniega": ["com.ogulniega.launcher"],
    "gamemode": ["gamemode"],
    "gamescope": ["gamescope"],
    "arc-store": ["arc-store"]
}

def get_szczur_logo_path() -> str:
    """Returns absolute path to szczur.svg logo."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # base_dir = .../arc_hello/utils  ->  up 3 = .../usr/share/
    share_dir = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    candidates = [
        "/usr/share/images/szczur.svg",
        os.path.join(share_dir, "images", "szczur.svg"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "system-run-symbolic"

def get_ogulniega_flatpakref_path() -> Optional[str]:
    """Returns path to OgulniegaInstaller.flatpakref."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    share_dir = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))
    candidates = [
        "/usr/share/programs/OgulniegaInstaller.flatpakref",
        os.path.join(share_dir, "programs", "OgulniegaInstaller.flatpakref"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def is_package_installed(pkg_key: str) -> bool:
    binary_names = {
        "vtrt-manager": ["virt-manager", "vtrt-manager"],
        "virt-manager": ["virt-manager"],
        "blockbench": ["blockbench", "Blockbench"],
        "blender": ["blender"],
        "opera": ["opera"],
        "sober": ["sober"],
        "ogulniega": ["com.ogulniega.launcher", "ogulniega"],
        "gamemode": ["gamemoded"],
        "gamescope": ["gamescope"],
        "arc-store": ["arc-store", "arc-store-gui"]
    }

    for b in binary_names.get(pkg_key, [pkg_key]):
        if shutil.which(b):
            return True

    pkgs = PACKAGE_MAP.get(pkg_key, [pkg_key])
    for pkg in pkgs:
        try:
            res = subprocess.run(["pacman", "-Qq", pkg], capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    if shutil.which("flatpak"):
        flatpak_ids = {
            "blockbench": "net.blockbench.Blockbench",
            "sober": "org.vinegarhq.Sober",
            "ogulniega": "com.ogulniega.launcher"
        }
        f_id = flatpak_ids.get(pkg_key)
        if f_id:
            try:
                res = subprocess.run(["flatpak", "info", f_id], capture_output=True, text=True)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

    return False

def install_package_with_fallback(pkg_key: str,
                                 parent_window,
                                 on_output: Callable[[str, str], None],
                                 on_finished: Callable[[int], None]):
    # Handle Ogulniega flatpakref installation
    if pkg_key == "ogulniega":
        ref_path = get_ogulniega_flatpakref_path()
        if ref_path and shutil.which("flatpak"):
            cmd = ["flatpak", "install", ref_path]
        elif shutil.which("flatpak"):
            cmd = ["flatpak", "install", "com.ogulniega.launcher"]
        else:
            on_output("Flatpak nie jest zainstalowany! Zainstaluj flatpak, aby kontynuować.\n", "error")
            on_finished(-1)
            return
        _run_as_user_async(cmd, on_output, on_finished)
        return

    pkgs = PACKAGE_MAP.get(pkg_key, [pkg_key])
    manager = get_sudo_manager()

    res = subprocess.run(["pacman", "-Si"] + pkgs, capture_output=True, text=True)
    can_pacman = (res.returncode == 0)

    if can_pacman:
        # Oficjalne repozytoria — potrzeba sudo
        cmd = ["pacman", "-S", "--needed", "--noconfirm"] + pkgs
        manager.run_privileged_async(cmd, on_output, on_finished)
    elif shutil.which("paru"):
        # AUR helper — NIE uruchamiaj jako root!
        cmd = ["paru", "-S", "--needed", "--noconfirm"] + pkgs
        _run_as_user_async(cmd, on_output, on_finished)
    elif shutil.which("yay"):
        # AUR helper — NIE uruchamiaj jako root!
        cmd = ["yay", "-S", "--needed", "--noconfirm"] + pkgs
        _run_as_user_async(cmd, on_output, on_finished)
    elif pkg_key in ["blockbench", "sober"] and shutil.which("flatpak"):
        flatpak_map = {
            "blockbench": "net.blockbench.Blockbench",
            "sober": "org.vinegarhq.Sober"
        }
        f_id = flatpak_map.get(pkg_key)
        cmd = ["flatpak", "install", "-y", "flathub", f_id]
        _run_as_user_async(cmd, on_output, on_finished)
    else:
        cmd = ["pacman", "-S", "--needed", "--noconfirm"] + pkgs
        manager.run_privileged_async(cmd, on_output, on_finished)

# -------------------------- STEAM BIG PICTURE --------------------------

def get_steam_big_picture_setting() -> bool:
    if not os.path.exists(STEAM_SETTINGS_FILE):
        return True
    try:
        with open(STEAM_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("big_picture_enabled", True)
    except Exception:
        return True

def set_steam_big_picture_setting(enabled: bool) -> bool:
    try:
        os.makedirs(os.path.dirname(STEAM_SETTINGS_FILE), exist_ok=True)
        with open(STEAM_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"big_picture_enabled": enabled}, f, indent=2)
        return True
    except Exception as e:
        print(f"Error setting Big Picture mode: {e}")
        return False

# -------------------------- X11 & DE DETECTION --------------------------

def detect_desktop_environment() -> Dict[str, str]:
    de_raw = (os.getenv("XDG_CURRENT_DESKTOP", "") + " " + os.getenv("DESKTOP_SESSION", "")).upper()
    session_type = os.getenv("XDG_SESSION_TYPE", "").lower()

    de_name = "Nieznane (Unknown)"
    if "KDE" in de_raw or "PLASMA" in de_raw:
        de_name = "KDE Plasma"
    elif "GNOME" in de_raw:
        de_name = "GNOME"
    elif "XFCE" in de_raw:
        de_name = "XFCE"
    elif "CINNAMON" in de_raw:
        de_name = "Cinnamon"
    elif "HYPRLAND" in de_raw or "SWAY" in de_raw:
        de_name = "Wayland Compositor (Hyprland/Sway)"
    elif de_raw.strip():
        de_name = de_raw.strip().capitalize()

    return {
        "de": de_name,
        "session_type": session_type if session_type else "x11",
        "raw_de": de_raw
    }

def is_x11_installed() -> bool:
    """Check if xorg-server package is actually installed via pacman.
    Don't rely on binary detection — Xwayland provides /usr/bin/X
    but that's NOT a full X11 session server."""
    try:
        res = subprocess.run(["pacman", "-Qq", "xorg-server"],
                             capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def get_x11_installation_packages() -> list[str]:
    de_info = detect_desktop_environment()
    de = de_info["de"]

    pkgs = ["xorg-server", "xorg-xinit"]
    if de == "KDE Plasma":
        pkgs.append("plasma-workspace-x11")
    elif de == "GNOME":
        pkgs.append("gnome-session")
    elif de == "XFCE":
        pkgs.append("xfce4-session")

    return pkgs

# -------------------------- DEFAULT APPLICATIONS --------------------------

APP_CATEGORIES = {
    "Przeglądarka internetowa": {
        "mimes": ["text/html", "x-scheme-handler/http", "x-scheme-handler/https"],
        "icon": "web-browser-symbolic"
    },
    "Odtwarzacz wideo": {
        "mimes": ["video/mp4", "video/x-matroska", "video/webm", "video/avi"],
        "icon": "multimedia-video-player-symbolic"
    },
    "Edytor tekstu": {
        "mimes": ["text/plain", "application/json", "text/x-python", "text/markdown"],
        "icon": "accessories-text-editor-symbolic"
    },
    "Przeglądarka obrazów": {
        "mimes": ["image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"],
        "icon": "image-viewer-symbolic"
    },
    "Menedżer plików": {
        "mimes": ["inode/directory"],
        "icon": "system-file-manager-symbolic"
    },
    "Odtwarzacz muzyki": {
        "mimes": ["audio/mpeg", "audio/flac", "audio/wav", "audio/ogg"],
        "icon": "audio-x-generic-symbolic"
    }
}

def get_installed_desktop_files() -> List[Dict[str, str]]:
    dirs = [
        "/usr/share/applications",
        os.path.expanduser("~/.local/share/applications")
    ]
    apps = []
    seen = set()

    for d in dirs:
        if not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            if fname.endswith(".desktop") and fname not in seen:
                seen.add(fname)
                fpath = os.path.join(d, fname)
                app_info = parse_desktop_file(fpath, fname)
                if app_info and app_info.get("name") and not app_info.get("no_display"):
                    apps.append(app_info)

    return sorted(apps, key=lambda x: x["name"].lower())

def parse_desktop_file(fpath: str, fname: str) -> Optional[Dict[str, str]]:
    try:
        name = ""
        icon = "application-x-executable-symbolic"
        no_display = False
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            is_main_entry = False
            for line in f:
                line = line.strip()
                if line == "[Desktop Entry]":
                    is_main_entry = True
                    continue
                elif line.startswith("[") and line.endswith("]"):
                    is_main_entry = False
                    continue
                if is_main_entry:
                    if line.startswith("Name=") and not name:
                        name = line.split("=", 1)[1]
                    elif line.startswith("Icon="):
                        icon = line.split("=", 1)[1]
                    elif line.startswith("NoDisplay=true") or line.startswith("Hidden=true"):
                        no_display = True

        if name:
            return {
                "name": name,
                "desktop_file": fname,
                "icon": icon,
                "no_display": no_display
            }
    except Exception:
        pass
    return None

def get_current_default_app(mime_type: str) -> str:
    try:
        res = subprocess.run(["xdg-mime", "query", "default", mime_type], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "Brak (Unassigned)"

def set_default_app_for_mimes(desktop_file: str, mime_list: List[str]) -> bool:
    success = True
    for mime in mime_list:
        try:
            res = subprocess.run(["xdg-mime", "default", desktop_file, mime], capture_output=True, text=True)
            if res.returncode != 0:
                success = False
        except Exception:
            success = False
    return success
