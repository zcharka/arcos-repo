"""
i18n/localizer.py — a small, no-compilation-step localization layer.

package_manager.py's main UI already goes through Python's own gettext via
``_()`` (see APP_NAME/LOCALE_DIR at the top of that file) — that's the
right place for full translations once real .po/.mo catalogs exist for
/usr/share/locale.

This module is the lighter-weight piece the UI spec calls for on top of
that: a plain Python-dict table per language, applied to a dialog's
heading/body/buttons right before it's shown, with no build step. It's
what backs the ``translate_dialog()`` calls already sprinkled through
package_manager.py.

Included out of the box: a pl_PL table covering every dialog Arc Store
actually shows through translate_dialog() (see locales/pl_PL/strings.py).
It activates automatically when the system locale is Polish.
"""

import os
import locale
import importlib.util
from pathlib import Path

from gi.repository import Gtk

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")


class Localizer:
    def __init__(self, locales_dir: str, fallback_lang="en_US"):
        self.fallback_lang = fallback_lang
        lang = locale.getlocale()[0] or os.environ.get("LANG", "")
        self.lang = lang.split(".")[0] if lang else fallback_lang
        self.tables = {}
        locales_path = Path(locales_dir)
        if locales_path.is_dir():
            for lang_dir in locales_path.iterdir():
                f = lang_dir / "strings.py"
                if lang_dir.is_dir() and f.exists():
                    spec = importlib.util.spec_from_file_location(f"strings_{lang_dir.name}", f)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.tables[lang_dir.name] = getattr(module, "translations", {})

    def tr(self, key: str) -> str:
        for lang in (self.lang, self.fallback_lang):
            if key in self.tables.get(lang, {}):
                return self.tables[lang][key]
        return key


_default_localizer = None


def get_localizer() -> Localizer:
    global _default_localizer
    if _default_localizer is None:
        _default_localizer = Localizer(LOCALES_DIR)
    return _default_localizer


def _translate_widget_tree(widget, localizer: Localizer):
    if isinstance(widget, Gtk.Label):
        widget.set_label(localizer.tr(widget.get_label()))
    elif isinstance(widget, Gtk.Button) and widget.get_label():
        widget.set_label(localizer.tr(widget.get_label()))
    child = widget.get_first_child()
    while child is not None:
        _translate_widget_tree(child, localizer)
        child = child.get_next_sibling()


def translate_dialog(dialog):
    """Translate an Adw.MessageDialog's heading/body/extra-child tree in
    place, using the default Localizer. This is the single-argument form
    that package_manager.py calls throughout — it binds a shared Localizer
    instance internally so every call site doesn't have to pass one in."""
    localizer = get_localizer()
    if dialog.get_heading():
        dialog.set_heading(localizer.tr(dialog.get_heading()))
    if dialog.get_body():
        dialog.set_body(localizer.tr(dialog.get_body()))
    extra = dialog.get_extra_child()
    if extra is not None:
        _translate_widget_tree(extra, localizer)
