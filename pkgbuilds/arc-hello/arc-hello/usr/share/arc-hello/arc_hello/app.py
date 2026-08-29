import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw

from arc_hello.theme import apply_css, BASE_CSS
from arc_hello.window import ArcHelloWindow

class ArcHelloApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.zcharka.ArcHello",
            flags=0
        )

    def do_startup(self):
        Adw.Application.do_startup(self)
        apply_css(BASE_CSS)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ArcHelloWindow(application=self)
        win.present()

def main():
    app = ArcHelloApplication()
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
