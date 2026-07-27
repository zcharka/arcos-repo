import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GObject, Adw, GLib, Pango
from .common import create_pill_button

class ProgressScreen(Gtk.Box):
    __gsignals__ = {
        'operation-complete': (GObject.SignalFlags.RUN_FIRST, None, (bool, str)),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(10)
        self.set_margin_top(20)
        
        clamp = Adw.Clamp(maximum_size=800)
        self.append(clamp)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        clamp.set_child(main_box)
        
        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_halign(Gtk.Align.CENTER)
        self.spinner = Gtk.Spinner()
        self.spinner.start()
        header_box.append(self.spinner)
        title_lbl = Gtk.Label()
        title_lbl.set_markup('<span size="x-large" weight="bold">Aktualizowanie ArcOS</span>')
        header_box.append(title_lbl)
        main_box.append(header_box)
        
        self.step_desc = Gtk.Label(label="Przygotowanie...")
        self.step_desc.add_css_class('dim-label')
        main_box.append(self.step_desc)
        
        self.progress_bar = Gtk.ProgressBar()
        main_box.append(self.progress_bar)
        
        self.time_label = Gtk.Label(label="00:00")
        self.time_label.add_css_class('dim-label')
        main_box.append(self.time_label)
        
        # Steps
        self.steps_list = Gtk.ListBox()
        self.steps_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.steps_list.add_css_class('boxed-list')
        main_box.append(self.steps_list)
        
        # Log view
        self.log_rev = Gtk.Revealer()
        
        log_frame = Gtk.Frame()
        log_frame.add_css_class('view')
        
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_min_content_height(200)
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.buffer = self.log_view.get_buffer()
        self.buffer.create_tag("command", foreground="#62a0ea", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("success", foreground="#57e389")
        self.buffer.create_tag("error", foreground="#ff7b63")
        self.buffer.create_tag("info", foreground="#f6d32d")
        
        log_scroll.set_child(self.log_view)
        log_frame.set_child(log_scroll)
        self.log_rev.set_child(log_frame)
        main_box.append(self.log_rev)
        
        self.btn_toggle_log = Gtk.ToggleButton(label="Pokaż logi")
        self.btn_toggle_log.set_halign(Gtk.Align.CENTER)
        self.btn_toggle_log.connect('toggled', self._on_log_toggled)
        main_box.append(self.btn_toggle_log)
        
        # Cancel button
        self.btn_cancel = Gtk.Button(label="Anuluj")
        self.btn_cancel.set_halign(Gtk.Align.CENTER)
        self.btn_cancel.add_css_class('destructive-action')
        main_box.append(self.btn_cancel)
        
        self.elapsed_seconds = 0
        self.timer_id = 0
        self.step_rows = []

    def _on_log_toggled(self, btn):
        self.log_rev.set_reveal_child(btn.get_active())
        btn.set_label("Ukryj logi" if btn.get_active() else "Pokaż logi")

    def start_timer(self):
        self.elapsed_seconds = 0
        self.timer_id = GLib.timeout_add(1000, self._update_timer)

    def stop_timer(self):
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = 0

    def _update_timer(self):
        self.elapsed_seconds += 1
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        self.time_label.set_text(f"{mins:02d}:{secs:02d}")
        return True

    def set_steps(self, steps):
        self.step_rows = []
        while child := self.steps_list.get_first_child():
            self.steps_list.remove(child)
            
        for s in steps:
            row = Adw.ActionRow(title=s)
            icon = Gtk.Image.new_from_icon_name('radio-symbolic')
            row.add_prefix(icon)
            self.steps_list.append(row)
            self.step_rows.append((row, icon))

    def update_step(self, index, status):
        if index < 0 or index >= len(self.step_rows):
            return
            
        row, icon = self.step_rows[index]
        if status == 'pending':
            icon.set_from_icon_name('radio-symbolic')
        elif status == 'running':
            spinner = Gtk.Spinner()
            spinner.start()
            row.remove(icon)
            row.add_prefix(spinner)
            self.step_rows[index] = (row, spinner)
        elif status == 'done':
            if isinstance(icon, Gtk.Spinner):
                row.remove(icon)
                icon = Gtk.Image()
                row.add_prefix(icon)
                self.step_rows[index] = (row, icon)
            icon.set_from_icon_name('emblem-ok-symbolic')
            icon.add_css_class('status-ready')
        elif status == 'error':
            if isinstance(icon, Gtk.Spinner):
                row.remove(icon)
                icon = Gtk.Image()
                row.add_prefix(icon)
                self.step_rows[index] = (row, icon)
            icon.set_from_icon_name('process-stop-symbolic')
            icon.add_css_class('status-error')
        elif status == 'warning':
            if isinstance(icon, Gtk.Spinner):
                row.remove(icon)
                icon = Gtk.Image()
                row.add_prefix(icon)
                self.step_rows[index] = (row, icon)
            icon.set_from_icon_name('dialog-warning-symbolic')
            icon.add_css_class('status-warning')

    def set_progress(self, fraction):
        self.progress_bar.set_fraction(fraction)

    def set_current_operation(self, text):
        self.step_desc.set_text(text)

    def append_log(self, text, tag=None):
        end_iter = self.buffer.get_end_iter()
        if tag:
            self.buffer.insert_with_tags_by_name(end_iter, text + "\n", tag)
        else:
            self.buffer.insert(end_iter, text + "\n")
        
        # Scroll to bottom
        mark = self.buffer.create_mark(None, self.buffer.get_end_iter(), False)
        self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
