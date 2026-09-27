import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from arc_hello.widgets.icons import load_icon

CHANGELOG_ENTRIES = [
    {
        "version": "1.0.0 (ArcOS Rolling Release)",
        "date": "Wrzesień 2026",
        "highlights": [
            "Nowy, odświeżony interfejs w stylu Linexin / Linepama (GTK4 + Libadwaita).",
            "Dedykowane widoki wewnątrz okna zamiast nakładających się okien dialogowych.",
            "Wbudowany podgląd i integracja z Arch Wiki.",
            "Wsparcie dla instalowania klienta Ogulniega z wewnętrznego repozytorium ArcOS.",
            "Pełna integracja z SudoManager do bezpiecznego uwierzytelniania sudo."
        ]
    },
    {
        "version": "0.9.5 (Beta)",
        "date": "Sierpień 2026",
        "highlights": [
            "Wsparcie dla automatycznego wykrywania sesji X11 dla KDE Plasma.",
            "Konsola logów instalacji z kolorowaniem składni.",
            "Nowy Hero Header z logo szczur.svg."
        ]
    }
]

class ChangelogView(Gtk.Box):
    """
    Full-page Changelog view with back button and animated stack transition.
    """
    def __init__(self, parent_window, back_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.parent_window = parent_window
        self.back_cb = back_cb

        self._build_ui()

    def _build_ui(self):
        # Header bar with back button
        header_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_bar.add_css_class("flat")
        header_bar.set_margin_top(12)
        header_bar.set_margin_bottom(12)
        header_bar.set_margin_start(16)
        header_bar.set_margin_end(16)

        btn_back = Gtk.Button()
        btn_back.add_css_class("flat")
        btn_back.add_css_class("pill-action")

        back_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        back_icon = Gtk.Image.new_from_icon_name("go-previous-symbolic")
        lbl_back_title = Gtk.Label(label="Powrót do strony głównej")
        lbl_back_title.add_css_class("heading")

        back_content.append(back_icon)
        back_content.append(lbl_back_title)
        btn_back.set_child(back_content)
        btn_back.connect("clicked", lambda _: self.back_cb())

        header_bar.append(btn_back)
        self.append(header_bar)

        # Content Scrolled Window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        clamp = Adw.Clamp(maximum_size=780)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(10)
        box.set_margin_bottom(30)
        box.set_margin_start(20)
        box.set_margin_end(20)

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Historia Zmian i Dziennik Wydań (Changelog)</span>')
        title.set_halign(Gtk.Align.START)
        box.append(title)

        for entry in CHANGELOG_ENTRIES:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("app-card")

            ver_lbl = Gtk.Label()
            ver_lbl.set_markup(f"<b>Wersja {entry['version']}</b> — <span foreground='#9a9996'>{entry['date']}</span>")
            ver_lbl.set_halign(Gtk.Align.START)
            card.append(ver_lbl)

            for h in entry["highlights"]:
                item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                bullet = Gtk.Label(label="•")
                bullet.add_css_class("accent-label")
                bullet.set_valign(Gtk.Align.START)

                lbl = Gtk.Label(label=h)
                lbl.set_wrap(True)
                lbl.set_halign(Gtk.Align.START)

                item_box.append(bullet)
                item_box.append(lbl)
                card.append(item_box)

            box.append(card)

        clamp.set_child(box)
        scrolled.set_child(clamp)
        self.append(scrolled)
