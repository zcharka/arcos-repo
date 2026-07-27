import os
import glob
import shutil
import subprocess
from dataclasses import dataclass
from .package_discovery import PackageInfo

REPO_X86_64 = os.path.expanduser('~/Documents/arcos-repo/x86_64')

@dataclass
class BuildResult:
    package_name: str
    success: bool
    package_file: str
    error: str
    log: str

class PackageBuilder:
    def __init__(self, repo_x86_64: str = REPO_X86_64):
        self.repo_x86_64 = repo_x86_64
        os.makedirs(self.repo_x86_64, exist_ok=True)

    def build_package(self, package: PackageInfo, progress_callback=None) -> BuildResult:
        result = BuildResult(
            package_name=package.name,
            success=False,
            package_file='',
            error='',
            log=''
        )
        
        try:
            # 1. Run makepkg
            proc = subprocess.run(
                ['makepkg', '-f', '--noconfirm'],
                cwd=package.path,
                capture_output=True,
                text=True
            )
            result.log = proc.stdout + '\n' + proc.stderr
            if proc.returncode != 0:
                result.error = "makepkg failed"
                return result
                
            # 2. Find package file
            pkg_pattern = os.path.join(package.path, '*.pkg.tar.zst')
            pkg_files = glob.glob(pkg_pattern)
            if not pkg_files:
                result.error = "Package file not found after build"
                return result
                
            newest_pkg = max(pkg_files, key=os.path.getmtime)
            
            # 3. Verify
            verify_proc = subprocess.run(
                ['pacman', '-Qip', newest_pkg],
                capture_output=True,
                text=True
            )
            if verify_proc.returncode != 0:
                result.error = "Package verification failed"
                return result
                
            # 4. Copy to repo
            dest = os.path.join(self.repo_x86_64, os.path.basename(newest_pkg))
            shutil.copy2(newest_pkg, dest)
            
            result.success = True
            result.package_file = dest
            
        except Exception as e:
            result.error = str(e)
            
        return result

    def clean_build(self, package: PackageInfo):
        for dirname in ['pkg', 'src']:
            dpath = os.path.join(package.path, dirname)
            if os.path.isdir(dpath):
                shutil.rmtree(dpath, ignore_errors=True)
