import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Adw, GLib

def setup_arc_manager_css():
    css = """
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
    .animated_button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 25px;
        font-weight: bold;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        box-shadow: 0 4px 12px rgba(201, 148, 218, 0.3);
    }
    .animated_button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(201, 148, 218, 0.3);
    }
    .animated_button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 8px rgba(201, 148, 218, 0.3);
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .pulse-animation {
        animation: pulse 2s ease-in-out infinite;
    }
    .success_icon {
        color: #4CAF50;
    }
    .error_icon {
        color: #bf0303;
    }
    .warning_icon {
        color: #b08000;
    }
    .package-row {
        transition: all 0.2s ease;
        border-radius: 8px;
    }
    .package-row:hover {
        background: alpha(@theme_selected_bg_color, 0.1);
    }
    .status-ready {
        color: #57e389;
    }
    .status-building {
        color: #62a0ea;
    }
    .status-error {
        color: #ff7b63;
    }
    .status-warning {
        color: #f6d32d;
    }
    .mode-button {
        border-radius: 12px;
        padding: 16px;
        min-height: 80px;
        transition: all 0.3s ease;
    }
    .mode-button:hover {
        background: alpha(@theme_selected_bg_color, 0.15);
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_string(css)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

def create_pill_button(label, css_class='back_button', size=(150, 50)):
    button = Gtk.Button(label=label)
    button.add_css_class(css_class)
    button.set_size_request(size[0], size[1])
    
    # Hover controller for pulse animation
    controller = Gtk.EventControllerMotion()
    def on_enter(ctrl, x, y):
        button.add_css_class('pulse-animation')
    def on_leave(ctrl):
        button.remove_css_class('pulse-animation')
    
    controller.connect('enter', on_enter)
    controller.connect('leave', on_leave)
    button.add_controller(controller)
    
    return button

def create_entrance_animation(widget, container, duration=1200):
    container.set_opacity(0.0)
    container.set_margin_top(40)
    
    target_opacity = Adw.CallbackAnimationTarget.new(
        lambda value: container.set_opacity(value)
    )
    anim_opacity = Adw.TimedAnimation.new(widget, 0.0, 1.0, duration, target_opacity)
    anim_opacity.set_easing(Adw.Easing.EASE_OUT_EXPO)
    
    target_margin = Adw.CallbackAnimationTarget.new(
        lambda value: container.set_margin_top(int(value))
    )
    anim_margin = Adw.TimedAnimation.new(widget, 40.0, 0.0, duration, target_margin)
    anim_margin.set_easing(Adw.Easing.EASE_OUT_EXPO)
    
    anim_opacity.play()
    anim_margin.play()
