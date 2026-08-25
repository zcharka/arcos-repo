#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import os
import gettext
import locale
import socket
import subprocess
import json
import urllib.request

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, GLib


class DEPicker(Gtk.Box):

    def __init__(self, on_continue_callback=None, **kwargs):
        """
        Initialize the widget.

        Args:
            on_continue_callback: Optional callback function to call when Continue button is clicked
            **kwargs: Additional arguments passed to Gtk.Box
        """
        super().__init__(**kwargs)

        print("DEBUG: Starting two box selection widget")

        # Store callback
        self.on_continue_callback = on_continue_callback
        self.selected_option = 0  # Default to first row (Plasma)
        self.animation_played = False

        # Check internet connectivity
        self.has_internet = self.check_internet_connection()
        print(f"DEBUG: Internet connection status: {self.has_internet}")

        # Per-option "Tryb Big Picture" toggle state, keyed by option index
        self.bigpicture_enabled = {}

        # Basic widget setup
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(8)

        self.set_valign(Gtk.Align.FILL)
        self.set_vexpand(True)

        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_margin_top(5)
        self.set_margin_bottom(5)

        # Setup CSS first
        self.setup_css()

        # Title
        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Choose Your Environment</span>')
        title.set_halign(Gtk.Align.CENTER)
        title.set_margin_bottom(14)
        self.append(title)

        # Get script directory for icons
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_dir = script_dir

        # Define the six environment options
        self.options = [
            {
                "key": "plasma",
                "name": "Plasma",
                "description": "Klasyczny pulpit KDE Plasma. Zainstalowany steam, discord, lutris oraz heroic games launcher.",
                "icon": "plasma.png",
                "requires_internet": False,
                "bigpicture_capable": True,
            },
            {
                "key": "gnome",
                "name": "GNOME",
                "description": "Pulpit GNOME z rozszerzeniami ArcOS.",
                "icon": "gnome.png",
                "requires_internet": False,
                "bigpicture_capable": True,
            },
            {
                "key": "hyprland",
                "name": "Hyprland",
                "description": "Kafelkowy kompozytor Wayland (Hyprland) skonfigurowany pod ArcOS.",
                "icon": "hyprland.png",
                "requires_internet": False,
                "bigpicture_capable": True,
            },
            {
                "key": "cinnamon",
                "name": "Cinnamon",
                "description": "Lekki, klasyczny pulpit Cinnamon (znany z Linux Mint).",
                "icon": "cinnamon.png",
                "requires_internet": False,
                "bigpicture_capable": True,
            },
            {
                "key": "none",
                "name": "Brak środowiska graficznego",
                "description": "Instalacja bez pulpitu i menedżera logowania - system startuje w konsoli (TTY). Zalecane dla serwerów lub zaawansowanych użytkowników.",
                "icon": "none.png",
                "requires_internet": False,
                "bigpicture_capable": False,
            },
        ]

        # --- Main split layout: list on the left, details on the right ---
        split_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        split_box.set_vexpand(True)
        split_box.add_css_class("de_split_box")

        # Left: scrolled list of options
        list_scroller = Gtk.ScrolledWindow()
        list_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        list_scroller.set_size_request(240, -1)
        list_scroller.set_vexpand(True)
        list_scroller.add_css_class("de_list_scroller")

        self.option_list = Gtk.ListBox()
        self.option_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.option_list.add_css_class("de_option_list")
        list_scroller.set_child(self.option_list)

        self.list_rows = []
        for i, option in enumerate(self.options):
            row = self.create_list_row(option, i)
            self.option_list.append(row)
            self.list_rows.append(row)

        split_box.append(list_scroller)

        # Right: detail panel as an animated Gtk.Stack (one page per option)
        self.detail_stack = Gtk.Stack()
        self.detail_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.detail_stack.set_transition_duration(220)
        self.detail_stack.set_hexpand(True)
        self.detail_stack.set_vexpand(True)
        self.detail_stack.add_css_class("de_detail_panel")

        self.bigpicture_switches = {}
        self.detail_pages = {}
        for i, option in enumerate(self.options):
            page = self.build_detail_page(option, i)
            self.detail_stack.add_named(page, str(i))
            self.detail_pages[i] = page

        split_box.append(self.detail_stack)

        self.append(split_box)

        # Only NOW connect the selection signal and select the first row - everything
        # the handler touches (detail_stack, bigpicture_switches, detail_pages) already
        # exists at this point. GTK auto-selects row 0 as soon as it's appended to a
        # SINGLE-selection ListBox; connecting the signal earlier than this made that
        # auto-selection fire on_row_selected -> commit_selection before detail_stack
        # existed, crashing the constructor with an AttributeError.
        self.option_list.connect("row-selected", self.on_row_selected)
        self.option_list.select_row(self.list_rows[0])

        # Add checkboxes for optional features
        checkbox_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        checkbox_box.set_halign(Gtk.Align.CENTER)
        checkbox_box.set_margin_top(6)

        # Updates checkbox
        self.update_check = Gtk.CheckButton(label="Install system updates during installation")
        self.update_check.set_active(self.has_internet)
        self.update_check.set_sensitive(self.has_internet)
        self.update_check.add_css_class("option_checkbox")
        if not self.has_internet:
            self.update_check.set_tooltip_text("Internet connection required")
        checkbox_box.append(self.update_check)

        self.append(checkbox_box)

        # Package selections: None means "not customized, use all defaults"
        self.selected_packages = None
        self._cached_packages = None

        navigation_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        navigation_btns.set_halign(Gtk.Align.CENTER)
        navigation_btns.set_margin_top(6)

        # Continue button - smaller
        self.continue_btn = Gtk.Button()
        self.continue_btn.set_label("Continue")
        self.continue_btn.add_css_class("suggested-action")
        self.continue_btn.add_css_class("continue_button")
        self.continue_btn.set_size_request(140, 50)
        self.continue_btn.set_halign(Gtk.Align.CENTER)
        self.continue_btn.connect("clicked", self.on_continue_clicked)


        self.back_btn = Gtk.Button()
        self.back_btn.set_label("Back")
        self.back_btn.add_css_class("back_button")
        self.back_btn.set_size_request(140, 50)
        self.back_btn.set_halign(Gtk.Align.CENTER)
        self.back_btn.connect("clicked", self.on_continue_clicked)

        # Add hover effects to continue button
        continue_hover = Gtk.EventControllerMotion()
        continue_hover.connect("enter", lambda c, x, y: self.continue_btn.add_css_class("pulse-animation"))
        continue_hover.connect("leave", lambda c: self.continue_btn.remove_css_class("pulse-animation"))
        self.continue_btn.add_controller(continue_hover)

        # Add hover effects to back button
        back_hover = Gtk.EventControllerMotion()
        back_hover.connect("enter", lambda c, x, y: self.back_btn.add_css_class("pulse-animation"))
        back_hover.connect("leave", lambda c: self.back_btn.remove_css_class("pulse-animation"))
        self.back_btn.add_controller(back_hover)

        navigation_btns.append(self.back_btn)
        navigation_btns.append(self.continue_btn)
        self.append(navigation_btns)

        # Animation setup
        self.set_opacity(0)
        self.connect("map", self.on_widget_mapped)

        print("DEBUG: Two box selection widget initialization complete")

    # ... [Rest of the file remains exactly the same] ...

    def check_internet_connection(self):
        """Check if internet connection is available"""
        # Try multiple methods to check connectivity

        # Method 1: Check if we can resolve a DNS name
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print("DEBUG: Internet check via DNS succeeded")
            return True
        except (socket.error, socket.timeout):
            print("DEBUG: Internet check via DNS failed")

        # Method 2: Try to open a connection to a reliable host
        try:
            urllib.request.urlopen('http://clients3.google.com/generate_204', timeout=3)
            print("DEBUG: Internet check via HTTP succeeded")
            return True
        except:
            print("DEBUG: Internet check via HTTP failed")

        print("DEBUG: No internet connection detected")
        return False

    def create_list_row(self, option, index):
        """Create a single sidebar row (icon from images/ + name), Linexin-Center style."""
        row = Gtk.ListBoxRow()
        row.option_index = index
        row.add_css_class("de_list_row")

        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_box.set_margin_top(8)
        row_box.set_margin_bottom(8)
        row_box.set_margin_start(10)
        row_box.set_margin_end(10)

        icon = self.load_images_dir_icon(option["icon"], size=28)
        row_box.append(icon)

        name_label = Gtk.Label(label=option["name"])
        name_label.set_halign(Gtk.Align.START)
        name_label.set_hexpand(True)
        row_box.append(name_label)

        row.set_child(row_box)
        return row

    def load_images_dir_icon(self, filename, size=28):
        """Load an icon strictly from <script_dir>/images/<filename> (used for the
        small sidebar row icons). Falls back to an emoji tile if not found there."""
        path = os.path.join(self.script_dir, "images", filename)
        if os.path.isfile(path) and os.access(path, os.R_OK):
            try:
                texture = Gdk.Texture.new_from_filename(path)
                icon = Gtk.Picture.new_for_paintable(texture)
                icon.set_content_fit(Gtk.ContentFit.CONTAIN)
                icon.set_can_shrink(True)
                icon.set_size_request(size, size)
                icon.add_css_class("option_icon_image")
                return icon
            except Exception as e:
                print(f"DEBUG: Failed to load {path}: {e}")

        fallback = Gtk.Box()
        fallback.set_size_request(size, size)
        fallback.add_css_class("large_fallback_icon")
        fallback.set_halign(Gtk.Align.CENTER)
        fallback.set_valign(Gtk.Align.CENTER)
        fallback_label = Gtk.Label(label="🖥️")
        fallback_label.add_css_class("fallback_emoji")
        overlay = Gtk.Overlay()
        overlay.set_child(fallback)
        overlay.add_overlay(fallback_label)
        return overlay

    def load_option_icon(self, option, size=120):
        """Load an option's icon at the given pixel size, falling back to an emoji tile."""
        icon_paths = [
            os.path.join(self.script_dir, option["icon"]),
            os.path.join(self.script_dir, "images", option["icon"]),
        ]
        for path in icon_paths:
            if os.path.isfile(path) and os.access(path, os.R_OK):
                try:
                    texture = Gdk.Texture.new_from_filename(path)
                    icon = Gtk.Picture.new_for_paintable(texture)
                    icon.set_content_fit(Gtk.ContentFit.CONTAIN)
                    icon.set_can_shrink(True)
                    icon.set_size_request(size, size)
                    icon.add_css_class("option_icon_image")
                    return icon
                except Exception as e:
                    print(f"DEBUG: Failed to load {path}: {e}")

        # Fallback: emoji tile
        fallback = Gtk.Box()
        fallback.set_size_request(size, size)
        fallback.add_css_class("large_fallback_icon")
        fallback.set_halign(Gtk.Align.CENTER)
        fallback.set_valign(Gtk.Align.CENTER)

        fallback_label = Gtk.Label(label="🖥️")
        fallback_label.add_css_class("fallback_emoji")

        overlay = Gtk.Overlay()
        overlay.set_child(fallback)
        overlay.add_overlay(fallback_label)
        return overlay

    def on_row_selected(self, listbox, row):
        """Called whenever the sidebar selection changes (including programmatically)."""
        if row is None:
            return
        index = row.option_index
        option = self.options[index]

        self.commit_selection(index)

    def commit_selection(self, index):
        """Actually apply a selection."""
        print(f"DEBUG: Option {index} selected: {self.options[index]['name']}")
        self.selected_option = index
        self.detail_stack.set_visible_child_name(str(index))

    def build_detail_page(self, option, index):
        """Build the (static) detail page for one option, used as a Gtk.Stack child.
        Built once at startup so switching between options animates instead of
        rebuilding widgets from scratch."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_hexpand(True)
        page.set_vexpand(True)
        page.set_halign(Gtk.Align.FILL)
        page.set_valign(Gtk.Align.CENTER)
        page.set_margin_start(28)
        page.set_margin_end(12)

        image = self.load_option_icon(option, size=180)
        image.set_halign(Gtk.Align.CENTER)
        page.append(image)

        name_label = Gtk.Label()
        name_label.set_markup(f'<span weight="bold" size="x-large">{option["name"]}</span>')
        name_label.set_halign(Gtk.Align.CENTER)
        page.append(name_label)

        desc_label = Gtk.Label()
        desc_label.set_text(option["description"])
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.add_css_class("option_description")
        page.append(desc_label)

        # "Requires Internet" notice - built once, visibility toggled later by refresh_ui
        notice_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        notice_box.set_halign(Gtk.Align.CENTER)
        notice_box.set_margin_top(5)
        warning_icon = Gtk.Label(label="⚠️")
        notice_box.append(warning_icon)
        notice_label = Gtk.Label()
        notice_label.set_markup('<span size="small" weight="bold">Requires Internet</span>')
        notice_label.add_css_class("internet_notice")
        notice_box.append(notice_label)
        notice_box.set_visible(bool(option.get("requires_internet") and not self.has_internet))
        page.append(notice_box)
        self.internet_notices = getattr(self, "internet_notices", {})
        self.internet_notices[index] = (notice_box, option.get("requires_internet", False))

        # "Tryb Big Picture" switch - hidden when bigpicture_capable is False (e.g. "none")
        if option.get("bigpicture_capable"):
            switch_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            switch_row.set_halign(Gtk.Align.CENTER)
            switch_row.set_margin_top(14)

            switch_label = Gtk.Label(label="Tryb Big Picture")
            switch_row.append(switch_label)

            switch = Gtk.Switch()
            switch.set_active(self.bigpicture_enabled.get(index, False))
            switch.set_valign(Gtk.Align.CENTER)
            switch.connect("state-set", self.on_bigpicture_switch_toggled, index)
            switch_row.append(switch)
            self.bigpicture_switches[index] = switch

            switch_row.set_tooltip_text(
                "Steam odpali się automatycznie w trybie Big Picture zaraz po starcie tego środowiska."
            )
            page.append(switch_row)

        return page

    def on_bigpicture_switch_toggled(self, switch, state, index):
        self.bigpicture_enabled[index] = state
        print(f"DEBUG: Big Picture autostart for option {index} set to {state}")
        return False  # let GTK update the switch's visual state normally

    def on_continue_clicked(self, button):
        """Handle continue button click"""
        selected_option = self.options[self.selected_option]
        print(f"DEBUG: Continue clicked with selection: {selected_option['name']}")

        # Write selection to file
        self.write_selection_to_file()
        self.write_package_selection()

        if self.on_continue_callback:
            # Pass the selected option to the callback
            self.on_continue_callback(self.selected_option, selected_option)
        else:
            print("DEBUG: No continue callback provided")

    def write_selection_to_file(self):
        """Write the selected option (index + key), the Big Picture autostart
        flag for that option, and the update checkbox state."""
        config_dir = "/tmp/installer_config"
        config_file_de = os.path.join(config_dir, "de_selection")
        config_file_de_key = os.path.join(config_dir, "de_selection_key")
        config_file_updates = os.path.join(config_dir, "install_updates")
        config_file_bigpicture = os.path.join(config_dir, "bigpicture_autostart")

        updates_val = "1" if self.update_check.get_active() else "0"
        de_key = self.options[self.selected_option]["key"]
        bigpicture_val = "1" if self.bigpicture_enabled.get(self.selected_option, False) else "0"

        try:
            # Check if we have write permission to the directory
            if os.path.exists(config_dir):
                can_write = os.access(config_dir, os.W_OK)
            else:
                # Check if we can write to parent directory
                can_write = os.access(os.path.dirname(config_dir), os.W_OK)

            if can_write:
                # We have permission, write directly
                os.makedirs(config_dir, exist_ok=True)
                with open(config_file_de, 'w') as f:
                    f.write(str(self.selected_option))
                with open(config_file_de_key, 'w') as f:
                    f.write(de_key)
                with open(config_file_updates, 'w') as f:
                    f.write(updates_val)
                with open(config_file_bigpicture, 'w') as f:
                    f.write(bigpicture_val)
                print(f"DEBUG: Wrote selection index {self.selected_option} ({de_key}), "
                      f"bigpicture={bigpicture_val} and flags to {config_dir}")
            else:
                # Need elevated privileges, use pkexec
                print("DEBUG: Elevated privileges required, using pkexec")
                self.write_selection_with_pkexec(
                    config_dir, config_file_de, config_file_de_key,
                    config_file_updates, config_file_bigpicture,
                    de_key, updates_val, bigpicture_val,
                )

        except Exception as e:
            print(f"ERROR: Failed to write selection to file: {e}")
            # Try with pkexec as fallback
            try:
                self.write_selection_with_pkexec(
                    config_dir, config_file_de, config_file_de_key,
                    config_file_updates, config_file_bigpicture,
                    de_key, updates_val, bigpicture_val,
                )
            except Exception as e2:
                print(f"ERROR: Fallback with pkexec also failed: {e2}")

    def write_selection_with_pkexec(self, config_dir, config_file_de, config_file_de_key,
                                     config_file_updates, config_file_bigpicture,
                                     de_key, updates_val, bigpicture_val):
        """Write selection file using pkexec for elevated privileges"""
        import subprocess

        # Create a temporary script to execute with elevated privileges
        script_content = f"""#!/bin/bash
mkdir -p "{config_dir}"
echo "{self.selected_option}" > "{config_file_de}"
echo "{de_key}" > "{config_file_de_key}"
echo "{updates_val}" > "{config_file_updates}"
echo "{bigpicture_val}" > "{config_file_bigpicture}"
chmod 644 "{config_file_de}" "{config_file_de_key}" "{config_file_updates}" "{config_file_bigpicture}"
"""

        # Write temp script
        temp_script = "/tmp/de_selection_writer.sh"
        with open(temp_script, 'w') as f:
            f.write(script_content)
        os.chmod(temp_script, 0o755)

        try:
            # Execute with pkexec
            result = subprocess.run(
                ['pkexec', 'bash', temp_script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"DEBUG: Successfully wrote selection index and flags using pkexec")
            else:
                print(f"ERROR: pkexec failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                raise Exception(f"pkexec failed: {result.stderr}")
        finally:
            # Clean up temp script
            try:
                os.remove(temp_script)
            except:
                pass

    def write_package_selection(self):
        """Write the package selection config files for the installation widget."""
        if self.selected_packages is None:
            return  # Not customized, use defaults

        config_dir = "/tmp/installer_config"
        packages = self._get_all_packages()

        # Separate flatpak selections and pacman removals
        selected_flatpaks = []
        removed_pacman = []
        for pkg_id, enabled in self.selected_packages.items():
            if pkg_id not in packages:
                continue
            pkg_type = packages[pkg_id].get("type", "pacman")
            if pkg_type == "flatpak":
                if enabled:
                    selected_flatpaks.append(pkg_id)
            else:
                if not enabled:
                    removed_pacman.append(pkg_id)

        flatpak_data = json.dumps(selected_flatpaks)
        removal_data = json.dumps(removed_pacman)

        try:
            if os.path.exists(config_dir):
                can_write = os.access(config_dir, os.W_OK)
            else:
                can_write = os.access(os.path.dirname(config_dir), os.W_OK)

            if can_write:
                os.makedirs(config_dir, exist_ok=True)
                with open(os.path.join(config_dir, "selected_packages"), 'w') as f:
                    f.write(flatpak_data)
                with open(os.path.join(config_dir, "removed_packages"), 'w') as f:
                    f.write(removal_data)
                print(f"DEBUG: Wrote package selection to {config_dir}")
            else:
                temp_script = "/tmp/pkg_selection_writer.sh"
                with open(temp_script, 'w') as f:
                    f.write(f'#!/bin/bash\nmkdir -p "{config_dir}"\n')
                    f.write(f"cat > \"{config_dir}/selected_packages\" << 'PKGEOF'\n{flatpak_data}\nPKGEOF\n")
                    f.write(f"cat > \"{config_dir}/removed_packages\" << 'PKGEOF'\n{removal_data}\nPKGEOF\n")
                    f.write(f'chmod 644 "{config_dir}/selected_packages" "{config_dir}/removed_packages"\n')
                os.chmod(temp_script, 0o755)
                try:
                    subprocess.run(['pkexec', 'bash', temp_script], capture_output=True, text=True, timeout=30)
                finally:
                    try:
                        os.remove(temp_script)
                    except:
                        pass
        except Exception as e:
            print(f"ERROR: Failed to write package selection: {e}")

    def get_selected_option(self):
        """Get the currently selected option"""
        return self.selected_option, self.options[self.selected_option]

    # --- Essential packages that cannot be deselected ---
    ESSENTIAL_PACKAGES = {
        'base', 'linux', 'linux-headers', 'linux-firmware', 'linux-api-headers',
        'grub', 'efibootmgr', 'systemd', 'systemd-libs', 'systemd-sysvcompat',
        'pacman', 'glibc', 'bash', 'sudo', 'filesystem', 'mkinitcpio',
        'dbus', 'shadow', 'util-linux', 'coreutils', 'gcc-libs', 'glib2',
        'iana-etc', 'tzdata', 'keyutils', 'libcap', 'openssl', 'zlib',
        'xz', 'bzip2', 'gzip', 'tar', 'findutils', 'grep', 'sed', 'gawk',
        'procps-ng', 'psmisc', 'e2fsprogs', 'dosfstools', 'btrfs-progs',
        'iproute2', 'iputils', 'kbd',
    }

    BOOTLOADER_PACKAGES = {'grub', 'efibootmgr', 'os-prober', 'refind'}

    # Categories that are hidden from Advanced Setup
    # Essential packages can't be removed; DE packages are controlled by the DE picker above
    HIDDEN_CATEGORIES = {"System (Essential)", "Desktop Environment"}

    def _categorize_package(self, name, groups):
        """Assign a UI category based on package name and groups.
        Returns None for packages that should be hidden from Advanced Setup."""
        if name in self.ESSENTIAL_PACKAGES:
            return None

        if name in self.BOOTLOADER_PACKAGES:
            return None

        gl = groups.lower() if groups else ""
        nl = name.lower()

        if any(x in nl for x in ('grub', 'refind', 'efibootmgr', 'os-prober', 'shim')):
            return None

        if 'gnome' in gl or nl.startswith('gnome-') or name in ('gdm', 'mutter', 'nautilus'):
            return None
        if 'plasma' in gl or 'kde' in gl or nl.startswith('plasma-') or nl.startswith('kde'):
            return None
        if any(nl.startswith(p) for p in ('xdg-', 'xorg-', 'wayland', 'libx11', 'libxkb')):
            return None

        # GPU drivers are handled by remove_gpu.sh
        if any(x in nl for x in ('nvidia', 'mesa', 'vulkan', 'xf86-', 'libva-', 'libdrm')):
            return None

        if any(x in nl for x in ('pipewire', 'wireplumber', 'gstreamer', 'gst-', 'ffmpeg')):
            return "Multimedia"

        if any(nl.startswith(p) for p in ('ttf-', 'otf-', 'noto-fonts', 'adobe-source')):
            return "Fonts"

        if any(x in nl for x in ('networkmanager', 'firewall', 'openssh', 'bluez', 'bluetooth')):
            return "Network"

        if any(nl.startswith(p) for p in ('python-', 'lib', 'perl-')):
            return "Libraries"

        return "Applications"

    def _query_pacman_packages(self):
        """Query all explicitly installed packages from pacman with details."""
        packages = {}
        try:
            result = subprocess.run(
                ['pacman', '-Qei', '--color', 'never'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                print(f"DEBUG: pacman -Qei failed: {result.stderr}")
                return packages

            current = {}
            for line in result.stdout.split('\n'):
                if line.startswith('Name'):
                    if current.get('name'):
                        pkg_name = current['name']
                        cat = self._categorize_package(pkg_name, current.get('groups', ''))
                        if cat is not None:
                            packages[pkg_name] = {
                                "name": pkg_name,
                                "description": current.get('description', ''),
                                "category": cat,
                                "type": "pacman",
                            }
                    current = {}
                    current['name'] = line.split(':', 1)[1].strip()
                elif line.startswith('Description'):
                    current['description'] = line.split(':', 1)[1].strip()
                elif line.startswith('Groups'):
                    current['groups'] = line.split(':', 1)[1].strip()

            # Don't forget the last package
            if current.get('name'):
                pkg_name = current['name']
                cat = self._categorize_package(pkg_name, current.get('groups', ''))
                if cat is not None:
                    packages[pkg_name] = {
                        "name": pkg_name,
                        "description": current.get('description', ''),
                        "category": cat,
                        "type": "pacman",
                    }
        except Exception as e:
            print(f"DEBUG: Error querying pacman packages: {e}")
        return packages

    def _get_flatpak_packages(self):
        """Return the static list of Flatpak packages."""
        return {
            "app.zen_browser.zen": {
                "name": "Zen Browser",
                "description": "Privacy-focused web browser",
                "category": "Flatpak Apps",
                "type": "flatpak",
                "essential": False,
            },
            "io.github.Faugus.faugus-launcher": {
                "name": "Faugus Launcher",
                "description": "Game launcher utility",
                "category": "Flatpak Apps",
                "type": "flatpak",
                "essential": False,
            },
            "it.mijorus.gearlever": {
                "name": "Gear Lever",
                "description": "AppImage manager",
                "category": "Flatpak Apps",
                "type": "flatpak",
                "essential": False,
            },
            "com.github.tchx84.Flatseal": {
                "name": "Flatseal",
                "description": "Flatpak permissions manager",
                "category": "Flatpak Apps",
                "type": "flatpak",
                "essential": False,
            },
            "com.usebottles.bottles": {
                "name": "Bottles",
                "description": "Run Windows software on Linux",
                "category": "Flatpak Apps",
                "type": "flatpak",
                "essential": False,
            },
            "com.heroicgameslauncher.hgl": {
                "name": "Heroic Games Launcher",
                "description": "Open source game launcher for GOG and Epic Games",
                "category": "Flatpak Apps",
                "type": "flatpak",
                "essential": False,
            },
        }

    def _get_all_packages(self):
        """Return user-selectable packages (pacman + flatpak), using cache if available.
        Excludes essential system packages and DE packages (handled by DE picker)."""
        if self._cached_packages is None:
            all_pkgs = self._query_pacman_packages()
            all_pkgs.update(self._get_flatpak_packages())
            # Filter out hidden categories (essential + DE)
            self._cached_packages = {
                pkg_id: info for pkg_id, info in all_pkgs.items()
                if info.get("category") is not None
            }
        return self._cached_packages

    def on_advanced_setup_clicked(self, button):
        """Open the Advanced Setup dialog with package settings."""
        # Query packages (cached after first run)
        packages = self._get_all_packages()

        # Init selected_packages on first open (default: all on)
        if self.selected_packages is None:
            self.selected_packages = {pkg_id: True for pkg_id in packages}

        dialog = Adw.Window()
        dialog.set_title("Advanced Setup")
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        dialog.set_default_size(650, 600)
        dialog.set_resizable(True)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        dialog.set_content(main_box)

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle.new("Advanced Setup", "Packages"))
        main_box.append(header)

        packages_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        packages_page.set_vexpand(True)
        main_box.append(packages_page)

        # Search entry
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Filter packages…")
        search_entry.set_margin_start(24)
        search_entry.set_margin_end(24)
        search_entry.set_margin_top(12)
        packages_page.append(search_entry)

        # Scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        packages_page.append(scrolled)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        scrolled.set_child(content_box)

        # Group by category
        categories = {}
        for pkg_id, pkg_info in packages.items():
            cat = pkg_info["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((pkg_id, pkg_info))

        # Sort categories: Flatpak last, rest alphabetical
        def cat_sort_key(name):
            if "Flatpak" in name:
                return (2, name)
            return (1, name)

        checkbuttons = {}
        all_rows = []  # (row_widget, pkg_id, pkg_name) for search filtering

        for cat_name in sorted(categories.keys(), key=cat_sort_key):
            pkg_list = sorted(categories[cat_name], key=lambda x: x[0])

            # Category header
            cat_label = Gtk.Label()
            cat_label.set_markup(f'<span size="large" weight="bold">{cat_name}</span>')
            cat_label.set_halign(Gtk.Align.START)
            cat_label.set_margin_top(12)
            cat_label.set_margin_bottom(2)
            content_box.append(cat_label)

            sel_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            sel_row.set_halign(Gtk.Align.START)
            sel_row.set_margin_bottom(4)

            select_all_btn = Gtk.Button(label="Select All")
            select_all_btn.add_css_class("flat")
            deselect_all_btn = Gtk.Button(label="Deselect All")
            deselect_all_btn.add_css_class("flat")
            sel_row.append(select_all_btn)
            sel_row.append(deselect_all_btn)
            content_box.append(sel_row)

            cat_checks = []

            for pkg_id, pkg_info in pkg_list:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                row.set_margin_start(8)
                row.set_margin_top(2)
                row.set_margin_bottom(2)

                check = Gtk.CheckButton()
                check.set_active(self.selected_packages.get(pkg_id, True))
                row.append(check)

                labels_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                labels_box.set_hexpand(True)

                name_label = Gtk.Label()
                display_name = pkg_info.get("name", pkg_id)
                name_label.set_markup(f'<span weight="bold">{GLib.markup_escape_text(display_name)}</span>')
                name_label.set_halign(Gtk.Align.START)
                labels_box.append(name_label)

                if pkg_info.get("description"):
                    desc_label = Gtk.Label()
                    desc_label.set_text(pkg_info["description"])
                    desc_label.set_halign(Gtk.Align.START)
                    desc_label.set_wrap(True)
                    desc_label.add_css_class("dim-label")
                    labels_box.append(desc_label)

                row.append(labels_box)
                content_box.append(row)

                checkbuttons[pkg_id] = check
                cat_checks.append(check)
                # Track for search filtering
                search_text = f"{pkg_id} {display_name} {pkg_info.get('description', '')}".lower()
                all_rows.append((row, cat_label, sel_row, search_text))

            # Wire Select All / Deselect All
            def _make_toggle(checks, val):
                def _toggle(btn):
                    for c in checks:
                        c.set_active(val)
                return _toggle
            select_all_btn.connect("clicked", _make_toggle(cat_checks, True))
            deselect_all_btn.connect("clicked", _make_toggle(cat_checks, False))

        # Search filtering
        current_cat_widgets = {}  # cat_label -> (sel_row, [rows])
        for row, cat_label, sel_row, _ in all_rows:
            if cat_label not in current_cat_widgets:
                current_cat_widgets[cat_label] = (sel_row, [])
            current_cat_widgets[cat_label][1].append(row)

        row_search_map = {row: search_text for row, _cat_label, _sel_row, search_text in all_rows}

        def on_search_changed(entry):
            query = entry.get_text().lower().strip()
            for cat_label, (sel_row, rows_for_cat) in current_cat_widgets.items():
                any_visible = False
                for row in rows_for_cat:
                    search_text = row_search_map.get(row, "")
                    visible = not query or query in search_text
                    row.set_visible(visible)
                    if visible:
                        any_visible = True
                cat_label.set_visible(any_visible)
                sel_row.set_visible(any_visible and not query)

        search_entry.connect("search-changed", on_search_changed)

        # Bottom bar
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_bar.set_halign(Gtk.Align.END)
        bottom_bar.set_margin_top(12)
        bottom_bar.set_margin_bottom(16)
        bottom_bar.set_margin_end(24)
        main_box.append(bottom_bar)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: dialog.close())
        bottom_bar.append(cancel_btn)

        apply_btn = Gtk.Button(label="Apply")
        apply_btn.add_css_class("suggested-action")

        def on_apply(btn):
            if self.selected_packages is None:
                self.selected_packages = {pkg_id: True for pkg_id in packages}

            for pkg_id, check in checkbuttons.items():
                self.selected_packages[pkg_id] = check.get_active()

            self.write_package_selection()
            dialog.close()

        apply_btn.connect("clicked", on_apply)
        bottom_bar.append(apply_btn)

        dialog.present()

    def on_widget_mapped(self, widget):
        """Start entrance animation and refresh data"""
        print("DEBUG: Widget mapped, refreshing UI and checking internet...")

        # Refresh UI (checks internet again)
        self.refresh_ui()

        if not self.animation_played:
            GLib.timeout_add(200, self.start_animation)
            self.animation_played = True

    def refresh_ui(self):
        """Re-check internet and refresh the currently shown detail panel
        (the sidebar rows themselves don't need rebuilding - only the
        "Requires Internet" notice does, for any option with
        requires_internet=True)."""
        self.has_internet = self.check_internet_connection()
        print(f"DEBUG: Refreshing UI. Internet status: {self.has_internet}")

        current_status = self.update_check.get_sensitive()
        if self.has_internet != current_status:
            self.update_check.set_sensitive(self.has_internet)

            if self.has_internet:
                self.update_check.set_active(True)
                self.update_check.set_tooltip_text(None)
            else:
                self.update_check.set_active(False)
                self.update_check.set_tooltip_text("Internet connection required")

        # Toggle the pre-built "Requires Internet" notices instead of rebuilding pages
        for index, (notice_box, requires_internet) in getattr(self, "internet_notices", {}).items():
            notice_box.set_visible(bool(requires_internet and not self.has_internet))

    def start_animation(self):
        """Fade in animation"""
        def animate(value, data):
            self.set_opacity(value)

        target = Adw.CallbackAnimationTarget.new(animate, None)
        animation = Adw.TimedAnimation.new(self, 0.0, 1.0, 1200, target)
        animation.set_easing(Adw.Easing.EASE_OUT_QUAD)
        animation.play()
        return False

    def setup_css(self):
        """Setup CSS styling"""
        css_provider = Gtk.CssProvider()
        css_data = """
        .option_box {
            background: @theme_base_color;
            border: 2px solid rgba(0,0,0,0.1);
            border-radius: 12px;
            margin: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }

        .option_box:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            background: alpha(@theme_base_color, 0.95);
        }

        .option_box.selected {
            border-color: @accent_color;
            background: alpha(@accent_color, 0.1);
            transform: scale(1.02);
            box-shadow: 0 6px 25px alpha(@accent_color, 0.3);
        }

        .option_box.selected:hover {
            transform: scale(1.02) translateY(-2px);
        }

        .option_box.unselected {
            opacity: 0.8;
        }

        .option_box.unselected:hover {
            opacity: 1.0;
        }

        .option_box.disabled {
            opacity: 0.5;
            background: alpha(@theme_base_color, 0.7);
            border-color: rgba(0,0,0,0.05);
            cursor: not-allowed;
        }

        .option_box.disabled:hover {
            transform: none;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }

        .disabled_icon {
            opacity: 0.4;
            filter: grayscale(100%);
        }

        .disabled_text {
            opacity: 0.6;
        }

        .internet_notice {
            color: @warning_color;
            opacity: 1.0;
        }

        .large_fallback_icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .option_icon_image {
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .option_icon_image:hover, .large_fallback_icon:hover {
            transform: scale(1.05);
        }

        .fallback_emoji {
            font-size: 96px;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .option_description {
            color: alpha(@theme_fg_color, 0.8);
            font-size: 0.95em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .option_details {
            color: alpha(@theme_fg_color, 0.6);
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .back_button {
            border-radius: 20px;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .back_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px alpha(@theme_bg_color, 0.3);
        }

        .back_button:active {
            transform: translateY(0px);
        }

        .continue_button {
            border-radius: 20px;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .continue_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px alpha(@accent_color, 0.3);
        }

        .continue_button:active {
            transform: translateY(0px);
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        .pulse-animation {
            animation: pulse 2s ease-in-out infinite;
        }

        label {
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .de_split_box {
            border-radius: 12px;
        }

        .de_list_scroller {
            border-right: 1px solid rgba(0,0,0,0.15);
        }

        .de_option_list {
            background: transparent;
        }

        .de_list_row {
            border-radius: 8px;
            margin: 2px 6px;
        }

        .de_list_row:hover {
            background: alpha(@theme_fg_color, 0.06);
        }

        .de_list_row:selected {
            background: alpha(@accent_color, 0.15);
            font-weight: bold;
        }

        .de_detail_panel {
            padding: 12px;
        }
        """

        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
