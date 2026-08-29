import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.widgets.icons import load_icon
from arc_hello.auth.sudo_manager import get_sudo_manager
from arc_hello.utils.system import (
    detect_desktop_environment,
    is_x11_installed,
    get_x11_installation_packages
)

class X11InstallerDialog(Adw.Window):
    def __init__(self, parent_window, run_cmd_cb, show_toast_cb):
        super().__init__(transient_for=parent_window, modal=True)
        self.set_title("Instalator Sesji X11")
        self.set_default_size(560, 480)

        self.parent_window = parent_window
        self.run_cmd_cb = run_cmd_cb
        self.show_toast_cb = show_toast_cb
        self.de_info = detect_desktop_environment()

        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        clamp = Adw.Clamp(maximum_size=520)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        icon = load_icon("dialog-warning-symbolic", size=48)
        box.append(icon)

        title = Gtk.Label()
        title.set_markup('<span size="large" weight="bold">Ostrzeżenie dotyczące serwera X11</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        warning_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        warning_card.add_css_class("app-card")

        lbl_warn = Gtk.Label()
        lbl_warn.set_markup(
            "<b>Ostrzeżenie:</b> Serwer wyświetlania X11 jest technologią przestarzałą na rzecz Waylanda. "
            "Jednak niektóre starsze aplikacje lub gry mogą wciąż go wymagać do prawidłowego działania.\n\n"
            "<b>Instrukcja użycia:</b>\n"
            "1. Po zainstalowaniu sesji wyloguj się z systemu.\n"
            "2. Na ekranie logowania (Display Manager) kliknij ikonę wyboru sesji w rogu.\n"
            "3. Wybierz sesję z dopiskiem <b>(X11)</b> lub <b>(Xorg)</b> i zaloguj się ponownie."
        )
        lbl_warn.set_wrap(True)
        lbl_warn.set_justify(Gtk.Justification.LEFT)
        warning_card.append(lbl_warn)

        box.append(warning_card)

        de_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        de_card.add_css_class("app-card")

        lbl_de_info = Gtk.Label()
        lbl_de_info.set_markup(
            f"Wykryte środowisko graficzne (DE): <b>{self.de_info['de']}</b>\n"
            f"Obecny typ sesji: <b>{self.de_info['session_type'].upper()}</b>"
        )
        lbl_de_info.set_halign(Gtk.Align.START)
        de_card.append(lbl_de_info)

        x11_present = is_x11_installed()
        is_current_x11 = self.de_info['session_type'].lower() == "x11"

        self.can_install = True

        if is_current_x11:
            self.status_msg = "<b>Informacja:</b> Aktualnie pracujesz już w sesji X11!"
            self.can_install = False
        elif x11_present:
            self.status_msg = (
                "<b>Informacja:</b> Pakiety X11 są już zainstalowane na Twoim systemie!\n"
                "Nie musisz niczego instalować. Wystarczy wylogować się i wybrać sesję X11 na ekranie logowania."
            )
            self.can_install = False
        else:
            pkgs = get_x11_installation_packages()
            self.status_msg = f"Gotowy do zainstalowania pakietów X11 dla {self.de_info['de']}: <b>{' '.join(pkgs)}</b>"

        lbl_status = Gtk.Label()
        lbl_status.set_markup(self.status_msg)
        lbl_status.set_wrap(True)
        lbl_status.set_halign(Gtk.Align.START)
        de_card.append(lbl_status)

        box.append(de_card)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.END)
        btn_box.set_margin_top(10)

        btn_cancel = Gtk.Button(label="Anuluj")
        btn_cancel.add_css_class("pill-action")
        btn_cancel.connect("clicked", lambda _: self.close())

        btn_confirm = Gtk.Button()
        btn_confirm.add_css_class("suggested-action")
        btn_confirm.add_css_class("pill-action")

        if self.can_install:
            btn_confirm.set_label("Zrozumiałem, zainstaluj X11")
            btn_confirm.connect("clicked", self._on_confirm_install)
        else:
            btn_confirm.set_label("Zamknij")
            btn_confirm.connect("clicked", lambda _: self.close())

        btn_box.append(btn_cancel)
        btn_box.append(btn_confirm)

        box.append(btn_box)

        clamp.set_child(box)
        toolbar_view.set_content(clamp)
        self.set_content(toolbar_view)

    def _on_confirm_install(self, button):
        self.close()
        pkgs = get_x11_installation_packages()
        cmd = ["pacman", "-S", "--needed", "--noconfirm"] + pkgs

        manager = get_sudo_manager()

        def _on_out(line, tag):
            self.run_cmd_cb(line, tag)

        def _on_fin(code):
            if code == 0:
                self.show_toast_cb("Instalacja X11 zakończona! Wyloguj się, aby wybrać sesję X11.")
            else:
                self.show_toast_cb("Instalacja X11 zakończyła się niepowodzeniem.")

        manager.run_privileged_async(cmd, _on_out, _on_fin)
