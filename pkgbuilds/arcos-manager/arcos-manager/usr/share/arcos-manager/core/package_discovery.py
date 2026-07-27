import os
import re
from dataclasses import dataclass
from typing import List

PKGBUILDS_DIR = os.path.expanduser('~/Documents/arcos-repo/pkgbuilds')

@dataclass
class PackageInfo:
    name: str
    pkgver: str
    pkgrel: int
    pkgdesc: str
    arch: str
    path: str
    pkgbuild_path: str

class PackageDiscovery:
    def __init__(self, pkgbuilds_dir: str = PKGBUILDS_DIR):
        self.pkgbuilds_dir = pkgbuilds_dir

    def scan_packages(self) -> List[PackageInfo]:
        return self.refresh()

    def _parse_pkgbuild(self, pkgbuild_path: str) -> dict:
        info = {}
        if not os.path.isfile(pkgbuild_path):
            return info
        
        with open(pkgbuild_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                match = re.match(r'^(pkgname|pkgver|pkgrel|pkgdesc|arch)=(.+)$', line)
                if match:
                    key = match.group(1)
                    val = match.group(2).strip("'\"()") 
                    info[key] = val
        return info

    def refresh(self) -> List[PackageInfo]:
        packages = []
        if not os.path.isdir(self.pkgbuilds_dir):
            return packages
            
        for entry in os.listdir(self.pkgbuilds_dir):
            pkg_dir = os.path.join(self.pkgbuilds_dir, entry)
            if os.path.isdir(pkg_dir):
                pkgbuild_path = os.path.join(pkg_dir, 'PKGBUILD')
                if os.path.isfile(pkgbuild_path):
                    data = self._parse_pkgbuild(pkgbuild_path)
                    if 'pkgname' in data:
                        try:
                            pkgrel = int(data.get('pkgrel', '1'))
                        except ValueError:
                            pkgrel = 1
                            
                        pkg = PackageInfo(
                            name=data.get('pkgname'),
                            pkgver=data.get('pkgver', ''),
                            pkgrel=pkgrel,
                            pkgdesc=data.get('pkgdesc', ''),
                            arch=data.get('arch', ''),
                            path=pkg_dir,
                            pkgbuild_path=pkgbuild_path
                        )
                        packages.append(pkg)
        return packages
