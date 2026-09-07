import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from arc_hello.utils.autostart import is_autostart_enabled, set_autostart_enabled, ensure_autostart_default
from arc_hello.utils.installer import ensure_installed
from arc_hello.utils.system import (
    get_szczur_logo_path,
    install_package_with_fallback,
    uninstall_package_with_fallback
)
from arc_hello.widgets.icons import load_icon

from arc_hello.views.welcome_view import WelcomeView
from arc_hello.views.app_details_view import AppDetailsView
from arc_hello.views.changelog_view import ChangelogView
from arc_hello.views.progress_view import ProgressView
from arc_hello.views.x11_dialog import X11InstallerDialog
from arc_hello.views.settings_view import SettingsView
from arc_hello.views.x11_manager_view import X11ManagerView

class ArcHelloWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Arc Hello")
        self.set_default_size(1080, 740)

        # Set default window icon for taskbar / compositor
        Gtk.Window.set_default_icon_name("org.arcos.ArcHello")
        self.set_icon_name("org.arcos.ArcHello")

        # Ensure autostart is enabled automatically by default on startup
        ensure_autostart_default()

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        self._build_ui()

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

        # Flat HeaderBar matching Linexin / Arc Store style
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

        # Settings Button
        btn_settings = Gtk.Button.new_from_icon_name("preferences-system-symbolic")
        btn_settings.set_tooltip_text("Ustawienia")
        btn_settings.connect("clicked", self._open_settings_view)
        header.pack_start(btn_settings)

        # Info Button
        btn_info = Gtk.Button.new_from_icon_name("help-about-symbolic")
        btn_info.set_tooltip_text("O programie Arc Hello")
        btn_info.connect("clicked", self._show_about_dialog)
        header.pack_start(btn_info)

        toolbar_view.add_top_bar(header)

        # Main Stack for Full-Page View Transitions (matching Arc Store)
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_stack.set_transition_duration(300)

        # 1. Main Welcome Dashboard
        self.welcome_view = WelcomeView(
            parent_window=self,
            run_cmd_cb=self.log_output,
            open_changelog_cb=self.open_changelog,
            open_x11_cb=self._open_x11_manager_view,
            show_toast_cb=self.show_toast,
            open_app_details_cb=self.open_app_details,
            start_install_cb=self.start_installation
        )
        self.main_stack.add_named(self.welcome_view, "main")

        # 2. App Details View
        self.app_details_view = AppDetailsView(
            parent_window=self,
            back_cb=self.go_back,
            start_install_cb=self.start_installation,
            start_uninstall_cb=self.start_uninstallation,
            show_toast_cb=self.show_toast
        )
        self.main_stack.add_named(self.app_details_view, "app_details")

        # 3. Changelog View
        self.changelog_view = ChangelogView(
            parent_window=self,
            back_cb=self.go_back
        )
        self.main_stack.add_named(self.changelog_view, "changelog")

        # 4. Progress View
        self.progress_view = ProgressView(
            parent_window=self,
            back_cb=self.go_back
        )
        self.main_stack.add_named(self.progress_view, "progress")

        # 5. X11 Manager View
        self.x11_manager_view = X11ManagerView(
            parent_window=self,
            back_cb=self.go_back,
            start_install_cb=self._do_start_installation,
            start_uninstall_cb=self.start_uninstallation
        )
        self.main_stack.add_named(self.x11_manager_view, "x11_manager")

        # 6. Settings View
        self.settings_view = SettingsView(
            parent_window=self,
            back_cb=self.go_back,
            open_about_cb=lambda: self._show_about_dialog(None)
        )
        self.main_stack.add_named(self.settings_view, "settings")

        self.main_stack.set_visible_child_name("main")

        toolbar_view.set_content(self.main_stack)
        self.toast_overlay.set_child(toolbar_view)

    def _on_autostart_toggled(self, switch, state):
        set_autostart_enabled(state)
        msg = "Włączono autostart Arc Hello" if state else "Wyłączono autostart Arc Hello"
        self.show_toast(msg)
        return False

    def open_app_details(self, app_info: dict):
        self.app_details_view.load_app(app_info)
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.main_stack.set_visible_child_name("app_details")

    def open_changelog(self):
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.main_stack.set_visible_child_name("changelog")

    def go_back(self):
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        self.main_stack.set_visible_child_name("main")

    def _open_x11_manager_view(self):
        self.x11_manager_view.refresh_state()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.main_stack.set_visible_child_name("x11_manager")

    def _open_settings_view(self, button=None):
        self.settings_view.refresh_state()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.main_stack.set_visible_child_name("settings")

    def start_installation(self, pkg_name: str, app_name: str):
        self._do_start_installation(pkg_name, app_name)

    def _do_start_installation(self, pkg_name: str, app_name: str):
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.main_stack.set_visible_child_name("progress")
        self.progress_view.start_install(app_name)

        def _on_output(line, tag):
            self.progress_view.log_output(line, tag)

        def _on_finished(code):
            self.progress_view.finish_install(code, app_name)
            if code == 0:
                self.show_toast(f"Pomyślnie zainstalowano {app_name}!")
                # Odśwież stan X11 managera, jeśli to instalacja X11
                if pkg_name == "x11":
                    self.x11_manager_view.refresh_state()
            elif code == -1:
                self.show_toast("Anulowano instalację.")
            else:
                self.show_toast(f"Błąd podczas instalacji {app_name}.")

        install_package_with_fallback(pkg_name, self, _on_output, _on_finished)

    def start_uninstallation(self, pkg_name: str, app_name: str):
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.main_stack.set_visible_child_name("progress")
        self.progress_view.start_install(f"odinstalowywanie {app_name}")

        def _on_output(line, tag):
            self.progress_view.log_output(line, tag)

        def _on_finished(code):
            self.progress_view.finish_install(code, app_name)
            if code == 0:
                self.show_toast(f"Pomyślnie odinstalowano {app_name}!")
                if pkg_name == "x11":
                    self.x11_manager_view.refresh_state()
            elif code == -1:
                self.show_toast("Anulowano odinstalowywanie.")
            else:
                self.show_toast(f"Błąd podczas odinstalowywania {app_name}.")

        uninstall_package_with_fallback(pkg_name, self, _on_output, _on_finished)

    def log_output(self, text: str, tag_name: str = "info"):
        self.progress_view.log_output(text, tag_name)

    def open_x11_dialog(self):
        dialog = X11InstallerDialog(
            parent_window=self,
            run_cmd_cb=self.log_output,
            show_toast_cb=self.show_toast
        )
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
