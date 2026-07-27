import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GObject, Adw
from .common import create_pill_button, create_entrance_animation

class SuccessScreen(Gtk.Box):
    __gsignals__ = {
        'done-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_spacing(20)
        
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.append(self.main_container)
        
        icon = Gtk.Image.new_from_icon_name('checkbox-checked-symbolic')
        icon.set_pixel_size(120)
        icon.add_css_class('success_icon')
        self.main_container.append(icon)
        
        self.title_label = Gtk.Label()
        self.title_label.set_markup('<span size="xx-large" weight="bold" color="#2E7D32">ArcOS został zaktualizowany</span>')
        self.main_container.append(self.title_label)
        
        self.subtitle_label = Gtk.Label()
        self.main_container.append(self.subtitle_label)
        
        clamp = Adw.Clamp(maximum_size=500)
        self.main_container.append(clamp)
        
        self.results_list = Gtk.ListBox()
        self.results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_list.add_css_class('boxed-list')
        clamp.set_child(self.results_list)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(20)
        
        self.btn_log = create_pill_button("Otwórz log", 'back_button')
        
        self.btn_done = create_pill_button("Gotowe", 'animated_button')
        self.btn_done.add_css_class('suggested-action')
        # adding gradient inline via css class or inline style could be done, but we'll stick to animated_button styling
        self.btn_done.connect('clicked', lambda x: self.emit('done-clicked'))
        
        btn_box.append(self.btn_log)
        btn_box.append(self.btn_done)
        self.main_container.append(btn_box)
        
        self.connect('map', self._on_map)

    def _on_map(self, widget):
        create_entrance_animation(self, self.main_container)

    def set_results(self, title, subtitle, results, log_path=None):
        if title:
            self.title_label.set_markup(f'<span size="xx-large" weight="bold" color="#2E7D32">{title}</span>')
        self.subtitle_label.set_text(subtitle)
        
        while child := self.results_list.get_first_child():
            self.results_list.remove(child)
            
        for r in results:
            row = Adw.ActionRow(title=r)
            icon = Gtk.Image.new_from_icon_name('checkbox-checked-symbolic')
            icon.add_css_class('success_icon')
            row.add_prefix(icon)
            self.results_list.append(row)
            
        if not log_path:
            self.btn_log.set_visible(False)
