import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from arc_hello.widgets.icons import load_icon

class ProgressView(Gtk.Box):
    """
    Installation Progress view matching Arc Store layout.
    Shows title, progress bar, status, 'Pokaż szczegóły' expander button, console log, and action buttons.
    """
    def __init__(self, parent_window, back_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.parent_window = parent_window
        self.back_cb = back_cb
        self.is_running = False

        self._build_ui()

    def _build_ui(self):
        # Header bar with back button
        header_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_bar.add_css_class("flat")
        header_bar.set_margin_top(12)
        header_bar.set_margin_bottom(12)
        header_bar.set_margin_start(16)
        header_bar.set_margin_end(16)

        self.btn_back = Gtk.Button()
        self.btn_back.add_css_class("flat")
        self.btn_back.add_css_class("pill-action")

        back_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        back_icon = Gtk.Image.new_from_icon_name("go-previous-symbolic")
        self.lbl_back = Gtk.Label(label="Powrót")
        self.lbl_back.add_css_class("heading")

        back_content.append(back_icon)
        back_content.append(self.lbl_back)
        self.btn_back.set_child(back_content)
        self.btn_back.connect("clicked", lambda _: self.back_cb())

        header_bar.append(self.btn_back)
        self.append(header_bar)

        # Scrolled Window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        clamp = Adw.Clamp(maximum_size=780)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(30)
        content_box.set_margin_bottom(30)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)

        # Main Progress Section (Matching Arc Store Screenshot 2)
        self.lbl_title = Gtk.Label()
        self.lbl_title.set_markup('<span size="x-large" weight="bold">Instalowanie pakietu...</span>')
        self.lbl_title.set_halign(Gtk.Align.START)
        content_box.append(self.lbl_title)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_hexpand(True)
        self.progress_bar.set_margin_top(8)
        self.progress_bar.set_margin_bottom(8)
        content_box.append(self.progress_bar)

        self.lbl_status = Gtk.Label(label="Instalowanie pakietu...")
        self.lbl_status.add_css_class("dim-label")
        self.lbl_status.set_halign(Gtk.Align.START)
        content_box.append(self.lbl_status)

        # 'Pokaż konsolę' Centered Expander Button
        self.btn_toggle_console = Gtk.Button(label="Pokaż konsolę")
        self.btn_toggle_console.add_css_class("flat")
        self.btn_toggle_console.add_css_class("heading")
        self.btn_toggle_console.set_halign(Gtk.Align.CENTER)
        self.btn_toggle_console.set_margin_top(16)
        self.btn_toggle_console.set_margin_bottom(8)
        self.btn_toggle_console.connect("clicked", self._on_toggle_console)
        content_box.append(self.btn_toggle_console)

        # Log Revealer
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.revealer.set_transition_duration(200)

        console_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        console_card.add_css_class("app-card")

        console_scroll = Gtk.ScrolledWindow()
        console_scroll.set_size_request(-1, 260)

        self.console_view = Gtk.TextView()
        self.console_view.set_editable(False)
        self.console_view.set_monospace(True)
        self.console_view.add_css_class("console")
        self.text_buffer = self.console_view.get_buffer()

        console_scroll.set_child(self.console_view)
        console_card.append(console_scroll)
        self.revealer.set_child(console_card)

        content_box.append(self.revealer)

        # Action Buttons Row (Matching Arc Store Screenshot 2)
        btn_action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        btn_action_box.set_halign(Gtk.Align.CENTER)
        btn_action_box.set_margin_top(16)

        self.btn_done = Gtk.Button(label="Powrót do aplikacji")
        self.btn_done.add_css_class("linexin-card-action")
        self.btn_done.connect("clicked", lambda _: self.back_cb())

        btn_action_box.append(self.btn_done)
        content_box.append(btn_action_box)

        clamp.set_child(content_box)
        scrolled.set_child(clamp)
        self.append(scrolled)

        self._setup_text_tags()

    def _setup_text_tags(self):
        self.tag_cmd = self.text_buffer.create_tag("cmd", foreground="#62a0ea", weight=700)
        self.tag_success = self.text_buffer.create_tag("success", foreground="#57e389", weight=700)
        self.tag_error = self.text_buffer.create_tag("error", foreground="#ff7b63", weight=700)
        self.tag_info = self.text_buffer.create_tag("info", foreground="#f6d32d")

    def _on_toggle_console(self, btn):
        revealed = not self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(revealed)
        self.btn_toggle_console.set_label("Ukryj konsolę" if revealed else "Pokaż konsolę")

    def start_install(self, app_name: str):
        self.is_running = True
        self.btn_back.set_sensitive(False)
        self.btn_done.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.pulse()

        self.lbl_title.set_markup(f'<span size="x-large" weight="bold">Instalowanie {app_name}...</span>')
        self.lbl_status.set_label("Instalowanie pakietu...")

        self.text_buffer.set_text("")
        self.log_output(f" Rozpoczęto instalację {app_name}...\n", "info")

    def log_output(self, text: str, tag_name: str = "info"):
        def _gui_update():
            tag = getattr(self, f"tag_{tag_name}", None)
            end_iter = self.text_buffer.get_end_iter()
            if tag:
                self.text_buffer.insert_with_tags(end_iter, text, tag)
            else:
                self.text_buffer.insert(end_iter, text)
            mark = self.text_buffer.create_mark(None, self.text_buffer.get_end_iter(), False)
            self.console_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
            if self.is_running:
                self.progress_bar.pulse()
        GLib.idle_add(_gui_update)

    def finish_install(self, code: int, app_name: str):
        def _gui_update():
            self.is_running = False
            self.btn_back.set_sensitive(True)
            self.btn_done.set_sensitive(True)

            if code == 0:
                self.progress_bar.set_fraction(1.0)
                self.lbl_title.set_markup(f'<span size="x-large" weight="bold" foreground="#57e389">Zainstalowano {app_name}!</span>')
                self.lbl_status.set_label("Instalacja zakończona sukcesem.")
            elif code == -1:
                self.progress_bar.set_fraction(0.0)
                self.lbl_title.set_markup(f'<span size="x-large" weight="bold" foreground="#f6d32d">Przerwano instalację {app_name}</span>')
                self.lbl_status.set_label("Wymagane uwierzytelnienie zostało anulowane lub operacja została przerwana.")
            else:
                self.progress_bar.set_fraction(0.0)
                self.lbl_title.set_markup(f'<span size="x-large" weight="bold" foreground="#ff7b63">Błąd instalacji {app_name}</span>')
                self.lbl_status.set_label("Wystąpił błąd podczas instalacji. Zobacz logi w szczegółach.")
                if not self.revealer.get_reveal_child():
                    self._on_toggle_console(None)

        GLib.idle_add(_gui_update)
