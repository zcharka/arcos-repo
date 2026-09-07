import os
import sys
import subprocess
import json
import shutil
import urllib.request
import urllib.parse
import re
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
    "ogulniega": ["ogulniega"],
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
        "ogulniega": ["ogulniega"],
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

def _run_as_user_async(cmd: list,
                      on_output: Callable[[str, str], None],
                      on_finished: Callable[[int], None]):
    """Run a command as the current (non-root) user in a background thread.
    Used for AUR helpers (paru/yay) and flatpak. Passes PACMAN_AUTH and
    SUDO_ASKPASS if user_password is set so sudo doesn't fail on AUR installs."""
    import threading
    manager = get_sudo_manager()

    def _thread():
        try:
            on_output(f"$ {' '.join(cmd)}\n", "cmd")
            env = os.environ.copy()
            if manager.user_password:
                env["PACMAN_AUTH"] = manager.wrapper_path
                env["SUDO_ASKPASS"] = manager.askpass_script
                env["SUDO_FLAGS"] = "-A"
                manager.start_privileged_session()

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            if proc.stdin:
                try:
                    proc.stdin.write("\n\n\n\n\n")
                    proc.stdin.flush()
                except Exception:
                    pass

            if proc.stdout:
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        on_output(line, "info")
            proc.wait()
            rc = proc.returncode
            if rc == 0:
                on_output("\n[SUKCES] Operacja zakończona sukcesem (kod 0).\n", "success")
            else:
                on_output(f"\n[BŁĄD] Operacja nie powiodła się (kod {rc}).\n", "error")
            on_finished(rc)
        except Exception as e:
            on_output(f"\n[BŁĄD] Wystąpił wyjątek: {e}\n", "error")
            on_finished(-1)
        finally:
            if manager.user_password:
                manager.stop_privileged_session()

    threading.Thread(target=_thread, daemon=True).start()

def open_arch_wiki(pkg_name: str, on_fetched_cb=None):
    """Searches Arch Wiki API for exact article and returns summary or opens in browser."""
    import urllib.parse
    import urllib.request
    import webbrowser
    import threading
    import json
    import re

    wiki_search_term = pkg_name
    if pkg_name == "x11":
        wiki_search_term = "Xorg"
    elif pkg_name in ["vtrt-manager", "virt-manager"]:
        wiki_search_term = "virt-manager"

    def _fetch():
        try:
            search_url = (
                "https://wiki.archlinux.org/api.php?"
                "action=opensearch&format=json&redirects=resolve&limit=1"
                f"&search={urllib.parse.quote(wiki_search_term)}"
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "ArcHello/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                results = json.loads(resp.read().decode())
                titles = results[1] if len(results) > 1 else []
                urls = results[3] if len(results) > 3 else []
                top_url = urls[0] if urls else f"https://wiki.archlinux.org/index.php?search={urllib.parse.quote(pkg_name)}"
                top_title = titles[0] if titles else pkg_name

            # Fetch parsed html summary
            p_url = (
                "https://wiki.archlinux.org/api.php?"
                "action=parse&prop=text&format=json&redirects=1"
                f"&page={urllib.parse.quote(top_title)}"
            )
            req2 = urllib.request.Request(p_url, headers={"User-Agent": "ArcHello/1.0"})
            with urllib.request.urlopen(req2, timeout=6) as resp2:
                data = json.loads(resp2.read().decode())
                html_raw = data.get("parse", {}).get("text", {}).get("*", "")
            if on_fetched_cb:
                on_fetched_cb(html_raw, top_url)
            else:
                webbrowser.open(top_url)
        except Exception:
            fallback_url = f"https://wiki.archlinux.org/index.php?search={urllib.parse.quote(wiki_search_term)}"
            if on_fetched_cb:
                on_fetched_cb("Nie udało się pobrać treści z Arch Wiki. Kliknij ikona obok, aby otworzyć przeglądarkę.", fallback_url)
            else:
                webbrowser.open(fallback_url)

    threading.Thread(target=_fetch, daemon=True).start()

def get_installed_package_version(pkg_key: str) -> str:
    """Returns installed package version string or empty string."""
    pkgs = PACKAGE_MAP.get(pkg_key, [pkg_key])
    for pkg in pkgs:
        try:
            res = subprocess.run(["pacman", "-Q", pkg], capture_output=True, text=True)
            if res.returncode == 0:
                parts = res.stdout.strip().split()
                if len(parts) >= 2:
                    return parts[1]
        except Exception:
            pass
        try:
            res = subprocess.run(["flatpak", "info", pkg], capture_output=True, text=True)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "Version:" in line:
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
    return ""

def install_package_with_fallback(pkg_key: str,
                                 parent_window,
                                 on_output: Callable[[str, str], None],
                                 on_finished: Callable[[int], None]):
    if pkg_key == "x11":
        pkgs = get_x11_installation_packages()
    else:
        pkgs = PACKAGE_MAP.get(pkg_key, [pkg_key])
    manager = get_sudo_manager()

    if pkg_key in ["vtrt-manager", "virt-manager"]:
        can_pacman = True
    elif pkg_key == "ogulniega":
        can_pacman = True
    else:
        res = subprocess.run(["pacman", "-Si"] + pkgs, capture_output=True, text=True)
        can_pacman = (res.returncode == 0)

    def _execute_install():
        if pkg_key in ["vtrt-manager", "virt-manager"]:
            vtrt_pkgs = ["virt-manager", "qemu-desktop", "libvirt", "dnsmasq", "iptables-nft", "ebtables", "openbsd-netcat"]
            cmd = ["pacman", "-S", "--needed", "--noconfirm"] + vtrt_pkgs

            def _on_vtrt_installed(code):
                if code == 0:
                    try:
                        on_output("\n[INFO] Konfigurowanie usług wirtualizacji (libvirtd, grupa użytkowników)...\n", "info")
                        curr_user = os.environ.get("SUDO_USER") or os.environ.get("USER") or os.getlogin()
                        env = os.environ.copy()
                        if manager.user_password:
                            env["SUDO_ASKPASS"] = manager.askpass_script
                            env["PACMAN_AUTH"] = manager.wrapper_path
                        subprocess.run(["sudo", "-A", "usermod", "-aG", "libvirt", curr_user], capture_output=True, env=env)
                        subprocess.run(["sudo", "-A", "systemctl", "enable", "--now", "libvirtd.service"], capture_output=True, env=env)
                        subprocess.run(["sudo", "-A", "virsh", "net-autostart", "default"], capture_output=True, env=env)
                        subprocess.run(["sudo", "-A", "virsh", "net-start", "default"], capture_output=True, env=env)
                        on_output(f"\n[SUKCES] Użytkownik {curr_user} został dodany do grupy libvirt. Usługa libvirtd została włączona!\n", "success")
                    except Exception as ex:
                        on_output(f"\n[OSTRZEŻENIE] Konfiguracja dodatkowa libvirt: {ex}\n", "info")
                on_finished(code)

            manager.run_privileged_async(cmd, on_output, _on_vtrt_installed)
        elif can_pacman:
            cmd = ["pacman", "-S", "--needed", "--noconfirm"] + pkgs
            manager.run_privileged_async(cmd, on_output, on_finished)
        elif shutil.which("paru"):
            cmd = ["paru", "-S", "--needed", "--noconfirm", "--skipreview"]
            if manager.user_password:
                cmd.extend(["--sudo", manager.wrapper_path])
            cmd.extend(pkgs)
            _run_as_user_async(cmd, on_output, on_finished)
        elif shutil.which("yay"):
            cmd = ["yay", "-S", "--needed", "--noconfirm", "--answerclean", "None", "--answerdiff", "None", "--answeredit", "None", "--answerupgrade", "None"]
            if manager.user_password:
                cmd.extend(["--sudo", manager.wrapper_path])
            cmd.extend(pkgs)
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

    # If password is non-empty or is flatpak-only install
    is_flatpak_only = (not can_pacman and not shutil.which("paru") and not shutil.which("yay") and pkg_key in ["blockbench", "sober"])
    if manager.user_password or is_flatpak_only:
        _execute_install()
    else:
        from arc_hello.auth.dialogs import prompt_password
        prompt_password(
            parent_window,
            f"Wprowadź hasło administratora, aby zainstalować pakiet {pkg_key}.",
            _execute_install,
            on_cancel=lambda: on_finished(-1)
        )

def uninstall_package_with_fallback(pkg_key: str,
                                   parent_window,
                                   on_output: Callable[[str, str], None],
                                   on_finished: Callable[[int], None]):
    """Uninstalls a package asynchronously with privilege escalation."""
    pkgs = PACKAGE_MAP.get(pkg_key, [pkg_key])
    manager = get_sudo_manager()

    def _execute_uninstall():
        cmd = ["pacman", "-R", "--noconfirm"] + pkgs
        manager.run_privileged_async(cmd, on_output, on_finished)

    if manager.user_password:
        _execute_uninstall()
    else:
        from arc_hello.auth.dialogs import prompt_password
        prompt_password(
            parent_window,
            f"Wprowadź hasło administratora, aby odinstalować pakiet {pkg_key}.",
            _execute_uninstall,
            on_cancel=lambda: on_finished(-1)
        )

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
    """Check if X11 session packages are installed for the currently active Desktop Environment."""
    de_info = detect_desktop_environment()
    de = de_info["de"]

    try:
        res = subprocess.run(["pacman", "-Qq", "xorg-server"], capture_output=True, text=True)
        if res.returncode != 0:
            return False
    except Exception:
        return False

    if de == "KDE Plasma":
        for pkg in ["plasma-x11-session", "plasma-workspace-x11"]:
            try:
                res = subprocess.run(["pacman", "-Qq", pkg], capture_output=True, text=True)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
        return False
    elif de == "GNOME":
        try:
            res = subprocess.run(["pacman", "-Qq", "gnome-session"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False
    elif de == "XFCE":
        try:
            res = subprocess.run(["pacman", "-Qq", "xfce4-session"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False

    return True

def get_x11_installation_packages() -> list[str]:
    de_info = detect_desktop_environment()
    de = de_info["de"]

    pkgs = ["xorg-server", "xorg-xinit"]
    if de == "KDE Plasma":
        for pkg in ["plasma-x11-session", "plasma-workspace-x11"]:
            try:
                res = subprocess.run(["pacman", "-Si", pkg], capture_output=True, text=True)
                if res.returncode == 0:
                    pkgs.append(pkg)
                    break
            except Exception:
                pass
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
