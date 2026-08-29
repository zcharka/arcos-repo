import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

class HoverBreatheController:
    def __init__(self, shell: Gtk.Widget, image: Gtk.Image, *,
                 base=88.0, hover=96.0, press=78.0, ease=0.20):
        self.shell, self.image = shell, image
        self.base, self.hover_size, self.press_size, self.ease = base, hover, press, ease
        self.size = base
        self.target = base
        self.hovered = self.pressed = False
        self.tick_id = 0

        motion = Gtk.EventControllerMotion()
        motion.connect("enter", self._on_enter)
        motion.connect("leave", self._on_leave)
        shell.add_controller(motion)

        click = Gtk.GestureClick()
        click.set_button(0)
        click.connect("pressed", self._on_pressed)
        click.connect("released", self._on_released)
        shell.add_controller(click)

    def _retarget(self):
        self.target = self.press_size if self.pressed else (self.hover_size if self.hovered else self.base)
        if not self.tick_id:
            self.tick_id = self.shell.add_tick_callback(self._tick)

    def _on_enter(self, *_):    self.hovered = True;  self._retarget()
    def _on_leave(self, *_):    self.hovered = False; self.pressed = False; self._retarget()
    def _on_pressed(self, *_):  self.pressed = True;  self._retarget()
    def _on_released(self, *_): self.pressed = False; self._retarget()

    def _tick(self, widget, frame_clock):
        self.size += (self.target - self.size) * self.ease
        self.image.set_pixel_size(max(1, round(self.size)))
        if abs(self.target - self.size) < 0.35:
            self.size = self.target
            self.image.set_pixel_size(max(1, round(self.size)))
            self.tick_id = 0
            return False
        return True
