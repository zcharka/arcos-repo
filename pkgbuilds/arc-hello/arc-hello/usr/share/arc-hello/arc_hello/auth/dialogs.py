import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from arc_hello.auth.sudo_manager import get_sudo_manager

def prompt_password(parent_window, message: str, on_success, primary_label="Uwierzytelnij"):
    manager = get_sudo_manager()

    dialog = Adw.MessageDialog(
        heading="Wymagane Uwierzytelnienie",
        body=message,
        transient_for=parent_window
    )
    dialog.add_response("cancel", "Anuluj")
    dialog.add_response("go", primary_label)
    dialog.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("go")

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    entry = Gtk.PasswordEntry(placeholder_text="Hasło użytkownika / root")
    box.append(entry)
    dialog.set_extra_child(box)

    def on_response(dlg, response):
        if response == "go":
            pwd = entry.get_text()
            if pwd and manager.validate_password(pwd):
                manager.set_password(pwd)
                on_success()
            else:
                err = Adw.MessageDialog(
                    heading="Błąd Uwierzytelniania",
                    body="Wprowadzono niepoprawne hasło.",
                    transient_for=parent_window
                )
                err.add_response("ok", "OK")
                err.present()
        dlg.close()

    dialog.connect("response", on_response)
    entry.connect("activate", lambda *_: dialog.response("go"))
    dialog.present()
