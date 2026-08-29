# Polish translations for the dialogs package_manager.py passes through
# translate_dialog(). Keys are the exact English source strings (as
# produced by package_manager.py's own gettext calls, since no compiled
# .mo catalog ships by default) — scoped to what those dialogs can
# actually show, including the couple of strings assembled with
# .format() where every possible resulting value is known ahead of time.
translations = {
    "No Versions Found": "Nie znaleziono innych wersji",
    "Change Version": "Zmień wersję",
    "Update Failed": "Aktualizacja nie powiodła się",
    "No Orphans Found": "Nie znaleziono osieroconych pakietów",
    "Remove Orphan Packages": "Usuń osierocone pakiety",
    "Authentication Required": "Wymagane uwierzytelnienie",
    "Authentication Failed": "Uwierzytelnienie nie powiodło się",

    "There are no orphan packages to remove.": "Nie ma żadnych osieroconych pakietów do usunięcia.",
    "Incorrect sudo password. Please try again.": "Błędne hasło sudo. Spróbuj ponownie.",
    "Repository update failed": "Aktualizacja repozytoriów nie powiodła się",
    "Please enter your password to update repositories.": "Podaj hasło, aby zaktualizować repozytoria.",
    "Please enter your password to clear the package cache.": "Podaj hasło, aby wyczyścić pamięć podręczną pakietów.",
    "Please enter your password to remove orphan packages.": "Podaj hasło, aby usunąć osierocone pakiety.",
    "Please enter your password to remove the database lock file.": "Podaj hasło, aby usunąć plik blokady bazy danych.",
    "Please enter your password to install this package.": "Podaj hasło, aby zainstalować ten pakiet.",
    "Please enter your password to remove this package.": "Podaj hasło, aby usunąć ten pakiet.",
    "Incorrect password.": "Nieprawidłowe hasło.",

    "OK": "OK",
    "Cancel": "Anuluj",
    "Install Selected": "Zainstaluj wybraną",
    "Remove All": "Usuń wszystkie",
    "Unlock": "Odblokuj",
}
