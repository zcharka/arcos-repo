import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango
from arc_hello.widgets.icons import load_icon
from arc_hello.utils.system import (
    is_package_installed,
    get_x11_installation_packages
)

class X11ManagerView(Gtk.Box):
    """
    Dedicated view for X11 Session management.
    """
    def __init__(self, parent_window, back_cb, start_install_cb, start_uninstall_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.parent_window = parent_window
        self.back_cb = back_cb
        self.start_install_cb = start_install_cb
        self.start_uninstall_cb = start_uninstall_cb

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
        
        self.detail_header_title = Gtk.Label(label="Zarządzanie Sesją X11")
        self.detail_header_title.add_css_class("title-4")
        self.detail_header_title.set_ellipsize(Pango.EllipsizeMode.END)
        self.detail_header_title.set_margin_start(6)
        toolbar.append(self.detail_header_title)
        
        self.append(toolbar)
        self.append(Gtk.Separator())

        # ── Scrolled Content ──
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        clamp = Adw.Clamp(maximum_size=820)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(36)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)

        # 1. App Header Section
        app_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        
        icon_holder = Gtk.Box()
        icon_holder.set_valign(Gtk.Align.START)
        icon_widget = load_icon("video-display", size=96)
        icon_holder.append(icon_widget)
        app_header.append(icon_holder)
        
        meta_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        meta_box.set_valign(Gtk.Align.CENTER)
        meta_box.set_hexpand(True)
        
        detail_name_label = Gtk.Label(label="Serwer Wyświetlania X11")
        detail_name_label.set_halign(Gtk.Align.START)
        detail_name_label.add_css_class("title-1")
        meta_box.append(detail_name_label)
        
        self.detail_status_label = Gtk.Label()
        self.detail_status_label.set_halign(Gtk.Align.START)
        meta_box.append(self.detail_status_label)
        
        app_header.append(meta_box)
        content_box.append(app_header)
        
        # Action Buttons Area
        self.btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.btn_box.set_halign(Gtk.Align.START)
        
        # Install Button
        self.btn_install = Gtk.Button(label="Zainstaluj X11")
        self.btn_install.add_css_class("suggested-action")
        self.btn_install.add_css_class("pill")
        self.btn_install.connect("clicked", self._on_install_clicked)
        self.btn_box.append(self.btn_install)

        # Install Missing Button
        self.btn_install_missing = Gtk.Button(label="Doinstaluj brakujące pakiety")
        self.btn_install_missing.add_css_class("pill")
        self.btn_install_missing.connect("clicked", self._on_install_clicked)
        self.btn_box.append(self.btn_install_missing)

        # Uninstall Button
        self.btn_uninstall = Gtk.Button(label="Odinstaluj")
        self.btn_uninstall.add_css_class("destructive-action")
        self.btn_uninstall.add_css_class("pill")
        self.btn_uninstall.connect("clicked", self._on_uninstall_clicked)
        self.btn_box.append(self.btn_uninstall)

        content_box.append(self.btn_box)
        content_box.append(Gtk.Separator())

        # Description
        desc_label = Gtk.Label()
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.add_css_class("body")
        desc_label.set_markup(
            "X11 (X Window System) to opcjonalny serwer wyświetlania, przydatny jeśli korzystasz ze starszych aplikacji, gier "
            "lub narzędzi, które nie obsługują jeszcze w pełni protokołu Wayland.\n\n"
            "Zainstalowanie X11 pozwoli na wybór tego środowiska podczas logowania w menedżerze ekranu (np. SDDM, GDM)."
        )
        content_box.append(desc_label)

        clamp.set_child(content_box)
        scrolled.set_child(clamp)
        self.append(scrolled)

    def refresh_state(self):
        pkgs = get_x11_installation_packages()
        installed_count = 0
        for pkg in pkgs:
            if is_package_installed(pkg):
                installed_count += 1

        if installed_count == 0:
            # Nothing installed
            self.detail_status_label.set_markup("<span foreground='#9e9e9e'>○ Niezainstalowany</span>")
            self.btn_install.set_sensitive(True)
            self.btn_install.set_visible(True)
            self.btn_install_missing.set_visible(False)
            self.btn_uninstall.set_sensitive(False)
            self.btn_install.set_label("Zainstaluj całe środowisko")
        elif installed_count == len(pkgs):
            # All installed
            self.detail_status_label.set_markup("<span foreground='#57e389'>● Zainstalowane w pełni</span>")
            self.btn_install.set_sensitive(False)
            self.btn_install.set_visible(True)
            self.btn_install_missing.set_visible(False)
            self.btn_uninstall.set_sensitive(True)
            self.btn_install.set_label("Zainstalowano")
        else:
            # Partial
            self.detail_status_label.set_markup("<span foreground='#f8e45c'>◑ Częściowo zainstalowane</span>")
            self.btn_install.set_sensitive(False)
            self.btn_install.set_visible(False)
            self.btn_install_missing.set_visible(True)
            self.btn_install_missing.set_sensitive(True)
            self.btn_uninstall.set_sensitive(True)

    def _on_install_clicked(self, button):
        if self.start_install_cb:
            self.start_install_cb("x11", "Sesja X11")

    def _on_uninstall_clicked(self, button):
        if self.start_uninstall_cb:
            self.start_uninstall_cb("x11", "Sesja X11")
