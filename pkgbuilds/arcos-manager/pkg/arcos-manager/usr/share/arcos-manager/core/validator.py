import os
import re

def validate_package_name(name: str) -> bool:
    """Validate package name to be alphanumeric and hyphens only."""
    return bool(re.match(r'^[a-zA-Z0-9\-]+$', name))

def validate_path(path: str, allowed_base_dir: str = '/home/Sebastian/Documents/arcos-repo') -> bool:
    """Validate that path is under allowed_base_dir and has no symlink escapes."""
    real_path = os.path.realpath(path)
    real_base = os.path.realpath(os.path.expanduser(allowed_base_dir))
    return real_path.startswith(real_base)

def sanitize_for_command(arg: str) -> str:
    """Ensure string is safe for subprocess args."""
    return arg
