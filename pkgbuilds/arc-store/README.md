# Arc Store

<p align="center">
  <img src="src/usr/share/arc-store/icon.png" alt="Arc Store" width="160" height="160"/>
</p>

**Arc Store** is a standalone graphical package manager for Arch Linux, built with Python, GTK4 and Libadwaita. It searches and manages official repositories (`pacman`), the AUR, and Flatpak, with a review step for every AUR `PKGBUILD` before it's ever built.

This app started life as a widget (`y-package_manager.py`) for [Linexin Center](https://github.com/Petexy/Linexin-Center) and has been converted here into its own self-contained `Adw.Application`, following the same look, animation, icon-loading and sudo/authentication rules Linexin Center itself uses. Packaged and maintained separately from Linexin Center by [zcharka](https://github.com/zcharka).

## 🌟 Key Features

* **Installed / Discover tabs:** "Discover" searches official repos, the AUR (optional), and Flatpak for things to install. "Installed" browses and searches only what's already on the system — pacman, AUR/`makepkg -si`, and Flatpak alike — with no AUR toggle to worry about there.
* **Flatpak included as a real source**, not just a mention in the first-run warning dialog. Flatpak entries get their own badge, show their friendly name instead of the raw app ID, and install/remove with `--user` scope — no root needed, so no password prompt either.
* **Search & manage packages:** live search, with install/remove from a single list. Typing a name that isn't in any repo (e.g. something `makepkg -si`'d from a private or since-removed source) still finds it via the local database, on both tabs.
* **AUR build review:** clones the AUR package's git repo and shows you the `PKGBUILD` before anything is compiled or installed.
* **Package details:** icon, version, install status, and — when `webkitgtk-6.0` is installed — the relevant Arch Wiki page rendered right in the app (pacman/AUR packages only; Flatpak entries skip this and version-switching, neither of which applies to them).
* **Version switching:** install an older version of an already-installed pacman package from the repo, the pacman cache, or the Arch Linux Archive.
* **Maintenance actions:** refresh repositories, clear the package cache, remove orphaned packages, and remove a stuck `db.lck` — all from one panel.
* **Safe root access:** every privileged pacman/makepkg call goes through a single `SudoManager` that validates the password with `sudo -S -v` before running anything, feeds it to `sudo` through a private named pipe (never a command-line argument, never written to disk), and forgets it as soon as the operation finishes.
* **Follows the system theme:** every color in the UI is a libadwaita alias (`@accent_color`, `@window_bg_color`, ...) — switching the system's theme or accent color updates Arc Store immediately, no restart needed.
* **Translated UI:** every string in the app (not just dialogs) is looked up in `i18n/locales/<lang>/strings.py` at display time — Polish ships out of the box and activates automatically under a Polish locale.

## 🛠️ Dependencies

* Python 3.8+
* GTK 4
* Libadwaita (`libadwaita-1`)
* PyGObject (`python-gobject`)
* `desktop-file-utils`, `hicolor-icon-theme` (for the `.desktop`/icon cache refresh on install)

Optional:
* `flatpak` — powers the Flatpak side of both tabs; without it, Arc Store just shows pacman/AUR results, same as before.
* `paru` — used automatically for AUR builds if installed; falls back to `makepkg -si` otherwise.
* `webkitgtk-6.0` — renders Arch Wiki pages in the package detail view; without it, Arc Store falls back to a plain-text summary.

## 📂 Directory Structure

Arc Store is packaged the same way as Linexin Center — a plain `usr/` tree meant to be installed with `PKGBUILD`, or copied straight onto the matching system paths:

```text
arc-store/
├── PKGBUILD
├── arc-store.install                    # post-install: refresh desktop-file + icon caches
├── LICENSE
├── README.md
└── src/
    └── usr/
        ├── bin/
        │   └── arc-store                       # launcher, resolves and runs main.py
        └── share/
            ├── applications/
            │   └── github.zcharka.arcstore.desktop
            ├── icons/hicolor/256x256/apps/
            │   └── github.zcharka.arcstore.png  # for the shell/taskbar — matches the .desktop Icon= name
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

## 🐞 Fixed since the first cut

* **Startup crash on every desktop:** `main.py` briefly tried to call `set_child()` on the `Adw.ApplicationWindow` for a Plasma/Hyprland-specific code path. Libadwaita doesn't support that at all — it's a hard `Adwaita-ERROR` abort, not a warning, and it fired regardless of desktop. Removed; `set_content()` is now used unconditionally, which is correct (and works fine) on GNOME, Plasma, Cinnamon, Hyprland, or anything else.
* **NVIDIA + GTK4's Vulkan renderer:** `GSK_RENDERER=gl` is now set as a default (not forced — `setdefault`, so it never overrides a value you set yourself) in both the launcher and `main.py`, working around a documented NVIDIA-proprietary-driver crash in GTK4's newer default renderer.
* Invalid CSS pseudo-class (`widget:insensitive`, not a real GTK4 selector) fixed to `widget:disabled`.
* The WebKit view for the Arch Wiki panel is now built on first use instead of at startup, so the app doesn't spin up a full WebKit process before its window even exists.

## 🆕 Installed/Discover split, translations, and desktop integration

* **Two tabs, one search bar.** "Discover" (default) searches repos/AUR/Flatpak to find things to install; empty query shows a prompt instead of dumping every installed package. "Installed" browses/searches the local database only — includes AUR/`makepkg -si` and Flatpak packages automatically, no separate handling needed — and hides the "Search AUR" checkbox since it doesn't apply there.
* **`_()` is no longer a no-op.** It was bound to real `gettext.gettext()`, which needs a compiled `.mo` catalog to translate anything — none shipped, so every non-dialog string (search bar, buttons, the Actions panel) was always English regardless of system locale, even though the handful of dialogs routed through `translate_dialog()` translated fine. `_` is now bound to the same `i18n.localizer` table dialogs already used, so the whole app translates consistently. `gettext.bindtextdomain`/`textdomain` are left in place as inert scaffolding for anyone who wants a real `.po`/`.mo` catalog later.
* **Polish translation table greatly expanded** (~110 strings, covering the persistent UI, not just dialogs).
* **App icon and `.desktop` visibility.** The icon is now also installed to `/usr/share/icons/hicolor/256x256/apps/`, and the `.desktop` file's `Icon=` references it by theme name instead of an absolute path — the more broadly-supported form for app-grid/taskbar/alt-tab icon lookups. `arc-store.install` runs `update-desktop-database` and `gtk-update-icon-cache` on install/upgrade/remove so both take effect immediately rather than waiting on the next unrelated cache refresh.

## 🆕 Flatpak support, and icon+label tabs

* **Flatpak is now a real source**, not just a mention in the first-run warning dialog. "Discover" searches `flatpak search` alongside repos/AUR; "Installed" lists `flatpak list --app --user` alongside the local pacman database. Flatpak entries get their own blue badge (matching the existing red AUR badge), show their friendly name instead of the app ID, and skip the pacman/AUR-only bits of the detail page (version switching, the Arch Wiki panel) that don't apply to them.
* **No sudo prompt for Flatpak actions.** Installs/removals use `--user` scope, which Flatpak doesn't need root for at all — so those go straight to the same progress view pacman actions use, just without ever touching `SudoManager`.
* **Installed/Discover tabs now have icons** (`Adw.ButtonContent`, matching the reference screenshot's icon+label style) instead of plain text.

Not done yet: opening a `.pkg.tar.zst` file to install it straight from Arc Store. That needs its own MIME-type registration and a dedicated "install this local file" view — scoped for a follow-up rather than bolted on here.

## 🔧 Other notes

* Minimum window size is locked to Arc Store's normal working size (1099×728) — it can be made larger, not smaller.
* App icon and GitHub links point at [zcharka](https://github.com/zcharka)'s own fork/packaging of this app, not the upstream Linexin Center project.
