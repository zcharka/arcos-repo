import os
import shutil
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.widgets.icons import load_icon
from arc_hello.utils.system import (
    is_package_installed,
    install_package_with_fallback
)

class AppDetailsDialog(Adw.Window):
    """
    App Details window matching Linpama / Linexin Center widget presentation.
    Shows app icon, full description, metadata (package name, source, status),
    and a prominent action button to Install or Remove.
    """
    def __init__(self, parent_window, app_info: dict, run_cmd_cb, show_toast_cb):
        super().__init__(transient_for=parent_window, modal=True)
        self.set_title(f"Informacje: {app_info['name']}")
        self.set_default_size(580, 520)

        self.app_info = app_info
        self.run_cmd_cb = run_cmd_cb
        self.show_toast_cb = show_toast_cb
        self.pkg_name = app_info.get("package", app_info.get("id", ""))

        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()
        header.add_css_class("flat")
        toolbar_view.add_top_bar(header)

        clamp = Adw.Clamp(maximum_size=520)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        # App Hero Section: Icon & Title
        hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hero_box.set_halign(Gtk.Align.CENTER)

        icon_name = self.app_info.get("icon", "application-x-addon-symbolic")
        icon = load_icon(icon_name, size=64)
        icon.set_halign(Gtk.Align.CENTER)
        hero_box.append(icon)

        title = Gtk.Label()
        title.set_markup(f'<span size="x-large" weight="bold">{self.app_info["name"]}</span>')
        title.set_halign(Gtk.Align.CENTER)
        hero_box.append(title)

        cat_name = self.app_info.get("category", "Ogólne / Pakiety ArcOS")
        badge = Gtk.Label(label=cat_name)
        badge.add_css_class("linexin-new-badge")
        badge.set_halign(Gtk.Align.CENTER)
        hero_box.append(badge)

        box.append(hero_card := Gtk.Box(orientation=Gtk.Orientation.VERTICAL))
        hero_card.add_css_class("highlight-section")
        hero_card.append(hero_box)

        # Full Description Card
        desc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        desc_card.add_css_class("app-card")

        lbl_desc_heading = Gtk.Label()
        lbl_desc_heading.set_markup("<b>Opis programu:</b>")
        lbl_desc_heading.set_halign(Gtk.Align.START)

        lbl_full_desc = Gtk.Label(label=self.app_info.get("description", "Brak opisu."))
        lbl_full_desc.set_wrap(True)
        lbl_full_desc.set_halign(Gtk.Align.START)
        lbl_full_desc.add_css_class("dim-label")

        desc_card.append(lbl_desc_heading)
        desc_card.append(lbl_full_desc)
        box.append(desc_card)

        # Package Details Box (Linpama style metadata)
        meta_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        meta_card.add_css_class("app-card")

        installed = is_package_installed(self.pkg_name)
        status_text = "<span foreground='#57e389'>Zainstalowany w systemie</span>" if installed else "<span foreground='#f6d32d'>Niezainstalowany</span>"
        source_text = "Plik FlatpakRef (.flatpakref)" if self.pkg_name == "ogulniega" else "Repozytorium ArcOS / Pacman / Flatpak"

        lbl_meta = Gtk.Label()
        lbl_meta.set_markup(
            f"Nazwa pakietu: <b>{self.pkg_name}</b>\n"
            f"Źródło instalacji: <b>{source_text}</b>\n"
            f"Status: <b>{status_text}</b>"
        )
        lbl_meta.set_halign(Gtk.Align.START)
        meta_card.append(lbl_meta)
        box.append(meta_card)

        # Action Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.END)
        btn_box.set_margin_top(12)

        btn_close = Gtk.Button(label="Zamknij")
        btn_close.add_css_class("linexin-card-action")
        btn_close.connect("clicked", lambda _: self.close())

        self.btn_action = Gtk.Button()
        self.btn_action.add_css_class("linexin-card-action")

        if installed:
            self.btn_action.set_label("Zainstalowano")
            self.btn_action.set_sensitive(False)
        else:
            self.btn_action.set_label("Zainstaluj")
            self.btn_action.add_css_class("suggested-action")
            self.btn_action.connect("clicked", self._on_install_clicked)

        btn_box.append(btn_close)
        btn_box.append(self.btn_action)
        box.append(btn_box)

        clamp.set_child(box)
        toolbar_view.set_content(clamp)
        self.set_content(toolbar_view)

    def _on_install_clicked(self, button):
        self.btn_action.set_sensitive(False)
        self.btn_action.set_label("Instalacja...")

        def _on_output(line, tag):
            self.run_cmd_cb(line, tag)

        def _on_finished(code):
            if code == 0:
                self.btn_action.set_label("Zainstalowano")
                self.btn_action.remove_css_class("suggested-action")
                self.show_toast_cb(f"Pomyślnie zainstalowano {self.app_info['name']}.")
            else:
                self.btn_action.set_sensitive(True)
                self.btn_action.set_label("Spróbuj ponownie")
                self.show_toast_cb("Błąd instalacji pakietu.")

        install_package_with_fallback(self.pkg_name, self, _on_output, _on_finished)
