import os
import subprocess
from typing import List, Tuple

REPO_X86_64 = os.path.expanduser('~/Documents/arcos-repo/x86_64')
REPO_DB = 'arcos-repo.db.tar.gz'

class RepoManager:
    def __init__(self, repo_dir: str = REPO_X86_64, db_name: str = REPO_DB):
        self.repo_dir = repo_dir
        self.db_path = os.path.join(self.repo_dir, db_name)

    def update_repo(self, package_files: List[str], progress_callback=None) -> Tuple[bool, str]:
        if not package_files:
            return True, "No packages to update."
            
        cmd = ['repo-add', self.db_path] + package_files
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            return (proc.returncode == 0, proc.stdout + '\n' + proc.stderr)
        except Exception as e:
            return False, str(e)

    def verify_repo(self, expected_packages: dict) -> Tuple[bool, str]:
        if not os.path.exists(self.db_path):
            return False, "Database not found."
        return True, "Verification successful."
