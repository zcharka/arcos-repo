import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.widgets.icons import load_icon
from arc_hello.utils.system import (
    get_steam_big_picture_setting,
    set_steam_big_picture_setting,
    is_package_installed,
    install_package_with_fallback
)

class SteamView(Gtk.Box):
    def __init__(self, parent_window, run_cmd_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self.parent_window = parent_window
        self.run_cmd_cb = run_cmd_cb
        self._build_ui()

    def _build_ui(self):
        clamp = Adw.Clamp(maximum_size=750)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Ustawienia Steam i Gier</span>')
        title.set_halign(Gtk.Align.START)

        desc = Gtk.Label()
        desc.set_markup('<span size="medium" class="dim-label">Zarządzaj opcjami uruchamiania Steam oraz zainstaluj narzędzia optymalizacyjne.</span>')
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)

        content.append(title)
        content.append(desc)

        bp_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        bp_card.add_css_class("app-card")
        bp_card.set_valign(Gtk.Align.CENTER)

        icon_bp = load_icon("input-gaming-symbolic", size=32)

        vbox_bp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox_bp.set_hexpand(True)

        lbl_bp_title = Gtk.Label()
        lbl_bp_title.set_markup("<b>Tryb Steam Big Picture przy uruchomieniu</b>")
        lbl_bp_title.set_halign(Gtk.Align.START)

        lbl_bp_desc = Gtk.Label(label="Włącz lub wyłącz automatyczne uruchamianie Steam w trybie Big Picture.")
        lbl_bp_desc.set_halign(Gtk.Align.START)
        lbl_bp_desc.add_css_class("dim-label")

        vbox_bp.append(lbl_bp_title)
        vbox_bp.append(lbl_bp_desc)

        self.switch_bp = Gtk.Switch()
        self.switch_bp.set_valign(Gtk.Align.CENTER)
        self.switch_bp.set_active(get_steam_big_picture_setting())
        self.switch_bp.connect("state-set", self._on_bp_toggled)

        bp_card.append(icon_bp)
        bp_card.append(vbox_bp)
        bp_card.append(self.switch_bp)

        content.append(bp_card)

        content.append(self._create_pkg_card(
            "gamemode",
            "Feral GameMode",
            "Optymalizuje wydajność procesora i GPU podczas grania.",
            "speedometer-symbolic"
        ))

        content.append(self._create_pkg_card(
            "gamescope",
            "Gamescope (Micro-compositor)",
            "Narzędzie Valve do skalowania i zarządzania oknami gier.",
            "video-display-symbolic"
        ))

        clamp.set_child(content)
        self.append(clamp)

    def _on_bp_toggled(self, switch, state):
        set_steam_big_picture_setting(state)
        return False

    def _create_pkg_card(self, pkg_name: str, display_name: str, description: str, icon_name: str) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.add_css_class("app-card")

        icon = load_icon(icon_name, size=32)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_hexpand(True)

        lbl_title = Gtk.Label()
        lbl_title.set_markup(f"<b>{display_name}</b>")
        lbl_title.set_halign(Gtk.Align.START)

        lbl_desc = Gtk.Label(label=description)
        lbl_desc.set_halign(Gtk.Align.START)
        lbl_desc.add_css_class("dim-label")

        vbox.append(lbl_title)
        vbox.append(lbl_desc)

        installed = is_package_installed(pkg_name)

        btn = Gtk.Button()
        if installed:
            btn.set_label("Zainstalowano")
            btn.set_sensitive(False)
            btn.add_css_class("pill-action")
        else:
            btn.set_label(f"Zainstaluj {pkg_name}")
            btn.add_css_class("suggested-action")
            btn.add_css_class("pill-action")
            btn.connect("clicked", lambda _: self._install_pkg(pkg_name, btn))

        card.append(icon)
        card.append(vbox)
        card.append(btn)

        return card

    def _install_pkg(self, pkg_name: str, button: Gtk.Button):
        button.set_sensitive(False)
        button.set_label("Instalacja...")

        def _on_output(line, tag):
            self.run_cmd_cb(line, tag)

        def _on_finished(code):
            if code == 0:
                button.set_label("Zainstalowano")
                button.remove_css_class("suggested-action")
            else:
                button.set_sensitive(True)
                button.set_label(f"Zainstaluj {pkg_name}")

        install_package_with_fallback(pkg_name, self.parent_window, _on_output, _on_finished)
