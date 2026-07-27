import os
import re
from .package_discovery import PackageInfo

class PkgrelManager:
    def increment_pkgrel(self, package: PackageInfo) -> int:
        current_rel = self._read_pkgrel(package.pkgbuild_path)
        new_rel = current_rel + 1
        self._write_pkgrel(package.pkgbuild_path, new_rel)
        package.pkgrel = new_rel
        return new_rel

    def _read_pkgrel(self, pkgbuild_path: str) -> int:
        if not os.path.isfile(pkgbuild_path):
            return 1
        with open(pkgbuild_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(r'^pkgrel=(\d+)$', line.strip())
                if match:
                    return int(match.group(1))
        return 1

    def _write_pkgrel(self, pkgbuild_path: str, new_rel: int):
        if not os.path.isfile(pkgbuild_path):
            return
        with open(pkgbuild_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        with open(pkgbuild_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if re.match(r'^pkgrel=\d+', line.strip()):
                    f.write(f'pkgrel={new_rel}\n')
                else:
                    f.write(line)
