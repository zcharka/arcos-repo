import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, Graphene

class ScaleBin(Gtk.Widget):
    def __init__(self):
        super().__init__()
        self._child = None
        self._scale = 1.0

    def set_child(self, child):
        if child is self._child:
            return
        if self._child is not None:
            self._child.unparent()
        self._child = child
        if child is not None:
            child.set_parent(self)

    def set_scale(self, scale):
        if scale != self._scale:
            self._scale = scale
            self.queue_draw()

    def do_measure(self, orientation, for_size):
        if self._child is None:
            return (0, 0, -1, -1)
        return self._child.measure(orientation, for_size)

    def do_size_allocate(self, width, height, baseline):
        if self._child is not None:
            self._child.allocate(width, height, baseline, None)

    def do_snapshot(self, snapshot):
        if self._child is None:
            return
        if self._scale == 1.0:
            self.snapshot_child(self._child, snapshot)
            return
        cx, cy = self.get_width() * 0.5, self.get_height() * 0.5
        snapshot.save()
        snapshot.translate(Graphene.Point().init(cx, cy))
        snapshot.scale(self._scale, self._scale)
        snapshot.translate(Graphene.Point().init(-cx, -cy))
        self.snapshot_child(self._child, snapshot)
        snapshot.restore()

    def do_dispose(self):
        if self._child is not None:
            self._child.unparent()
            self._child = None
        Gtk.Widget.do_dispose(self)
