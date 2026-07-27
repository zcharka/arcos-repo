import subprocess
import shutil
from typing import List, Tuple

class PrivilegedRunner:
    def run_privileged(self, command: List[str], progress_callback=None) -> Tuple[bool, str, str]:
        full_cmd = ['pkexec'] + command
        try:
            proc = subprocess.run(full_cmd, capture_output=True, text=True)
            return (proc.returncode == 0, proc.stdout, proc.stderr)
        except Exception as e:
            return (False, "", str(e))

    def check_polkit_available(self) -> bool:
        return shutil.which('pkexec') is not None
