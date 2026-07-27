import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GObject, Adw
from .common import create_pill_button

class OptionsScreen(Gtk.Box):
    __gsignals__ = {
        'start-operation': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        
        self.mode = 'full'
        
        self.title_label = Gtk.Label()
        self.title_label.set_markup('<span size="xx-large" weight="bold">Opcje</span>')
        self.append(self.title_label)
        
        clamp = Adw.Clamp(maximum_size=600)
        self.append(clamp)
        
        self.prefs_group = Adw.PreferencesGroup()
        clamp.set_child(self.prefs_group)
        
        self.row_auto_pkgrel = Adw.SwitchRow(title="Automatycznie zwiększ pkgrel", active=True)
        self.prefs_group.add(self.row_auto_pkgrel)
        
        self.row_commit_msg = Adw.EntryRow(title="Wiadomość commita")
        self.row_commit_msg.set_text("Update ArcOS packages")
        self.prefs_group.add(self.row_commit_msg)
        
        self.row_build_iso = Adw.SwitchRow(title="Po publikacji zbuduj ISO", active=True)
        self.prefs_group.add(self.row_build_iso)
        
        self.summary_label = Gtk.Label(label="")
        self.summary_label.set_margin_top(10)
        self.summary_label.set_margin_bottom(10)
        self.append(self.summary_label)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)
        
        self.btn_back = create_pill_button("Wróć", 'back_button')
        self.btn_start = create_pill_button("Rozpocznij", 'continue_button')
        self.btn_start.add_css_class('suggested-action')
        self.btn_start.connect('clicked', lambda x: self.emit('start-operation'))
        
        btn_box.append(self.btn_back)
        btn_box.append(self.btn_start)
        self.append(btn_box)
        
    def setup_for_mode(self, mode, selected_packages=None):
        self.mode = mode
        if mode == 'publish':
            self.title_label.set_markup('<span size="xx-large" weight="bold">Opcje publikacji</span>')
            self.row_auto_pkgrel.set_visible(True)
            self.row_commit_msg.set_visible(True)
            self.row_build_iso.set_visible(False)
        elif mode == 'iso':
            self.title_label.set_markup('<span size="xx-large" weight="bold">Opcje ISO</span>')
            self.row_auto_pkgrel.set_visible(False)
            self.row_commit_msg.set_visible(False)
            self.row_build_iso.set_visible(False)
        else: # full
            self.title_label.set_markup('<span size="xx-large" weight="bold">Opcje pełnej aktualizacji</span>')
            self.row_auto_pkgrel.set_visible(True)
            self.row_commit_msg.set_visible(True)
            self.row_build_iso.set_visible(True)
            
        if selected_packages:
            pkgs = ", ".join([p.name for p in selected_packages])
            self.summary_label.set_markup(f"<b>Wybrane pakiety:</b> {pkgs}")
        else:
            self.summary_label.set_text("")
            
    @property
    def auto_pkgrel(self):
        return self.row_auto_pkgrel.get_active()
        
    @property
    def commit_message(self):
        return self.row_commit_msg.get_text()
        
    @property
    def build_iso_after(self):
        return self.row_build_iso.get_active()
