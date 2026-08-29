import gi
import shutil
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.widgets.icons import load_icon
from arc_hello.utils.system import (
    is_package_installed,
    install_package_with_fallback
)

GENERAL_APPS = [
    {
        "id": "blockbench",
        "name": "Blockbench",
        "desc": "Edytor modeli 3D i pikselartu dla Minecraft i gier 3D.",
        "icon": "applications-games-symbolic",
        "pkg": "blockbench"
    },
    {
        "id": "blender",
        "name": "Blender",
        "desc": "Zaawansowany pakiet do tworzenia grafiki i animacji 3D.",
        "icon": "applications-graphics-symbolic",
        "pkg": "blender"
    },
    {
        "id": "opera",
        "name": "Opera Browser",
        "desc": "Przeglądarka internetowa z wbudowanym VPN i blokerem reklam.",
        "icon": "web-browser-symbolic",
        "pkg": "opera"
    },
    {
        "id": "sober",
        "name": "Sober",
        "desc": "Środowisko uruchomieniowe do gier na Linuksie.",
        "icon": "input-gaming-symbolic",
        "pkg": "sober"
    }
]

class AppsView(Gtk.Box):
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
        title.set_markup('<span size="x-large" weight="bold">Zainstaluj Aplikacje</span>')
        title.set_halign(Gtk.Align.START)
        content.append(title)

        sec_gen = Gtk.Label()
        sec_gen.set_markup('<span size="medium" weight="bold">Ogólne</span>')
        sec_gen.set_halign(Gtk.Align.START)
        content.append(sec_gen)

        for app in GENERAL_APPS:
            card = self._create_app_card(app)
            content.append(card)

        sec_adv = Gtk.Label()
        sec_adv.set_markup('<span size="medium" weight="bold">Zaawansowane</span>')
        sec_adv.set_halign(Gtk.Align.START)
        sec_adv.set_margin_top(12)
        content.append(sec_adv)

        arc_store_card = self._create_arc_store_card()
        content.append(arc_store_card)

        clamp.set_child(content)
        self.append(clamp)

    def _create_app_card(self, app_info: dict) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.add_css_class("app-card")

        icon = load_icon(app_info["icon"], size=32)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_hexpand(True)

        lbl_name = Gtk.Label()
        lbl_name.set_markup(f"<b>{app_info['name']}</b>")
        lbl_name.set_halign(Gtk.Align.START)

        lbl_desc = Gtk.Label(label=app_info["desc"])
        lbl_desc.set_halign(Gtk.Align.START)
        lbl_desc.add_css_class("dim-label")

        vbox.append(lbl_name)
        vbox.append(lbl_desc)

        installed = is_package_installed(app_info["pkg"])

        btn = Gtk.Button()
        if installed:
            btn.set_label("Zainstalowano")
            btn.set_sensitive(False)
            btn.add_css_class("pill-action")
        else:
            btn.set_label("Zainstaluj")
            btn.add_css_class("suggested-action")
            btn.add_css_class("pill-action")
            btn.connect("clicked", lambda _: self._install_app(app_info["pkg"], btn))

        card.append(icon)
        card.append(vbox)
        card.append(btn)

        return card

    def _create_arc_store_card(self) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.add_css_class("app-card")

        icon = load_icon("software-store-symbolic", size=32)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_hexpand(True)

        lbl_name = Gtk.Label()
        lbl_name.set_markup("<b>Arc Store</b>")
        lbl_name.set_halign(Gtk.Align.START)

        lbl_desc = Gtk.Label(label="Oficjalne centrum oprogramowania dla systemów ArcOS.")
        lbl_desc.set_halign(Gtk.Align.START)
        lbl_desc.add_css_class("dim-label")

        vbox.append(lbl_name)
        vbox.append(lbl_desc)

        btn = Gtk.Button(label="Uruchom Arc Store")
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill-action")
        btn.connect("clicked", lambda _: self.launch_arc_store(btn))

        card.append(icon)
        card.append(vbox)
        card.append(btn)

        return card

    def launch_arc_store(self, btn: Gtk.Button):
        binary = "arc-store"
        if shutil.which("arc-store-gui"):
            binary = "arc-store-gui"

        if shutil.which(binary):
            import subprocess
            subprocess.Popen([binary])
        else:
            btn.set_sensitive(False)
            btn.set_label("Instalowanie...")
            def _on_output(line, tag):
                self.run_cmd_cb(line, tag)
            def _on_finished(code):
                btn.set_sensitive(True)
                if code == 0:
                    btn.set_label("Uruchom Arc Store")
                else:
                    btn.set_label("Zainstaluj Arc Store")

            install_package_with_fallback("arc-store", self.parent_window, _on_output, _on_finished)

    def _install_app(self, pkg_name: str, button: Gtk.Button):
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
                button.set_label("Zainstaluj")

        install_package_with_fallback(pkg_name, self.parent_window, _on_output, _on_finished)
