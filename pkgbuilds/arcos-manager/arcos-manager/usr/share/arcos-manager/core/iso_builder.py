import os
import subprocess
import hashlib
from typing import Tuple

REPO_ROOT = os.path.expanduser('~/Documents/arcos-repo')

class ISOBuilder:
    def __init__(self, repo_root: str = REPO_ROOT):
        self.repo_root = repo_root
        self.work_dir = '/tmp/arcos-iso-work'

    def build_iso(self, progress_callback=None) -> Tuple[bool, str, str]:
        profile_dir = os.path.join(self.repo_root, 'iso-profile') 
        out_dir = os.path.join(self.repo_root, 'out')
        os.makedirs(out_dir, exist_ok=True)
        
        cmd = ['pkexec', '/usr/share/arcos-manager/arcos-manager-helper', 'mkarchiso', '-v', '-w', self.work_dir, '-o', out_dir, profile_dir]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            log = proc.stdout + '\n' + proc.stderr
            success = (proc.returncode == 0)
            iso_path = ''
            if success:
                # Find iso in out_dir
                for f in os.listdir(out_dir):
                    if f.endswith('.iso'):
                        iso_path = os.path.join(out_dir, f)
                        break
            return success, iso_path, log
        except Exception as e:
            return False, '', str(e)

    def clean_work_dirs(self) -> bool:
        cmd = ['pkexec', '/usr/share/arcos-manager/arcos-manager-helper', 'clean-work']
        proc = subprocess.run(cmd, capture_output=True)
        return proc.returncode == 0

    def generate_checksum(self, iso_path: str) -> str:
        if not os.path.isfile(iso_path):
            return ""
        sha256_hash = hashlib.sha256()
        with open(iso_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
