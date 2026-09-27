import os
import subprocess
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from arc_hello.auth.sudo_manager import get_sudo_manager

WIDGET_DEST = "/usr/share/arcos/widgets/arc_hello_widget.py"

class SettingsView(Gtk.Box):
    def __init__(self, parent_window, back_cb, open_about_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.parent_window = parent_window
        self.back_cb = back_cb
        self.open_about_cb = open_about_cb

        self._build_ui()
        self.refresh_state()

    def _build_ui(self):
        # ── Toolbar Header ──
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        
        btn_back = Gtk.Button()
        btn_back.set_icon_name("go-previous-symbolic")
        btn_back.add_css_class("flat")
        btn_back.add_css_class("circular")
        btn_back.set_tooltip_text("Wróć")
        btn_back.connect("clicked", lambda _: self.back_cb())
        toolbar.append(btn_back)
        
        title = Gtk.Label(label="Ustawienia")
        title.add_css_class("title-4")
        title.set_margin_start(6)
        toolbar.append(title)
        
        self.append(toolbar)
        self.append(Gtk.Separator())

        # ── Content ──
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        clamp = Adw.Clamp(maximum_size=820)
        page = Adw.PreferencesPage()

        # Group: Integracja
        group_integration = Adw.PreferencesGroup(title="Integracja z systemem", description="Zarządzaj w jaki sposób Arc Hello integruje się z systemem")
        
        self.arc_center_switch = Gtk.Switch()
        self.arc_center_switch.set_valign(Gtk.Align.CENTER)
        self.arc_center_switch.connect("notify::active", self._on_arc_center_toggled)

        self.arc_center_row = Adw.ActionRow(title="Przenieś do arc center", subtitle="Dodaje ten asystent jako wbudowany widżet w aplikacji Arc Center i ukrywa go z głównego menu systemu.")
        self.arc_center_row.add_suffix(self.arc_center_switch)
        group_integration.add(self.arc_center_row)

        page.add(group_integration)

        # Group: O programie
        group_about = Adw.PreferencesGroup(title="Informacje")
        
        about_row = Adw.ActionRow(title="Informacje o programie")
        about_row.set_activatable(True)
        icon_about = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        icon_about.set_valign(Gtk.Align.CENTER)
        about_row.add_suffix(icon_about)
        about_row.connect("activated", lambda _: self.open_about_cb())
        group_about.add(about_row)

        page.add(group_about)

        clamp.set_child(page)
        scrolled.set_child(clamp)
        self.append(scrolled)

    def refresh_state(self):
        # Sprawdzamy czy widżet istnieje w docelowym miejscu
        is_in_center = os.path.exists(WIDGET_DEST)
        self.arc_center_switch.set_state(is_in_center)

    def _on_arc_center_toggled(self, switch, gparam):
        is_active = switch.get_active()
        
        # Aby wykonać operację, potrzebujemy hasła
        manager = get_sudo_manager()
        if not manager.user_password:
            from arc_hello.auth.dialogs import prompt_password
            def on_success():
                self._execute_arc_center_toggle(is_active)
            def on_cancel():
                self.arc_center_switch.set_state(not is_active)
            
            prompt_password(self.parent_window, "Wymagane hasło do modyfikacji plików systemowych.", on_success, on_cancel=on_cancel)
            return

        
        self._execute_arc_center_toggle(is_active)

    def _execute_arc_center_toggle(self, is_active):
        manager = get_sudo_manager()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Z /usr/share/arc-hello/arc_hello/views -> /usr/share/arc-hello/arc_hello/data/arc_hello_widget.py
        # Ale pliku arc_hello_widget.py jeszcze nie ma. Musimy go napisać do systemu.
        source_widget = os.path.abspath(os.path.join(base_dir, "..", "data", "arc_hello_widget.py"))
        
        desktop_file_user = os.path.expanduser("~/.local/share/applications/arc-hello.desktop")
        desktop_file_system = "/usr/share/applications/arc-hello.desktop"

        if is_active:
            # Tworzymy katalog jeśli nie istnieje
            manager.run_privileged(["mkdir", "-p", os.path.dirname(WIDGET_DEST)])
            manager.run_privileged(["cp", source_widget, WIDGET_DEST])
            manager.run_privileged(["chmod", "644", WIDGET_DEST])
            
            # Ukrywamy .desktop uzytkownika kopiujac systemowy i dodajac NoDisplay=true
            if not os.path.exists(os.path.dirname(desktop_file_user)):
                os.makedirs(os.path.dirname(desktop_file_user))
            
            if os.path.exists(desktop_file_system):
                with open(desktop_file_system, "r") as f:
                    content = f.read()
                if "NoDisplay=true" not in content:
                    content += "\nNoDisplay=true\n"
                with open(desktop_file_user, "w") as f:
                    f.write(content)
            
            # Pokazujemy dialog
            self._show_info_dialog("Zakończono", "Program został przeniesiony do Arc Center. Ten program zostanie teraz zamknięty.", self._on_close_and_open_center)
        else:
            manager.run_privileged(["rm", "-f", WIDGET_DEST])
            if os.path.exists(desktop_file_user):
                os.remove(desktop_file_user)
            # Aktualizacja bazy
            subprocess.run(["update-desktop-database", os.path.expanduser("~/.local/share/applications")])

    def _show_info_dialog(self, title, message, callback=None):
        dialog = Adw.MessageDialog(
            transient_for=self.parent_window,
            heading=title,
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dlg, response):
            if callback:
                callback()
            
        dialog.connect("response", on_response)
        dialog.present()

    def _on_close_and_open_center(self):
        # Uruchamiamy arc-center w tle
        subprocess.Popen(["linexin-center"], start_new_session=True)
        # Zamykamy arc-hello
        self.parent_window.close()
