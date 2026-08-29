import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk

BASE_CSS = """
/* Nagłówek zlewający się z tłem okna */
headerbar.flat {
    min-height: 0; padding-top: 3px; padding-bottom: 3px;
    background: transparent; border: none; box-shadow: none;
}
.dim-label { opacity: 0.65; }

/* Stan zablokowany podczas operacji uprzywilejowanej (GTK4 :disabled) */
widget:disabled { opacity: 0.35; }
.command-locked { background: alpha(@warning_color, 0.1); }

/* Styl sekcji NOWE i kart aplikacji wzorowany na Linexin Hello */
.linexin-new-section {
    background-color: alpha(@accent_bg_color, 0.08);
    border: 1px solid alpha(@accent_bg_color, 0.30);
    border-radius: 14px;
    padding: 10px;
}
.linexin-new-card {
    border: 1px solid alpha(@accent_bg_color, 0.45);
}
.linexin-app-grid > flowboxchild {
    border-radius: 12px;
    padding: 0;
}
.linexin-app-grid > flowboxchild:hover {
    border-radius: 12px;
}
.linexin-app-card {
    border-radius: 12px;
}
.linexin-new-badge {
    background-color: @accent_bg_color;
    color: @accent_fg_color;
    border-radius: 9999px;
    padding: 2px 10px;
    font-size: 0.68em;
    font-weight: 800;
}
.linexin-card-action {
    border-radius: 9999px;
    padding-left: 16px;
    padding-right: 16px;
    font-weight: bold;
}

/* Console Log TextView */
.console {
    font-family: monospace;
    font-size: 13px;
    background-color: #1e1e1e;
    color: #e0e0e0;
    border-radius: 8px;
    padding: 12px;
}

/* Header autostart switch */
.header-autostart-box {
    margin-right: 8px;
}
.header-autostart-label {
    font-size: 12px;
    font-weight: bold;
    opacity: 0.85;
}
"""

def apply_css(css: str = BASE_CSS):
    """Applies CSS provider to default Gdk Display."""
    provider = Gtk.CssProvider()
    if hasattr(provider, "load_from_string"):
        provider.load_from_string(css)
    else:
        provider.load_from_data(css.encode("utf-8"))
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
