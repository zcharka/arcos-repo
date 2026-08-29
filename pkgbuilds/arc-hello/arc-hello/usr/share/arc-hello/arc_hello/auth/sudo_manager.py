import os
import subprocess
import tempfile
import threading
import atexit
from typing import Optional, Callable

class SudoManager:
    """Singleton, który raz uwierzytelnia hasło i pozwala uruchamiać
    polecenia z rootem BEZ wpisywania hasła w linię poleceń (nie widać go w
    `ps aux`) i BEZ zapisu na dysk. Hasło płynie przez prywatny named pipe
    (FIFO), czytany przez sudo za pomocą mechanizmu SUDO_ASKPASS."""

    _instance: Optional["SudoManager"] = None

    @classmethod
    def get_instance(cls) -> "SudoManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.user_password = None
        self._running = True

        askpass_tf = tempfile.NamedTemporaryFile(delete=False, prefix="arc-askpass-")
        self.askpass_script = askpass_tf.name
        askpass_tf.close()

        wrapper_tf = tempfile.NamedTemporaryFile(delete=False, prefix="arc-sudo-")
        self.wrapper_path = wrapper_tf.name
        wrapper_tf.close()

        self.fifo_dir = tempfile.mkdtemp(prefix="arc-pipe-")
        self.fifo_path = os.path.join(self.fifo_dir, "password_pipe")
        os.mkfifo(self.fifo_path, 0o600)

        self._setup_scripts()

        self._feed_condition = threading.Condition()
        self._feeds_allowed = 0
        self.feeder_thread = threading.Thread(target=self._feed_pipe_loop, daemon=True)
        self.feeder_thread.start()
        atexit.register(self.cleanup)

    def _setup_scripts(self):
        with open(self.askpass_script, "w") as f:
            f.write(f'#!/bin/sh\ncat "{self.fifo_path}"\n')
        os.chmod(self.askpass_script, 0o700)
        with open(self.wrapper_path, "w") as f:
            f.write("#!/bin/sh\n"
                    f"export SUDO_ASKPASS='{self.askpass_script}'\n"
                    'exec sudo -A "$@"\n')
        os.chmod(self.wrapper_path, 0o700)

    def _feed_pipe_loop(self):
        while self._running:
            with self._feed_condition:
                self._feed_condition.wait_for(lambda: self._feeds_allowed > 0 or not self._running)
            if not self._running:
                break
            if self.user_password:
                try:
                    fd = os.open(self.fifo_path, os.O_WRONLY)
                    with os.fdopen(fd, "w") as f:
                        f.write(str(self.user_password) + "\n")
                    with self._feed_condition:
                        if self._feeds_allowed > 0:
                            self._feeds_allowed -= 1
                except OSError:
                    pass
            else:
                with self._feed_condition:
                    if self._feeds_allowed > 0:
                        self._feeds_allowed -= 1

    def validate_password(self, password: str) -> bool:
        if not password:
            return False
        subprocess.run(["sudo", "-k"], check=False)
        result = subprocess.run(
            ["sudo", "-S", "-v"], input=password + "\n",
            capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"},
        )
        return result.returncode == 0

    def set_password(self, password: str):
        self.user_password = password

    def run_privileged(self, cmd: list, **kwargs):
        if not self.user_password:
            raise ValueError("Brak hasła — najpierw validate_password()+set_password()")
        with self._feed_condition:
            self._feeds_allowed += 1
            self._feed_condition.notify_all()
        try:
            return subprocess.run([self.wrapper_path] + cmd, **kwargs)
        finally:
            self._drain_pipe()

    def run_privileged_async(self, cmd: list,
                             on_output: Callable[[str, str], None],
                             on_finished: Callable[[int], None]):
        def _thread():
            try:
                on_output(f"$ {' '.join(cmd)}\n", "cmd")
                with self._feed_condition:
                    self._feeds_allowed += 1
                    self._feed_condition.notify_all()

                proc = subprocess.Popen(
                    [self.wrapper_path] + cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                if proc.stdout:
                    for line in iter(proc.stdout.readline, ''):
                        if line:
                            on_output(line, "info")
                proc.wait()
                rc = proc.returncode
                if rc == 0:
                    on_output("\n[SUKCES] Operacja zakończona sukcesem (kod 0).\n", "success")
                else:
                    on_output(f"\n[BŁĄD] Operacja nie powiodła się (kod {rc}).\n", "error")
                on_finished(rc)
            except Exception as e:
                on_output(f"\n[BŁĄD] Wystąpił wyjątek: {e}\n", "error")
                on_finished(-1)
            finally:
                self._drain_pipe()

        t = threading.Thread(target=_thread, daemon=True)
        t.start()

    def forget_password(self):
        self.user_password = None
        subprocess.run(["sudo", "-k"], check=False)

    def _drain_pipe(self):
        with self._feed_condition:
            remaining = self._feeds_allowed
        if remaining > 0:
            try:
                fd = os.open(self.fifo_path, os.O_RDONLY | os.O_NONBLOCK)
                os.read(fd, 1024)
                os.close(fd)
            except Exception:
                pass

    def cleanup(self):
        self._running = False
        self.forget_password()
        for p in (self.askpass_script, self.wrapper_path, self.fifo_path):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(self.fifo_dir)
        except OSError:
            pass

def get_sudo_manager() -> SudoManager:
    return SudoManager.get_instance()
