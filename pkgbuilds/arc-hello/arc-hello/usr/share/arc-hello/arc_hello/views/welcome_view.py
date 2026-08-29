import os
import shutil
import webbrowser
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango
from arc_hello.widgets.icons import load_icon
from arc_hello.widgets.hover_breathe import HoverBreatheController
from arc_hello.views.app_details_dialog import AppDetailsDialog
from arc_hello.utils.system import (
    is_package_installed,
    install_package_with_fallback,
    get_szczur_logo_path,
    APP_CATEGORIES,
    get_installed_desktop_files,
    set_default_app_for_mimes
)

QUICK_LINKS = [
    {
        "label": "Strona ArcOS & Dokumentacja",
        "description": "Dowiedz się więcej o systemie ArcOS",
        "icon": "help-browser-symbolic",
        "url": "https://zcharka.github.io/ArcOS/documentation",
    },
    {
        "label": "Kod źródłowy ArcOS",
        "description": "Przeglądaj i wspieraj ArcOS na GitHubie",
        "icon": "code-context-symbolic",
        "url": "https://github.com/zcharka/ArcOS",
    },
    {
        "label": "Repozytorium arcos-repo",
        "description": "Przeglądaj pakiety repozytorium arcos-repo",
        "icon": "folder-download-symbolic",
        "url": "https://github.com/zcharka/arcos-repo",
    },
    {
        "label": "Zgłoś błąd",
        "description": "Pomóż nam się rozwijać, zgłaszając problemy",
        "icon": "dialog-warning-symbolic",
        "url": "https://github.com/zcharka/ArcOS/issues",
    },
]

RECOMMENDED_APPS = [
    {
        "name": "Ogulniega",
        "description": "Launcher dla klienta Ogulniega Client (Minecraft). Instalator z pliku .flatpakref.",
        "icon": "applications-games-symbolic",
        "package": "ogulniega",
        "category": "Gry / Minecraft",
    },
    {
        "name": "Blockbench",
        "description": "Edytor modeli 3D i pikselartu dla Minecraft i gier 3D.",
        "icon": "applications-games-symbolic",
        "package": "blockbench",
        "category": "Grafika 3D",
    },
    {
        "name": "Blender",
        "description": "Zaawansowany pakiet do tworzenia grafiki i animacji 3D.",
        "icon": "applications-graphics-symbolic",
        "package": "blender",
        "category": "Grafika 3D",
    },
    {
        "name": "Opera Browser",
        "description": "Szybka i bezpieczna przeglądarka internetowa z VPN.",
        "icon": "web-browser-symbolic",
        "package": "opera",
        "category": "Internet",
    },
    {
        "name": "Sober",
        "description": "Środowisko uruchomieniowe do uruchamiania gier na Linuksie.",
        "icon": "input-gaming-symbolic",
        "package": "sober",
        "category": "Gry",
    },
]

class WelcomeView(Gtk.Box):
    def __init__(self, parent_window, run_cmd_cb, open_changelog_cb, open_x11_cb, show_toast_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.parent_window = parent_window
        self.run_cmd_cb = run_cmd_cb
        self.open_changelog_cb = open_changelog_cb
        self.open_x11_cb = open_x11_cb
        self.show_toast_cb = show_toast_cb

        self._download_buttons = {}
        self._build_ui()

    def _build_ui(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(1280)
        clamp.set_tightening_threshold(980)

        scroll_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        scroll_content.set_margin_top(18)
        scroll_content.set_margin_bottom(24)
        scroll_content.set_margin_start(24)
        scroll_content.set_margin_end(24)

        # Hero Header with szczur.svg Breathing Logo
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hero.set_halign(Gtk.Align.CENTER)
        hero.set_margin_top(8)
        hero.set_margin_bottom(12)

        logo_shell = Gtk.Overlay()
        logo_shell.set_halign(Gtk.Align.CENTER)
        logo_shell.set_valign(Gtk.Align.CENTER)
        logo_shell.set_size_request(112, 112)

        logo_path = get_szczur_logo_path()
        logo_image = load_icon(logo_path, size=88, fallback="system-run-symbolic")
        logo_shell.set_child(logo_image)
        self._breathe = HoverBreatheController(logo_shell, logo_image, base=88.0, hover=96.0, press=78.0)

        hero.append(logo_shell)

        title = Gtk.Label(label="Witaj w ArcOS")
        title.add_css_class("title-1")
        hero.append(title)

        subtitle = Gtk.Label(label="Odkryj aplikacje i narzędzia stworzone dla Twojego systemu")
        subtitle.add_css_class("dim-label")
        hero.append(subtitle)

        scroll_content.append(hero)

        # Main Body: 2 Columns
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        body.set_valign(Gtk.Align.START)
        body.set_vexpand(True)
        body.set_hexpand(True)

        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        left_col.set_hexpand(True)
        left_col.set_valign(Gtk.Align.START)

        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        right_col.set_size_request(300, -1)
        right_col.set_valign(Gtk.Align.START)
        right_col.set_hexpand(False)

        # Left Column Section 1: Polecane aplikacje (w tym Ogulniega)
        left_col.append(self._create_section(
            "Polecane aplikacje",
            "Wybrane aplikacje dla systemu ArcOS (kliknij kartę, aby zobaczyć szczegóły)",
            self._build_recommended_grid()
        ))

        # Left Column Section 2: System i Narzędzia
        left_col.append(self._create_section(
            "System i Narzędzia",
            "Optymalizacja gier, wirtualizacja oraz serwer X11",
            self._build_system_tools_grid()
        ))

        # Left Column Section 3: Domyślne Programy
        left_col.append(self._create_section(
            "Domyślne Programy",
            "Szybkie skojarzenia plików i aplikacji",
            self._build_defaults_card()
        ))

        # Right Column Section 1: Nowe (Featured Highlighted Arc Store Card)
        right_col.append(self._build_new_section())

        # Right Column Section 2: Szybkie łącza
        right_col.append(self._build_quick_links())

        body.append(left_col)
        body.append(right_col)

        scroll_content.append(body)

        footer = Gtk.Label(label="Dziękujemy za wybór systemu ArcOS ❤️")
        footer.add_css_class("dim-label")
        footer.set_halign(Gtk.Align.CENTER)
        footer.set_margin_top(16)
        footer.set_margin_bottom(8)
        scroll_content.append(footer)

        clamp.set_child(scroll_content)
        scrolled.set_child(clamp)

        self.append(scrolled)

    def _create_section(self, title: str, subtitle: str, content_widget: Gtk.Widget) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header.set_halign(Gtk.Align.START)

        title_label = Gtk.Label(label=title)
        title_label.add_css_class("title-3")
        title_label.set_halign(Gtk.Align.START)
        header.append(title_label)

        if subtitle:
            sub = Gtk.Label(label=subtitle)
            sub.add_css_class("dim-label")
            sub.add_css_class("caption")
            sub.set_halign(Gtk.Align.START)
            header.append(sub)

        section.append(header)
        section.append(content_widget)
        return section

    def _build_recommended_grid(self) -> Gtk.FlowBox:
        grid = Gtk.FlowBox()
        grid.set_valign(Gtk.Align.START)
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        grid.set_homogeneous(True)
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.add_css_class("linexin-app-grid")
        grid.set_min_children_per_line(2)
        grid.set_max_children_per_line(2)

        for app in RECOMMENDED_APPS:
            card = self._create_app_card_with_details(app)
            grid.append(card)

        return grid

    def _build_system_tools_grid(self) -> Gtk.FlowBox:
        grid = Gtk.FlowBox()
        grid.set_valign(Gtk.Align.START)
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        grid.set_homogeneous(True)
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.add_css_class("linexin-app-grid")
        grid.set_min_children_per_line(2)
        grid.set_max_children_per_line(2)

        # 1. Steam Big Picture & Gaming Tools
        app_steam = {
            "name": "Steam & Gamemode",
            "description": "Ustawienia Big Picture oraz optymalizatory gamemode/gamescope",
            "icon": "input-gaming-symbolic",
            "package": "gamemode",
            "category": "Gry"
        }
        grid.append(self._create_app_card_with_details(app_steam))

        # 2. vtrt-manager / virt-manager
        app_vtrt = {
            "name": "vtrt-manager",
            "description": "Menedżer wirtualizacji QEMU/KVM i libvirt",
            "icon": "system-run-symbolic",
            "package": "vtrt-manager",
            "category": "Wirtualizacja"
        }
        grid.append(self._create_app_card_with_details(app_vtrt))

        # 3. Sesja X11
        card_x11 = self._create_custom_card(
            "Sesja X11",
            "Instalator serwera wyświetlania X11 z instrukcją przełączania",
            "video-display-symbolic",
            action_label="Zainstaluj",
            on_click=lambda btn: self.open_x11_cb()
        )
        grid.append(card_x11)

        return grid

    def _build_defaults_card(self) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("app-card")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl = Gtk.Label(label="Kategoria:")
        lbl.set_halign(Gtk.Align.START)

        cats = list(APP_CATEGORIES.keys())
        dropdown = Gtk.DropDown.new_from_strings(cats)
        dropdown.set_hexpand(True)

        row.append(lbl)
        row.append(dropdown)
        card.append(row)

        apps = get_installed_desktop_files()
        app_names = [a["name"] for a in apps]

        row_app = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_app = Gtk.Label(label="Aplikacja:")
        dropdown_app = Gtk.DropDown.new_from_strings(app_names)
        dropdown_app.set_hexpand(True)

        row_app.append(lbl_app)
        row_app.append(dropdown_app)
        card.append(row_app)

        btn_set = Gtk.Button(label="Ustaw domyślne")
        btn_set.add_css_class("suggested-action")
        btn_set.add_css_class("linexin-card-action")
        btn_set.set_halign(Gtk.Align.END)

        def _on_set(b):
            c_idx = dropdown.get_selected()
            a_idx = dropdown_app.get_selected()
            if 0 <= c_idx < len(cats) and 0 <= a_idx < len(apps):
                cat_name = cats[c_idx]
                app_file = apps[a_idx]["desktop_file"]
                mimes = APP_CATEGORIES[cat_name]["mimes"]
                ok = set_default_app_for_mimes(app_file, mimes)
                if ok:
                    self.show_toast_cb(f"Ustawiono '{apps[a_idx]['name']}' dla kategorii '{cat_name}'.")
                else:
                    self.show_toast_cb("Błąd podczas przypisywania aplikacji.")

        btn_set.connect("clicked", _on_set)
        card.append(btn_set)
        return card

    def _build_new_section(self) -> Gtk.Box:
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label(label="Nowe")
        title.add_css_class("title-3")
        title.add_css_class("accent")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)

        badge = Gtk.Label(label="NOWE")
        badge.add_css_class("linexin-new-badge")
        badge.set_valign(Gtk.Align.CENTER)

        header.append(title)
        header.append(badge)
        section.append(header)

        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrapper.add_css_class("linexin-new-section")

        app_arc_store = {
            "name": "Arc Store",
            "description": "Oficjalne sklep i centrum oprogramowania dla systemów ArcOS.",
            "icon": "software-store-symbolic",
            "package": "arc-store",
            "category": "Centrum Oprogramowania"
        }
        card = self._create_app_card_with_details(app_arc_store, highlighted=True)
        wrapper.append(card)
        section.append(wrapper)
        return section

    def _build_quick_links(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.START)

        label = Gtk.Label(label="Szybkie łącza")
        label.add_css_class("title-3")
        label.set_halign(Gtk.Align.START)
        label.set_margin_top(4)
        box.append(label)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.add_css_class("boxed-list")

        for link in QUICK_LINKS:
            row = Adw.ActionRow(title=link["label"], subtitle=link["description"])
            row.set_activatable(True)
            row.set_subtitle_lines(2)
            row.add_prefix(load_icon(link["icon"], size=20))
            row.add_suffix(load_icon("go-next-symbolic", size=16))
            row.connect("activated", lambda r, u=link["url"]: webbrowser.open(u))
            listbox.append(row)

        row_cl = Adw.ActionRow(title="Changelog", subtitle="Zobacz historię zmian (najnowsza wersja)")
        row_cl.set_activatable(True)
        row_cl.add_prefix(load_icon("document-properties-symbolic", size=20))
        row_cl.add_suffix(load_icon("go-next-symbolic", size=16))
        row_cl.connect("activated", lambda *_: self.open_changelog_cb())
        listbox.append(row_cl)

        box.append(listbox)
        return box

    def _create_app_card_with_details(self, app_info: dict, highlighted: bool = False) -> Gtk.Box:
        """
        Creates an app card where clicking the card body opens Linpama-style App Details Dialog.
        """
        pkg = app_info.get("package", app_info.get("name", ""))
        installed = is_package_installed(pkg)

        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        card.add_css_class("card")
        card.add_css_class("linexin-app-card")
        card.add_css_class("activatable")
        card.set_size_request(-1, 72)
        card.set_tooltip_text(f"{app_info['name']}\n{app_info.get('description', '')}\nKliknij, aby zobaczyć szczegóły")

        if highlighted:
            card.add_css_class("linexin-new-card")

        # Gesture click on card opens AppDetailsDialog
        click_gesture = Gtk.GestureClick()
        click_gesture.set_button(1)
        click_gesture.connect("released", lambda g, n, x, y: self._open_app_details(app_info))
        card.add_controller(click_gesture)

        icon_name = app_info.get("icon", "application-x-addon-symbolic")
        icon = load_icon(icon_name, size=36)
        icon.set_valign(Gtk.Align.CENTER)
        icon.set_margin_start(10)
        card.append(icon)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)
        text_box.set_margin_top(10)
        text_box.set_margin_bottom(10)

        name_label = Gtk.Label(label=app_info["name"])
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.add_css_class("heading")
        text_box.append(name_label)

        desc_label = Gtk.Label(label=app_info.get("description", ""))
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("dim-label")
        desc_label.add_css_class("caption")
        desc_label.set_ellipsize(Pango.EllipsizeMode.END)
        desc_label.set_max_width_chars(22)
        desc_label.set_lines(2)
        desc_label.set_wrap(True)
        desc_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        text_box.append(desc_label)

        card.append(text_box)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.set_margin_end(10)

        btn = Gtk.Button()
        if installed:
            btn.set_label("Zainstalowano")
            btn.set_sensitive(False)
            btn.add_css_class("linexin-card-action")
        else:
            btn.set_label("Zainstaluj")
            btn.add_css_class("suggested-action")
            btn.add_css_class("linexin-card-action")
            btn.connect("clicked", lambda b: self._install_pkg(pkg, b))

        btn_box.append(btn)
        card.append(btn_box)

        self._download_buttons[pkg] = btn
        return card

    def _create_custom_card(self, name: str, description: str, icon_name: str,
                            action_label: str = "Zainstaluj", on_click=None) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        card.add_css_class("card")
        card.add_css_class("linexin-app-card")
        card.set_size_request(-1, 72)

        icon = load_icon(icon_name, size=36)
        icon.set_valign(Gtk.Align.CENTER)
        icon.set_margin_start(10)
        card.append(icon)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_valign(Gtk.Align.CENTER)

        name_label = Gtk.Label(label=name)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        text_box.append(name_label)

        desc_label = Gtk.Label(label=description)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("dim-label")
        desc_label.add_css_class("caption")
        desc_label.set_ellipsize(Pango.EllipsizeMode.END)
        desc_label.set_max_width_chars(22)
        desc_label.set_lines(2)
        text_box.append(desc_label)

        card.append(text_box)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.set_margin_end(10)

        btn = Gtk.Button(label=action_label)
        btn.add_css_class("suggested-action")
        btn.add_css_class("linexin-card-action")
        if on_click:
            btn.connect("clicked", on_click)

        btn_box.append(btn)
        card.append(btn_box)
        return card

    def _open_app_details(self, app_info: dict):
        dialog = AppDetailsDialog(
            parent_window=self.parent_window,
            app_info=app_info,
            run_cmd_cb=self.run_cmd_cb,
            show_toast_cb=self.show_toast_cb
        )
        dialog.present()

    def _install_pkg(self, pkg_name: str, button: Gtk.Button):
        button.set_sensitive(False)
        button.set_label("Instalacja...")

        def _on_output(line, tag):
            self.run_cmd_cb(line, tag)

        def _on_finished(code):
            if code == 0:
                button.set_label("Zainstalowano")
                button.remove_css_class("suggested-action")
            else:
                button.set_sensitive(True)
                button.set_label("Zainstaluj")

        install_package_with_fallback(pkg_name, self.parent_window, _on_output, _on_finished)
