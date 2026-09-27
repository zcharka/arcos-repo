import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.utils.system import (
    APP_CATEGORIES,
    get_installed_desktop_files,
    get_current_default_app,
    set_default_app_for_mimes
)

class DefaultsView(Gtk.Box):
    def __init__(self, show_toast_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self.show_toast_cb = show_toast_cb
        self.apps = get_installed_desktop_files()
        self.selected_category = list(APP_CATEGORIES.keys())[0]

        self._build_ui()

    def _build_ui(self):
        clamp = Adw.Clamp(maximum_size=750)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Ustawianie Domyślnych Programów</span>')
        title.set_halign(Gtk.Align.START)

        desc = Gtk.Label()
        desc.set_markup(
            '<span size="medium" class="dim-label">'
            'Wybierz kategorię lub aplikację i kliknij "Ustaw domyślne", aby przypisać skojarzenia plików.'
            '</span>'
        )
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)

        content.append(title)
        content.append(desc)

        cat_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        cat_card.add_css_class("app-card")

        cat_title = Gtk.Label()
        cat_title.set_markup("<b>Kategorie Domyślnych Aplikacji</b>")
        cat_title.set_halign(Gtk.Align.START)
        cat_card.append(cat_title)

        cat_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_cat = Gtk.Label(label="Kategoria:")
        lbl_cat.set_halign(Gtk.Align.START)

        self.cat_dropdown = Gtk.DropDown.new_from_strings(list(APP_CATEGORIES.keys()))
        self.cat_dropdown.set_hexpand(True)
        self.cat_dropdown.connect("notify::selected", self._on_category_changed)

        cat_select_box.append(lbl_cat)
        cat_select_box.append(self.cat_dropdown)
        cat_card.append(cat_select_box)

        self.lbl_current_default = Gtk.Label()
        self.lbl_current_default.set_halign(Gtk.Align.START)
        self.lbl_current_default.set_wrap(True)
        cat_card.append(self.lbl_current_default)

        app_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_app = Gtk.Label(label="Aplikacja:")
        lbl_app.set_halign(Gtk.Align.START)

        app_names = [a["name"] for a in self.apps]
        self.app_dropdown = Gtk.DropDown.new_from_strings(app_names)
        self.app_dropdown.set_hexpand(True)

        app_select_box.append(lbl_app)
        app_select_box.append(self.app_dropdown)
        cat_card.append(app_select_box)

        self.btn_set_default = Gtk.Button(label="Ustaw domyślne")
        self.btn_set_default.add_css_class("suggested-action")
        self.btn_set_default.add_css_class("pill-action")
        self.btn_set_default.set_halign(Gtk.Align.END)
        self.btn_set_default.connect("clicked", self._on_set_default_clicked)

        cat_card.append(self.btn_set_default)
        content.append(cat_card)

        ext_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        ext_card.add_css_class("app-card")

        ext_title = Gtk.Label()
        ext_title.set_markup("<b>Przypisz Aplikację do Rozszerzenia / Typu MIME</b>")
        ext_title.set_halign(Gtk.Align.START)
        ext_card.append(ext_title)

        ext_input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_ext = Gtk.Label(label="Rozszerzenie lub typ MIME:")
        lbl_ext.set_halign(Gtk.Align.START)

        self.entry_ext = Gtk.Entry()
        self.entry_ext.set_placeholder_text("np. .pdf, .mkv lub video/mp4")
        self.entry_ext.set_hexpand(True)

        ext_input_box.append(lbl_ext)
        ext_input_box.append(self.entry_ext)
        ext_card.append(ext_input_box)

        ext_app_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_ext_app = Gtk.Label(label="Aplikacja docelowa:")
        lbl_ext_app.set_halign(Gtk.Align.START)

        self.ext_app_dropdown = Gtk.DropDown.new_from_strings(app_names)
        self.ext_app_dropdown.set_hexpand(True)

        ext_app_box.append(lbl_ext_app)
        ext_app_box.append(self.ext_app_dropdown)
        ext_card.append(ext_app_box)

        self.btn_set_ext = Gtk.Button(label="Przypisz rozszerzenie")
        self.btn_set_ext.add_css_class("suggested-action")
        self.btn_set_ext.add_css_class("pill-action")
        self.btn_set_ext.set_halign(Gtk.Align.END)
        self.btn_set_ext.connect("clicked", self._on_set_custom_ext_clicked)

        ext_card.append(self.btn_set_ext)
        content.append(ext_card)

        clamp.set_child(content)
        self.append(clamp)

        self._update_category_info()

    def _on_category_changed(self, dropdown, pspec):
        idx = dropdown.get_selected()
        cats = list(APP_CATEGORIES.keys())
        if 0 <= idx < len(cats):
            self.selected_category = cats[idx]
            self._update_category_info()

    def _update_category_info(self):
        cat_info = APP_CATEGORIES.get(self.selected_category, {})
        mimes = cat_info.get("mimes", [])
        if mimes:
            curr = get_current_default_app(mimes[0])
            self.lbl_current_default.set_markup(
                f'<span size="small" class="dim-label">Obecna aplikacja domyślna: <b>{curr}</b></span>'
            )
        else:
            self.lbl_current_default.set_text("")

    def _on_set_default_clicked(self, button):
        app_idx = self.app_dropdown.get_selected()
        if 0 <= app_idx < len(self.apps):
            app = self.apps[app_idx]
            desktop_file = app["desktop_file"]
            mimes = APP_CATEGORIES[self.selected_category]["mimes"]

            ok = set_default_app_for_mimes(desktop_file, mimes)
            if ok:
                self.show_toast_cb(f"Ustawiono '{app['name']}' jako domyślną dla '{self.selected_category}'.")
                self._update_category_info()
            else:
                self.show_toast_cb(f"Błąd podczas ustawiania domyślnej aplikacji.")

    def _on_set_custom_ext_clicked(self, button):
        ext = self.entry_ext.get_text().strip().lower()
        if not ext:
            self.show_toast_cb("Wprowadź rozszerzenie pliku (np. .pdf) lub typ MIME.")
            return

        mime_type = ext
        if ext.startswith("."):
            ext_map = {
                ".pdf": "application/pdf",
                ".zip": "application/zip",
                ".txt": "text/plain",
                ".mp4": "video/mp4",
                ".mkv": "video/x-matroska",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".mp3": "audio/mpeg"
            }
            mime_type = ext_map.get(ext, f"application/x-{ext[1:]}")

        app_idx = self.ext_app_dropdown.get_selected()
        if 0 <= app_idx < len(self.apps):
            app = self.apps[app_idx]
            desktop_file = app["desktop_file"]

            ok = set_default_app_for_mimes(desktop_file, [mime_type])
            if ok:
                self.show_toast_cb(f"Przypisano '{ext}' ({mime_type}) do aplikacji '{app['name']}'.")
            else:
                self.show_toast_cb(f"Nie udało się przypisać rozszerzenia.")
