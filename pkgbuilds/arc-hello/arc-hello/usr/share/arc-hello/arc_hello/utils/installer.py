import os
import sys
from arc_hello.auth.sudo_manager import get_sudo_manager
from arc_hello.auth.dialogs import prompt_password

INSTALL_BIN = "/usr/bin/arc-hello"
INSTALL_SHARE = "/usr/share/arc-hello"
DESKTOP_FILE = "/usr/share/applications/arc-hello.desktop"

def is_running_from_system() -> bool:
    current_script = os.path.abspath(sys.argv[0])
    return current_script == INSTALL_BIN or current_script.startswith(INSTALL_SHARE)

def install_system_files() -> bool:
    manager = get_sudo_manager()
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    try:
        manager.run_privileged(["mkdir", "-p", "/usr/bin"])
        manager.run_privileged(["mkdir", "-p", INSTALL_SHARE])
        manager.run_privileged(["mkdir", "-p", "/usr/share/applications"])
        manager.run_privileged(["mkdir", "-p", "/usr/share/images"])
        manager.run_privileged(["mkdir", "-p", "/usr/share/programs"])

        share_src = os.path.join(pkg_root, "share", "arc-hello")
        bin_src = os.path.join(pkg_root, "bin", "arc-hello")
        desktop_src = os.path.join(pkg_root, "share", "applications", "arc-hello.desktop")
        images_src = os.path.join(pkg_root, "share", "images")
        programs_src = os.path.join(pkg_root, "share", "programs")

        if os.path.exists(share_src):
            manager.run_privileged(["cp", "-rf", share_src + "/.", INSTALL_SHARE + "/"])
        if os.path.exists(bin_src):
            manager.run_privileged(["cp", "-f", bin_src, INSTALL_BIN])
            manager.run_privileged(["chmod", "+x", INSTALL_BIN])
        if os.path.exists(desktop_src):
            manager.run_privileged(["cp", "-f", desktop_src, DESKTOP_FILE])
            manager.run_privileged(["chmod", "644", DESKTOP_FILE])
        if os.path.exists(images_src):
            manager.run_privileged(["cp", "-rf", images_src + "/.", "/usr/share/images/"])
        if os.path.exists(programs_src):
            manager.run_privileged(["cp", "-rf", programs_src + "/.", "/usr/share/programs/"])

        return True
    except Exception as e:
        print(f"Błąd podczas instalacji systemowej Arc Hello: {e}")
        return False

def ensure_installed(parent_window, on_complete_cb):
    if is_running_from_system():
        on_complete_cb(True)
        return

    def _do_install():
        ok = install_system_files()
        on_complete_cb(ok)

    prompt_password(
        parent_window,
        "Aplikacja Arc Hello zostanie automatycznie zainstalowana w systemie (/usr/bin/arc-hello).\n"
        "Podaj hasło administratora, aby kontynuować.",
        _do_install,
        primary_label="Zainstaluj w systemie"
    )
