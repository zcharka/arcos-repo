import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

ICON_SIZE = 32

def load_icon(icon_path_or_name: str, size: int = ICON_SIZE,
              fallback: str = "application-x-addon-symbolic") -> Gtk.Image:
    if icon_path_or_name and os.path.isfile(icon_path_or_name):
        try:
            if icon_path_or_name.lower().endswith(".svg"):
                image = Gtk.Image()
                image.set_from_file(icon_path_or_name)
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path_or_name, size, size)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                image = Gtk.Image.new_from_paintable(texture)
            image.set_pixel_size(size)
            return image
        except Exception:
            pass
    image = Gtk.Image.new_from_icon_name(icon_path_or_name or fallback)
    image.set_pixel_size(size)
    return image
