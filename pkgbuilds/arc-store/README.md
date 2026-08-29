# Arc Store

<p align="center">
  <img src="src/usr/share/arc-store/icon.png" alt="Arc Store" width="160" height="160"/>
</p>

**Arc Store** is a standalone graphical package manager for Arch Linux, built with Python, GTK4 and Libadwaita. It searches and manages both official repositories (`pacman`) and the AUR, with a review step for every AUR `PKGBUILD` before it's ever built.

This app started life as a widget (`y-package_manager.py`) for [Linexin Center](https://github.com/Petexy/Linexin-Center) and has been converted here into its own self-contained `Adw.Application`, following the same look, animation, icon-loading and sudo/authentication rules Linexin Center itself uses.

## 🌟 Key Features

* **Search & manage packages:** live search across official repos and (optionally) the AUR, with install/remove from a single list.
* **AUR build review:** clones the AUR package's git repo and shows you the `PKGBUILD` before anything is compiled or installed.
* **Package details:** icon, version, install status, and — when `webkitgtk-6.0` is installed — the relevant Arch Wiki page rendered right in the app.
* **Version switching:** install an older version of an already-installed package from the repo, the pacman cache, or the Arch Linux Archive.
* **Maintenance actions:** refresh repositories, clear the package cache, remove orphaned packages, and remove a stuck `db.lck` — all from one panel.
* **Safe root access:** every privileged pacman/makepkg call goes through a single `SudoManager` that validates the password with `sudo -S -v` before running anything, feeds it to `sudo` through a private named pipe (never a command-line argument, never written to disk), and forgets it as soon as the operation finishes.
* **Follows the system theme:** every color in the UI is a libadwaita alias (`@accent_color`, `@window_bg_color`, ...) — switching the system's theme or accent color updates Arc Store immediately, no restart needed.
* **GNOME and Plasma/Hyprland aware:** picks client-side or server-side window decorations depending on the desktop it's running under.

## 🛠️ Dependencies

* Python 3.8+
* GTK 4
* Libadwaita (`libadwaita-1`)
* PyGObject (`python-gobject`)

Optional:
* `flatpak` — lets Arc Store point you at GNOME Software/Discover from the first-run warning screen.
* `paru` — used automatically for AUR builds if installed; falls back to `makepkg -si` otherwise.
* `webkitgtk-6.0` — renders Arch Wiki pages in the package detail view; without it, Arc Store falls back to a plain-text summary.

## 📂 Directory Structure

Arc Store is packaged the same way as Linexin Center — a plain `usr/` tree meant to be installed with `PKGBUILD`, or copied straight onto the matching system paths:

```text
arc-store/
├── PKGBUILD
├── LICENSE
├── README.md
└── src/
    └── usr/
        ├── bin/
        │   └── arc-store                       # launcher, resolves and runs main.py
        └── share/
            ├── applications/
            │   └── github.petexy.arcstore.desktop
            └── arc-store/                       # everything the app needs to run
                ├── main.py                       # Adw.Application + main window
                ├── theme.py                      # shared CSS (apply_css)
                ├── package_manager.py             # the actual package manager UI/logic
                ├── icon.png                       # app icon, next to the rest of the .py files
                ├── widgets/                       # scale_bin, hover_breathe, compact_sidebar, stagger, icons
                ├── auth/                          # sudo_manager.py, dialogs.py
                └── i18n/                          # localizer.py + locales/{en_US,pl_PL}/strings.py
```

## 📦 Installing

```sh
makepkg -si
```

## 🧩 What changed going from widget to standalone app

* Wrapped in its own `Adw.Application`/`Adw.ApplicationWindow` (`main.py`) instead of being hosted inside Linexin Center's sidebar.
* `sudo_manager` and `translate_dialog` are now real imports (`auth.sudo_manager`, `i18n.localizer`) instead of names a host injects into the module at load time.
* Renamed `LinexinPackageManager` → `PackageManagerView`; `APP_NAME` is now `arc-store` (so its config file lives at `~/.config/arc-store/config.json`); the widget icon now points at Arc Store's own `icon.png`.
* Added a small hand-built "About Arc Store" window, since a standalone app needs one and a hosted widget didn't.
* Everything else — search, install/remove, AUR review, maintenance actions, adaptive layout — is unchanged from the original widget.

Not pulled in from the UI spec: `ScaleBin`/breakpoint-spring transitions, `CompactSidebarAnimator`, and `stagger_reveal`/`stagger_dismiss` are shipped in `widgets/` ready to use, but weren't force-fitted into the existing (and already working) adaptive layout and virtualized results list — retrofitting them would have meant restructuring already-solid code for a cosmetic difference. `load_icon()` and `HoverBreatheController` *are* wired up, on the About window's logo.
