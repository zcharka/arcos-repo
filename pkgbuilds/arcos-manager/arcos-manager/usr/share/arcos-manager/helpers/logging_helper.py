import os
import time
import subprocess

class LogManager:
    def __init__(self):
        self._log_path = ""
        os.makedirs(self.log_dir, exist_ok=True)

    @property
    def log_dir(self) -> str:
        return '/tmp/arcos-manager-logs/'

    def start_session(self) -> str:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self._log_path = os.path.join(self.log_dir, f"session-{timestamp}.log")
        with open(self._log_path, 'w', encoding='utf-8') as f:
            f.write(f"--- Session started at {timestamp} ---\n")
        return self._log_path

    def log(self, level: str, message: str):
        if not self._log_path:
            self.start_session()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self._log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level.upper()}] {message}\n")

    def get_log_path(self) -> str:
        return self._log_path

    def open_log_in_editor(self):
        if self._log_path and os.path.exists(self._log_path):
            subprocess.run(['xdg-open', self._log_path])
