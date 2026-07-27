import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GObject, Adw
from .common import create_entrance_animation

class WelcomeScreen(Gtk.Box):
    __gsignals__ = {
        'mode-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_container.set_margin_start(20)
        self.main_container.set_margin_end(20)
        self.main_container.set_margin_top(40)
        self.main_container.set_margin_bottom(40)
        self.append(self.main_container)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'logo.svg')
        if os.path.exists(logo_path):
            logo = Gtk.Image.new_from_file(logo_path)
        else:
            logo = Gtk.Image.new_from_icon_name('system-software-install-symbolic')
        logo.set_pixel_size(140)
        self.main_container.append(logo)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="xx-large" weight="bold">Arc Manager</span>')
        self.main_container.append(title_label)

        # Subtitle
        subtitle_label = Gtk.Label(label="Zarządzaj pakietami ArcOS i twórz nowe obrazy systemu.")
        subtitle_label.add_css_class('dim-label')
        self.main_container.append(subtitle_label)

        # Mode Buttons
        self.buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        self.modes_list = Gtk.ListBox()
        self.modes_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.modes_list.add_css_class('boxed-list')
        self.buttons_box.append(self.modes_list)
        
        self.add_mode_row('publish', 'Publikuj paczki', 'Zaktualizuj wybrane pakiety', 'package-x-generic-symbolic', suggested=True)
        self.add_mode_row('iso', 'Zbuduj tylko ISO', 'Wygeneruj nowy obraz instalacyjny', 'media-optical-symbolic')
        self.add_mode_row('full', 'Pełna aktualizacja', 'Opublikuj paczki i zbuduj ISO', 'system-software-update-symbolic')
        
        self.main_container.append(self.buttons_box)
        
        self.connect('map', self._on_map)

    def add_mode_row(self, mode_id, title, subtitle, icon_name, suggested=False):
        row = Adw.ActionRow(title=title, subtitle=subtitle)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        row.add_prefix(icon)
        
        suffix = Gtk.Image.new_from_icon_name('go-next-symbolic')
        row.add_suffix(suffix)
        
        row.add_css_class('mode-button')
        if suggested:
            row.add_css_class('suggested-action')
            
        row.connect('activated', lambda r: self.emit('mode-selected', mode_id))
        row.set_activatable(True)
        self.modes_list.append(row)

    def _on_map(self, widget):
        create_entrance_animation(self, self.main_container)
