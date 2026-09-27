import os

CHANGELOG_DIR = "/usr/share/changelog"
LATEST_FILE = os.path.join(CHANGELOG_DIR, "latest.txt")

FALLBACK_LATEST = """===================================================
                ArcOS Changelog
===================================================
Wersja: Najnowsza wersja ArcOS Rolling

Nowości i usprawnienia:
- Wprowadzono nową aplikację Arc Hello (GTK4 + Libadwaita)
- Dodano integrację ze Steam (Big Picture toggle, Gamemode, Gamescope)
- Usprawniono instalator sesji X11 dla różnych środowisk graficznych
- Dodano menedżer vtrt-manager oraz integrację z Arc Store
- Wdrożono Windows-style konfigurator domyślnych aplikacji (xdg-mime)
- Poprawiono ogólną wydajność systemu oraz pakietów
==================================================="""

def get_changelog_files() -> list[tuple[str, str]]:
    results = []

    if os.path.exists(LATEST_FILE):
        results.append(("najnowsza wersja", LATEST_FILE))
    else:
        results.append(("najnowsza wersja", "mock_latest"))

    if os.path.exists(CHANGELOG_DIR) and os.path.isdir(CHANGELOG_DIR):
        try:
            for fname in sorted(os.listdir(CHANGELOG_DIR), reverse=True):
                full_path = os.path.join(CHANGELOG_DIR, fname)
                if fname != "latest.txt" and os.path.isfile(full_path):
                    results.append((fname, full_path))
        except Exception as e:
            print(f"Error reading changelog directory: {e}")

    return results

def read_changelog_content(filepath: str) -> str:
    if filepath == "mock_latest":
        return FALLBACK_LATEST
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception as e:
        return f"Nie udało się odczytać pliku: {e}"
    return FALLBACK_LATEST
