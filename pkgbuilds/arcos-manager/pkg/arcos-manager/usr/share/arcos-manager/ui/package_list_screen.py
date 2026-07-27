import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GObject, Adw
from .common import create_pill_button

class PackageListScreen(Gtk.Box):
    __gsignals__ = {
        'packages-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(10)
        
        self.packages = []
        self.selected = set()
        
        # Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_label = Gtk.Label()
        title_label.set_markup('<span size="xx-large" weight="bold">Wybierz pakiety</span>')
        self.subtitle_label = Gtk.Label(label="Wybierz pakiety do aktualizacji")
        self.subtitle_label.add_css_class('dim-label')
        title_box.append(title_label)
        title_box.append(self.subtitle_label)
        self.append(title_box)
        
        # Clamp
        clamp = Adw.Clamp(maximum_size=600)
        self.append(clamp)
        
        self.clamp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        clamp.set_child(self.clamp_box)
        
        # Select All / Deselect All
        sel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_sel_all = Gtk.Button(label="Zaznacz wszystko")
        btn_sel_all.connect('clicked', self._on_select_all)
        btn_desel_all = Gtk.Button(label="Odznacz wszystko")
        btn_desel_all.connect('clicked', self._on_deselect_all)
        sel_box.append(btn_sel_all)
        sel_box.append(btn_desel_all)
        self.clamp_box.append(sel_box)
        
        # List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(300)
        scrolled.set_vexpand(True)
        
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class('boxed-list')
        scrolled.set_child(self.listbox)
        self.clamp_box.append(scrolled)
        
        # Bottom bar
        self.count_label = Gtk.Label(label="Wybrano 0 z 0")
        self.clamp_box.append(self.count_label)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)
        self.btn_back = create_pill_button("Wróć", 'back_button')
        self.btn_next = create_pill_button("Dalej", 'continue_button')
        self.btn_next.add_css_class('suggested-action')
        self.btn_next.set_sensitive(False)
        self.btn_next.connect('clicked', self._on_next_clicked)
        btn_box.append(self.btn_back)
        btn_box.append(self.btn_next)
        self.append(btn_box)
        
        self.empty_state_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.empty_state_box.set_halign(Gtk.Align.CENTER)
        self.empty_state_box.set_valign(Gtk.Align.CENTER)
        empty_title = Gtk.Label(label="Nie znaleziono pakietów")
        empty_title.add_css_class('title-1')
        self.empty_state_box.append(empty_title)
        self.empty_desc = Gtk.Label(label="Sprawdź ścieżkę")
        self.empty_state_box.append(self.empty_desc)
        btn_refresh = Gtk.Button(label="Odśwież")
        self.empty_state_box.append(btn_refresh)
        # Usually one might put empty_state_box inside a stack, but for now we'll just toggle visibility
        self.empty_state_box.set_visible(False)
        self.append(self.empty_state_box)

    def set_packages(self, packages: list):
        self.packages = packages
        self.selected.clear()
        
        # Clear listbox
        while child := self.listbox.get_first_child():
            self.listbox.remove(child)
            
        if not packages:
            self.clamp_box.set_visible(False)
            self.empty_state_box.set_visible(True)
            return
            
        self.clamp_box.set_visible(True)
        self.empty_state_box.set_visible(False)
        
        for pkg in packages:
            row = Adw.ActionRow(title=pkg.name, subtitle=f"{pkg.pkgver}-{pkg.pkgrel}")
            
            check = Gtk.CheckButton()
            check.connect('toggled', self._on_check_toggled, pkg)
            row.add_prefix(check)
            
            status = Gtk.Label(label="Gotowa")
            status.add_css_class('status-ready')
            row.add_suffix(status)
            
            self.listbox.append(row)
            
        self._update_selection_count()

    def _on_check_toggled(self, check, pkg):
        if check.get_active():
            self.selected.add(pkg.name)
        else:
            self.selected.discard(pkg.name)
        self._update_selection_count()

    def get_selected_packages(self):
        return [p for p in self.packages if p.name in self.selected]

    def _update_selection_count(self):
        self.count_label.set_text(f"Wybrano {len(self.selected)} z {len(self.packages)}")
        self.btn_next.set_sensitive(len(self.selected) > 0)

    def _on_select_all(self, button):
        child = self.listbox.get_first_child()
        while child:
            check = child.get_prefix()
            if isinstance(check, Gtk.CheckButton):
                check.set_active(True)
            child = child.get_next_sibling()

    def _on_deselect_all(self, button):
        child = self.listbox.get_first_child()
        while child:
            check = child.get_prefix()
            if isinstance(check, Gtk.CheckButton):
                check.set_active(False)
            child = child.get_next_sibling()

    def _on_next_clicked(self, btn):
        self.emit('packages-selected', self.get_selected_packages())
