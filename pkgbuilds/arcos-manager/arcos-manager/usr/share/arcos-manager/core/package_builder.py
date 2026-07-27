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
    package_files: list
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
            package_files=[],
            error='',
            log=''
        )
        
        try:
            # 1. Run makepkg
            proc = subprocess.Popen(
                ['makepkg', '-f', '--noconfirm'],
                cwd=package.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            full_log = []
            for line in iter(proc.stdout.readline, ''):
                full_log.append(line)
                if progress_callback:
                    progress_callback(line)
            proc.stdout.close()
            proc.wait()
            
            result.log = "".join(full_log)
            if proc.returncode != 0:
                result.error = "makepkg failed"
                return result
                
            # 2. Find package files
            pkg_pattern = os.path.join(package.path, '*.pkg.tar.zst')
            pkg_files = glob.glob(pkg_pattern)
            if not pkg_files:
                result.error = "Package file not found after build"
                return result
                
            # 3. Verify and Copy ALL produced packages
            dest_files = []
            for pkg_file in pkg_files:
                verify_proc = subprocess.run(
                    ['pacman', '-Qip', pkg_file],
                    capture_output=True,
                    text=True
                )
                if verify_proc.returncode == 0:
                    dest = os.path.join(self.repo_x86_64, os.path.basename(pkg_file))
                    shutil.copy2(pkg_file, dest)
                    dest_files.append(dest)
                else:
                    result.error += f"Package verification failed for {os.path.basename(pkg_file)}\n"
            
            if dest_files:
                result.success = True
                result.package_files = dest_files
            else:
                result.error = "No packages passed verification\n" + result.error
            
        except Exception as e:
            result.error = str(e)
            
        return result

    def clean_build(self, package: PackageInfo):
        for dirname in ['pkg', 'src']:
            dpath = os.path.join(package.path, dirname)
            if os.path.isdir(dpath):
                shutil.rmtree(dpath, ignore_errors=True)
