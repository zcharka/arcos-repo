import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GObject, Adw
from .common import create_pill_button

class ErrorScreen(Gtk.Box):
    __gsignals__ = {
        'back-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_spacing(20)
        
        icon = Gtk.Image.new_from_icon_name('dialog-error-symbolic')
        icon.set_pixel_size(120)
        icon.add_css_class('error_icon')
        self.append(icon)
        
        self.title_label = Gtk.Label()
        self.title_label.set_markup('<span size="xx-large" weight="bold">Nie udało się ukończyć operacji</span>')
        self.append(self.title_label)
        
        self.desc_label = Gtk.Label()
        self.append(self.desc_label)
        
        clamp = Adw.Clamp(maximum_size=600)
        self.append(clamp)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        clamp.set_child(box)
        
        self.rev = Gtk.Revealer()
        
        log_frame = Gtk.Frame()
        log_frame.add_css_class('view')
        
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_min_content_height(150)
        self.tv = Gtk.TextView()
        self.tv.set_editable(False)
        self.tv.set_monospace(True)
        log_scroll.set_child(self.tv)
        log_frame.set_child(log_scroll)
        self.rev.set_child(log_frame)
        box.append(self.rev)
        
        self.btn_toggle = Gtk.ToggleButton(label="Pokaż szczegóły")
        self.btn_toggle.set_halign(Gtk.Align.CENTER)
        self.btn_toggle.connect('toggled', self._on_toggle)
        box.append(self.btn_toggle)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(20)
        
        self.btn_log = create_pill_button("Otwórz log", 'back_button')
        
        self.btn_back = create_pill_button("Wróć", 'continue_button')
        self.btn_back.add_css_class('suggested-action')
        self.btn_back.connect('clicked', lambda x: self.emit('back-clicked'))
        
        btn_box.append(self.btn_log)
        btn_box.append(self.btn_back)
        self.append(btn_box)

    def _on_toggle(self, btn):
        self.rev.set_reveal_child(btn.get_active())
        btn.set_label("Ukryj szczegóły" if btn.get_active() else "Pokaż szczegóły")

    def set_error(self, short_message, full_details, log_path=None):
        self.desc_label.set_text(short_message)
        self.tv.get_buffer().set_text(full_details)
        if not log_path:
            self.btn_log.set_visible(False)
