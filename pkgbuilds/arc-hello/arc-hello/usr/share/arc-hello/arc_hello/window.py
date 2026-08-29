import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from arc_hello.utils.autostart import is_autostart_enabled, set_autostart_enabled, ensure_autostart_default
from arc_hello.utils.installer import ensure_installed
from arc_hello.utils.system import get_szczur_logo_path
from arc_hello.widgets.icons import load_icon

from arc_hello.views.welcome_view import WelcomeView
from arc_hello.views.x11_dialog import X11InstallerDialog
from arc_hello.views.changelog_dialog import ChangelogDialog

class ArcHelloWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Arc Hello")
        self.set_default_size(1080, 740)

        # Ensure autostart is enabled automatically by default on startup
        ensure_autostart_default()

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        self._build_ui()
        self._setup_text_tags()

        # Trigger self-copy check deferred after window is presented
        GLib.idle_add(self._check_self_installation)

    def _check_self_installation(self):
        def _on_done(success):
            if success:
                print("Arc Hello verified in system directory.")
        ensure_installed(self, _on_done)
        return False

    def show_toast(self, message: str):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()

        # Flat HeaderBar matching Linexin style
        header = Adw.HeaderBar()
        header.add_css_class("flat")

        title_widget = Adw.WindowTitle(title="Arc Hello", subtitle="ArcOS rolling")
        header.set_title_widget(title_widget)

        # Autostart Toggle Switch in Header
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        autostart_box.add_css_class("header-autostart-box")
        autostart_box.set_valign(Gtk.Align.CENTER)

        lbl_autostart = Gtk.Label(label="Uruchamiaj przy starcie")
        lbl_autostart.add_css_class("header-autostart-label")

        switch_autostart = Gtk.Switch()
        switch_autostart.set_valign(Gtk.Align.CENTER)
        switch_autostart.set_active(is_autostart_enabled())
        switch_autostart.connect("state-set", self._on_autostart_toggled)

        autostart_box.append(lbl_autostart)
        autostart_box.append(switch_autostart)

        header.pack_end(autostart_box)

        # Info Button
        btn_info = Gtk.Button.new_from_icon_name("help-about-symbolic")
        btn_info.set_tooltip_text("O programie Arc Hello")
        btn_info.connect("clicked", self._show_about_dialog)
        header.pack_start(btn_info)

        toolbar_view.add_top_bar(header)

        # WelcomeView (Main 2-Column Dashboard Layout)
        self.welcome_view = WelcomeView(
            parent_window=self,
            run_cmd_cb=self.log_output,
            open_changelog_cb=self.open_changelog_dialog,
            open_x11_cb=self.open_x11_dialog,
            show_toast_cb=self.show_toast
        )
        self.welcome_view.set_vexpand(True)
        self.welcome_view.set_hexpand(True)

        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        bottom_box.set_vexpand(True)
        bottom_box.set_hexpand(True)
        bottom_box.append(self.welcome_view)

        # Bottom Console Revealer Bar
        log_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        log_bar.set_margin_top(6)
        log_bar.set_margin_bottom(6)
        log_bar.set_margin_start(16)
        log_bar.set_margin_end(16)

        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(20, 20)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_hexpand(True)
        self.progress_bar.set_valign(Gtk.Align.CENTER)

        self.btn_toggle_log = Gtk.Button(label="Konsola instalacji")
        self.btn_toggle_log.add_css_class("linexin-card-action")
        self.btn_toggle_log.connect("clicked", self._on_toggle_log_clicked)

        log_bar.append(self.spinner)
        log_bar.append(self.progress_bar)
        log_bar.append(self.btn_toggle_log)

        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.revealer.set_transition_duration(250)

        console_scroll = Gtk.ScrolledWindow()
        console_scroll.set_size_request(-1, 160)

        self.console_view = Gtk.TextView()
        self.console_view.set_editable(False)
        self.console_view.set_monospace(True)
        self.console_view.add_css_class("console")
        self.text_buffer = self.console_view.get_buffer()

        console_scroll.set_child(self.console_view)
        self.revealer.set_child(console_scroll)

        bottom_box.append(log_bar)
        bottom_box.append(self.revealer)

        toolbar_view.set_content(bottom_box)
        self.toast_overlay.set_child(toolbar_view)

    def _on_autostart_toggled(self, switch, state):
        set_autostart_enabled(state)
        msg = "Włączono autostart Arc Hello" if state else "Wyłączono autostart Arc Hello"
        self.show_toast(msg)
        return False

    def _on_toggle_log_clicked(self, button):
        self.revealer.set_reveal_child(not self.revealer.get_reveal_child())

    def _setup_text_tags(self):
        self.tag_cmd = self.text_buffer.create_tag("cmd", foreground="#62a0ea", weight=700)
        self.tag_success = self.text_buffer.create_tag("success", foreground="#57e389", weight=700)
        self.tag_error = self.text_buffer.create_tag("error", foreground="#ff7b63", weight=700)
        self.tag_info = self.text_buffer.create_tag("info", foreground="#f6d32d")

    def log_output(self, text: str, tag_name: str = "info"):
        self.revealer.set_reveal_child(True)
        def _gui_update():
            tag = getattr(self, f"tag_{tag_name}", None)
            end_iter = self.text_buffer.get_end_iter()
            if tag:
                self.text_buffer.insert_with_tags(end_iter, text, tag)
            else:
                self.text_buffer.insert(end_iter, text)
            mark = self.text_buffer.create_mark(None, self.text_buffer.get_end_iter(), False)
            self.console_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

        GLib.idle_add(_gui_update)

    def open_x11_dialog(self):
        dialog = X11InstallerDialog(
            parent_window=self,
            run_cmd_cb=self.log_output,
            show_toast_cb=self.show_toast
        )
        dialog.present()

    def open_changelog_dialog(self):
        dialog = ChangelogDialog(parent_window=self)
        dialog.present()

    def _show_about_dialog(self, button):
        logo_path = get_szczur_logo_path()
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="Arc Hello",
            application_icon=logo_path if os.path.exists(logo_path) else "system-run-symbolic",
            developer_name="ArcOS Developers",
            version="1.0.0",
            website="https://zcharka.github.io/ArcOS/documentation",
            issue_url="https://github.com/zcharka/ArcOS/issues",
            copyright="© 2026 ArcOS Project",
            license_type=Gtk.License.GPL_3_0
        )
        about.present()
