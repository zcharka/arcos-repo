import os
import shutil
import subprocess
from typing import List, Tuple

REPO_ROOT = os.path.expanduser('~/Documents/arcos-repo')

class GitManager:
    def __init__(self, repo_root: str = REPO_ROOT):
        self.repo_root = repo_root

    def check_nested_git(self, package_dirs: List[str]) -> List[str]:
        nested = []
        for d in package_dirs:
            git_dir = os.path.join(d, '.git')
            if os.path.isdir(git_dir):
                nested.append(d)
        return nested

    def remove_nested_git(self, package_dir: str) -> bool:
        git_dir = os.path.join(package_dir, '.git')
        if os.path.isdir(git_dir):
            shutil.rmtree(git_dir, ignore_errors=True)
            return True
        return False

    def git_add_all(self) -> Tuple[bool, str]:
        proc = subprocess.run(['git', 'add', '-A'], cwd=self.repo_root, capture_output=True, text=True)
        return proc.returncode == 0, proc.stdout + '\n' + proc.stderr

    def git_commit(self, message: str) -> Tuple[bool, str]:
        proc = subprocess.run(['git', 'commit', '-m', message], cwd=self.repo_root, capture_output=True, text=True)
        return proc.returncode == 0, proc.stdout + '\n' + proc.stderr

    def git_push(self) -> Tuple[bool, str]:
        proc = subprocess.run(['git', 'push'], cwd=self.repo_root, capture_output=True, text=True)
        return proc.returncode == 0, proc.stdout + '\n' + proc.stderr

    def get_status(self) -> str:
        proc = subprocess.run(['git', 'status'], cwd=self.repo_root, capture_output=True, text=True)
        return proc.stdout
