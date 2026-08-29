import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.widgets.icons import load_icon
from arc_hello.utils.system import (
    is_package_installed,
    install_package_with_fallback
)

class VtrtView(Gtk.Box):
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
        title.set_markup('<span size="x-large" weight="bold">Konfiguracja vtrt-manager (virt-manager)</span>')
        title.set_halign(Gtk.Align.START)

        desc = Gtk.Label()
        desc.set_markup(
            '<span size="medium" class="dim-label">'
            'vtrt-manager (virt-manager) automatycznie instaluje i konfiguruje środowisko wirtualizacji (KVM/QEMU, libvirt, dnsmasq).'
            '</span>'
        )
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)

        content.append(title)
        content.append(desc)

        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.add_css_class("app-card")

        icon = load_icon("system-run-symbolic", size=36)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_hexpand(True)

        lbl_card_title = Gtk.Label()
        lbl_card_title.set_markup("<b>Menedżer Wirtualizacji vtrt-manager / virt-manager</b>")
        lbl_card_title.set_halign(Gtk.Align.START)

        lbl_card_desc = Gtk.Label(
            label="Zainstaluj i skonfiguruj pełny zestaw pakietów vtrt-manager (virt-manager, qemu, libvirt)."
        )
        lbl_card_desc.set_halign(Gtk.Align.START)
        lbl_card_desc.add_css_class("dim-label")

        vbox.append(lbl_card_title)
        vbox.append(lbl_card_desc)

        installed = is_package_installed("vtrt-manager") or is_package_installed("virt-manager")

        self.btn_install = Gtk.Button()
        self.btn_install.add_css_class("suggested-action")
        self.btn_install.add_css_class("pill-action")

        if installed:
            self.btn_install.set_label("Zainstalowano / Zaktualizuj")
        else:
            self.btn_install.set_label("Ustaw vtrt-manager")

        self.btn_install.connect("clicked", self._on_install_clicked)

        card.append(icon)
        card.append(vbox)
        card.append(self.btn_install)

        content.append(card)

        clamp.set_child(content)
        self.append(clamp)

    def _on_install_clicked(self, button):
        button.set_sensitive(False)
        button.set_label("Instalowanie pakietów...")

        def _on_output(line, tag):
            self.run_cmd_cb(line, tag)

        def _on_finished(code):
            button.set_sensitive(True)
            if code == 0:
                button.set_label("vtrt-manager Gotowy")
                button.remove_css_class("suggested-action")
            else:
                button.set_label("Spróbuj ponownie")

        install_package_with_fallback("vtrt-manager", self.parent_window, _on_output, _on_finished)
