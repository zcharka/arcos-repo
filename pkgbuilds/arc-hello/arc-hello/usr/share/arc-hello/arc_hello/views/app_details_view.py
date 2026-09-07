import os
import shutil
import webbrowser
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

try:
    gi.require_version("WebKit", "6.0")
    from gi.repository import WebKit
    WEBKIT_AVAILABLE = True
except Exception:
    WEBKIT_AVAILABLE = False

from gi.repository import Gtk, Adw, GLib, Pango, Gdk
from arc_hello.widgets.icons import load_icon
from arc_hello.utils.system import (
    is_package_installed,
    get_installed_package_version,
    install_package_with_fallback,
    uninstall_package_with_fallback,
    open_arch_wiki
)

class AppDetailsView(Gtk.Box):

    _WIKI_CSS = """
        html, body {
            background: transparent !important;
            font-family: Cantarell, sans-serif !important;
            margin: 0 !important;
            padding: 0 16px !important;
            font-size: 15px !important;
            line-height: 1.6 !important;
        }
        .archwiki-template-meta-related-articles,
        .toc, #toc, .mw-editsection { display: none !important; }
        a { text-decoration: none !important; }
        a:hover { text-decoration: underline !important; }
        h1, h2, h3, h4, h5 { margin-top: 1.2em !important; }
        h2 { padding-bottom: 4px !important; }
        code { padding: 1px 5px !important; }
        pre, code, kbd, .mw-highlight { border-radius: 6px !important; }
        pre, .mw-highlight {
            padding: 12px 16px !important;
            overflow-x: auto !important;
            line-height: 1.6 !important;
        }
        pre code { background: transparent !important; border: none !important; padding: 0 !important; }
        table.wikitable { border-collapse: collapse !important; }
        table.wikitable td, table.wikitable th { padding: 6px 10px !important; }
        .archwiki-template-box, .archwiki-template-box-note,
        .archwiki-template-box-warning, .archwiki-template-box-tip {
            border-radius: 4px !important;
            padding: 10px 14px !important;
            margin: 12px 0 !important;
        }
        img { max-width: 100% !important; }
        dl { margin-left: 1em !important; }
        dt { font-weight: bold !important; }
        @media (prefers-color-scheme: dark) {
            html, body { color: #e0e0e0 !important; }
            a { color: #78aeed !important; }
            a:visited { color: #a78aee !important; }
            h1, h2, h3, h4, h5 { color: #ffffff !important; }
            h2 { border-bottom: 1px solid rgba(255,255,255,0.12) !important; }
            dt { color: #ffffff !important; }
        }
    """

    def __init__(self, parent_window, back_cb, start_install_cb, show_toast_cb, start_uninstall_cb=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.parent_window = parent_window
        self.back_cb = back_cb
        self.start_install_cb = start_install_cb
        self.start_uninstall_cb = start_uninstall_cb
        self.show_toast_cb = show_toast_cb
        self.app_info = None
        self.pkg_name = ""
        self.wiki_url = None

        self._build_ui()

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
        
        self.detail_header_title = Gtk.Label()
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
        
        self.icon_holder = Gtk.Box()
        self.icon_holder.set_valign(Gtk.Align.START)
        app_header.append(self.icon_holder)
        
        meta_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        meta_box.set_valign(Gtk.Align.CENTER)
        meta_box.set_hexpand(True)
        
        self.detail_name_label = Gtk.Label()
        self.detail_name_label.set_halign(Gtk.Align.START)
        self.detail_name_label.add_css_class("title-1")
        meta_box.append(self.detail_name_label)
        
        self.detail_version_label = Gtk.Label()
        self.detail_version_label.set_halign(Gtk.Align.START)
        self.detail_version_label.add_css_class("dim-label")
        meta_box.append(self.detail_version_label)
        
        self.detail_status_label = Gtk.Label()
        self.detail_status_label.set_halign(Gtk.Align.START)
        meta_box.append(self.detail_status_label)
        
        app_header.append(meta_box)
        
        self.action_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.action_btn_box.set_valign(Gtk.Align.CENTER)
        app_header.append(self.action_btn_box)
        
        content_box.append(app_header)
        content_box.append(Gtk.Separator())
        
        # 2. Short Description
        self.detail_desc_label = Gtk.Label()
        self.detail_desc_label.set_halign(Gtk.Align.START)
        self.detail_desc_label.set_wrap(True)
        self.detail_desc_label.add_css_class("body")
        content_box.append(self.detail_desc_label)
        
        content_box.append(Gtk.Separator())
        
        # 3. Arch Wiki Section
        self.wiki_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        wiki_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        wiki_icon = load_icon("help-browser-symbolic", size=20)
        wiki_lbl = Gtk.Label(label="Arch Wiki")
        wiki_lbl.add_css_class("title-4")
        wiki_lbl.set_hexpand(True)
        wiki_lbl.set_halign(Gtk.Align.START)
        
        self.wiki_spinner = Gtk.Spinner()
        self.wiki_spinner.set_size_request(18, 18)
        
        btn_open_browser = Gtk.Button()
        btn_open_browser.add_css_class("flat")
        btn_open_browser.set_tooltip_text("Otwórz w przeglądarce")
        btn_open_browser.set_child(load_icon("web-browser-symbolic", size=16))
        btn_open_browser.connect("clicked", lambda _: self._open_wiki_in_browser())
        
        wiki_header.append(wiki_icon)
        wiki_header.append(wiki_lbl)
        wiki_header.append(self.wiki_spinner)
        wiki_header.append(btn_open_browser)
        self.wiki_card.append(wiki_header)
        

        self.wiki_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.wiki_card.append(self.wiki_content_box)
        
        self.lbl_wiki_text = Gtk.Label(label="Ładowanie informacji z Arch Wiki...")
        self.lbl_wiki_text.set_wrap(True)
        self.lbl_wiki_text.set_halign(Gtk.Align.START)
        self.lbl_wiki_text.add_css_class("dim-label")
        self.wiki_content_box.append(self.lbl_wiki_text)
        
        self.detail_webview = None

        
        content_box.append(self.wiki_card)

        clamp.set_child(content_box)
        scrolled.set_child(clamp)
        self.append(scrolled)

    def load_app(self, app_info: dict):
        self.app_info = app_info
        self.pkg_name = app_info.get("package", app_info.get("id", ""))
        self.detail_header_title.set_label(app_info["name"])

        # Update Icon
        child = self.icon_holder.get_first_child()
        if child:
            self.icon_holder.remove(child)
        icon_name = app_info.get("icon", "application-x-addon-symbolic")
        icon_widget = load_icon(icon_name, size=96)
        self.icon_holder.append(icon_widget)

        # Clear existing action buttons
        while self.action_btn_box.get_first_child():
            self.action_btn_box.remove(self.action_btn_box.get_first_child())

        # Update Labels
        self.detail_name_label.set_label(app_info["name"])

        installed = is_package_installed(self.pkg_name)
        version_str = get_installed_package_version(self.pkg_name) if installed else ""

        if version_str:
            self.detail_version_label.set_label(f"{version_str}  ·  local")
        else:
            source_text = "Repozytorium ArcOS" if self.pkg_name == "ogulniega" else "Oficjalne / AUR"
            self.detail_version_label.set_label(f"{self.pkg_name}  ·  {source_text}")

        if installed:
            self.detail_status_label.set_markup("<span foreground='#57e389'>● Zainstalowane</span>")

            btn_uninstall = Gtk.Button(label="Usuń")
            btn_uninstall.add_css_class("destructive-action")
            btn_uninstall.add_css_class("pill")
            btn_uninstall.connect("clicked", self._on_uninstall_clicked)
            self.action_btn_box.append(btn_uninstall)
        else:
            self.detail_status_label.set_markup("<span foreground='#9e9e9e'>○ Niezainstalowany</span>")

            btn_install = Gtk.Button(label="Zainstaluj")
            btn_install.add_css_class("suggested-action")
            btn_install.add_css_class("pill")
            btn_install.connect("clicked", self._on_install_clicked)
            self.action_btn_box.append(btn_install)

        self.detail_desc_label.set_label(app_info.get("description", app_info.get("desc", "Brak opisu.")))

        # Load Arch Wiki Content
        self.wiki_card.set_visible(True)
        self.wiki_spinner.start()
        
        if WEBKIT_AVAILABLE:
            self._ensure_detail_webview()
            self.detail_webview.load_uri("about:blank")
            self.detail_webview.set_visible(False)
        
        self.lbl_wiki_text.set_label("Pobieranie treści z Arch Wiki...")
        self.lbl_wiki_text.set_visible(True)
        self.wiki_content_box.set_visible(True)
        
        open_arch_wiki(self.pkg_name, self._on_wiki_fetched)

    def _on_wiki_fetched(self, text: str, wiki_url: str):
        def _update():
            self.wiki_spinner.stop()
            self.wiki_url = wiki_url
            if text and text.strip() and not text.startswith("Nie udało się"):
                if WEBKIT_AVAILABLE:
                    self.detail_webview.load_html(text, wiki_url)
                    self.lbl_wiki_text.set_visible(False)
                    self.detail_webview.set_visible(True)
                else:
                    self.lbl_wiki_text.set_label(text)
                self.wiki_card.set_visible(True)
            else:
                self.wiki_card.set_visible(False)
        GLib.idle_add(_update)

    def _open_wiki_in_browser(self):
        url = self.wiki_url or f"https://wiki.archlinux.org/index.php?search={self.pkg_name}"
        webbrowser.open(url)

    def _on_install_clicked(self, button):
        if self.app_info and self.start_install_cb:
            self.start_install_cb(self.pkg_name, self.app_info["name"])

    def _on_uninstall_clicked(self, button):
        if self.app_info and self.start_uninstall_cb:
            self.start_uninstall_cb(self.pkg_name, self.app_info["name"])

    def _ensure_detail_webview(self):
        if not WEBKIT_AVAILABLE or self.detail_webview is not None:
            return
        settings = WebKit.Settings()
        settings.set_enable_javascript(False)
        settings.set_enable_media(False)
        ucm = WebKit.UserContentManager()
        ucm.add_style_sheet(
            WebKit.UserStyleSheet(
                self._WIKI_CSS,
                WebKit.UserContentInjectedFrames.ALL_FRAMES,
                WebKit.UserStyleLevel.USER,
                None, None
            )
        )
        self.detail_webview = WebKit.WebView(
            settings=settings,
            user_content_manager=ucm
        )
        self.detail_webview.set_background_color(Gdk.RGBA(0, 0, 0, 0))
        self.detail_webview.set_vexpand(True)
        self.wiki_content_box.append(self.detail_webview)
