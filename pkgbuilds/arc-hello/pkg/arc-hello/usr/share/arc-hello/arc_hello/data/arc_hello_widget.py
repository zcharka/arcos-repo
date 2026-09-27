import sys
import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

# Dodajemy głowny kod arc-hello do ścieżki
sys.path.insert(0, "/usr/share/arc-hello")

# Importujemy logikę widoków
from arc_hello.views.welcome_view import WelcomeView
from arc_hello.views.app_details_view import AppDetailsView
from arc_hello.views.changelog_view import ChangelogView
from arc_hello.views.progress_view import ProgressView
from arc_hello.views.x11_manager_view import X11ManagerView
from arc_hello.views.settings_view import SettingsView

class ArcHelloWidget(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        
        self.widgetname = "Arc Hello"
        self.widgeticon = "org.arcos.ArcHello"
        self.widget_id = "arc_hello"
        
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_stack.set_transition_duration(300)

        # Trzeba zasymulować "parent_window" z metodami `log_output`, itd. dla poszczególnych widoków.
        # W widgetach Linexin-Center można przechwycić to do lokalnych funkcji.
        class ParentMock:
            def log_output(self, *args):
                pass
            def close(self):
                # Widget nie zamyka okna, po prostu nic nie robi
                pass
        
        self.mock_parent = ParentMock()
        
        self.welcome_view = WelcomeView(
            parent_window=self.mock_parent,
            run_cmd_cb=self.mock_parent.log_output,
            open_changelog_cb=self.open_changelog,
            open_x11_cb=self.open_x11_manager,
            show_toast_cb=self.show_toast,
            open_app_details_cb=self.open_app_details,
            start_install_cb=self.start_install
        )
        
        # Pasek narzędziowy / Header
        toolbar = Adw.HeaderBar()
        toolbar.add_css_class("flat")
        title_widget = Adw.WindowTitle(title="Arc Hello", subtitle="ArcOS rolling")
        toolbar.set_title_widget(title_widget)
        
        btn_settings = Gtk.Button.new_from_icon_name("preferences-system-symbolic")
        btn_settings.set_tooltip_text("Ustawienia")
        btn_settings.connect("clicked", lambda _: self.open_settings())
        toolbar.pack_start(btn_settings)

        # Ustawiamy zawartość widgetu
        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrapper.append(toolbar)
        
        self.main_stack.add_named(self.welcome_view, "welcome")
        wrapper.append(self.main_stack)
        
        self.append(wrapper)

    def show_toast(self, msg):
        print(f"Arc Hello Widget: {msg}")

    def go_back_to_welcome(self):
        self.main_stack.set_visible_child_name("welcome")

    def open_changelog(self):
        cv = ChangelogView(self.mock_parent, self.go_back_to_welcome)
        self.main_stack.add_named(cv, "changelog")
        self.main_stack.set_visible_child_name("changelog")

    def open_x11_manager(self):
        x11_view = X11ManagerView(
            parent_window=self.mock_parent,
            back_cb=self.go_back_to_welcome,
            start_install_cb=self.start_install,
            start_uninstall_cb=self.start_uninstall
        )
        self.main_stack.add_named(x11_view, "x11")
        self.main_stack.set_visible_child_name("x11")

    def open_settings(self):
        settings = SettingsView(
            parent_window=self.mock_parent,
            back_cb=self.go_back_to_welcome,
            open_about_cb=self.open_about
        )
        self.main_stack.add_named(settings, "settings")
        self.main_stack.set_visible_child_name("settings")

    def open_about(self):
        about = Adw.AboutWindow(
            application_name="Arc Hello (Widget)",
            developer_name="ArcOS Developers",
            version="1.0"
        )
        about.present()

    def open_app_details(self, app_info):
        detail_view = AppDetailsView(
            parent_window=self.mock_parent,
            back_cb=self.go_back_to_welcome,
            app_info=app_info,
            start_install_cb=self.start_install
        )
        self.main_stack.add_named(detail_view, f"details_{app_info['name']}")
        self.main_stack.set_visible_child_name(f"details_{app_info['name']}")

    def start_install(self, pkg_key, display_name):
        pv = ProgressView(
            parent_window=self.mock_parent,
            back_cb=self.go_back_to_welcome,
            pkg_key=pkg_key,
            display_name=display_name,
            action="install"
        )
        self.main_stack.add_named(pv, f"install_{pkg_key}")
        self.main_stack.set_visible_child_name(f"install_{pkg_key}")
        pv.start()

    def start_uninstall(self, pkg_key, display_name):
        pv = ProgressView(
            parent_window=self.mock_parent,
            back_cb=self.go_back_to_welcome,
            pkg_key=pkg_key,
            display_name=display_name,
            action="uninstall"
        )
        self.main_stack.add_named(pv, f"uninstall_{pkg_key}")
        self.main_stack.set_visible_child_name(f"uninstall_{pkg_key}")
        pv.start()

def get_widget():
    return ArcHelloWidget()
