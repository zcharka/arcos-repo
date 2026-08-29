import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.utils.changelog import (
    get_changelog_files,
    read_changelog_content
)

class ChangelogDialog(Adw.Window):
    def __init__(self, parent_window):
        super().__init__(transient_for=parent_window, modal=True)
        self.set_title("Historia zmian ArcOS (Changelog)")
        self.set_default_size(700, 520)

        self.changelog_files = get_changelog_files()
        self._build_ui()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_file = Gtk.Label(label="Wybierz wersję changelogu:")
        lbl_file.set_halign(Gtk.Align.START)
        lbl_file.set_markup("<b>Wybierz wersję changelogu:</b>")

        display_names = [item[0] for item in self.changelog_files]
        self.dropdown = Gtk.DropDown.new_from_strings(display_names)
        self.dropdown.set_hexpand(True)
        self.dropdown.connect("notify::selected", self._on_file_selected)

        select_box.append(lbl_file)
        select_box.append(self.dropdown)
        box.append(select_box)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.add_css_class("console")
        self.buffer = self.text_view.get_buffer()

        scroll.set_child(self.text_view)
        box.append(scroll)

        btn_close = Gtk.Button(label="Zamknij")
        btn_close.add_css_class("suggested-action")
        btn_close.add_css_class("pill-action")
        btn_close.set_halign(Gtk.Align.END)
        btn_close.connect("clicked", lambda _: self.close())
        box.append(btn_close)

        toolbar_view.set_content(box)
        self.set_content(toolbar_view)

        self._load_selected_file(0)

    def _on_file_selected(self, dropdown, pspec):
        idx = dropdown.get_selected()
        self._load_selected_file(idx)

    def _load_selected_file(self, index: int):
        if 0 <= index < len(self.changelog_files):
            display_name, fpath = self.changelog_files[index]
            content = read_changelog_content(fpath)
            self.buffer.set_text(content)
