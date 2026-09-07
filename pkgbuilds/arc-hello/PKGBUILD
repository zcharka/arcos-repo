# Maintainer: ArcOS Developers <https://github.com/zcharka/ArcOS>

pkgname=arc-hello
pkgver=1.0.0
pkgrel=10
pkgdesc='ArcOS Welcome and Setup Assistant'
url='https://github.com/zcharka'
arch=('any')
license=('GPL-3.0')
depends=(
  'python-gobject'
  'gtk4'
  'libadwaita'
  'python'
  'xdg-utils'
  'hicolor-icon-theme'
)

prepare() {
    cd "${startdir}/arc-hello"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
}

package() {
    cd "${startdir}/arc-hello"

    find usr -type f ! -name "*.pyc" ! -path "*/__pycache__/*" | while IFS= read -r _file; do
        if [[ "${_file}" == usr/bin/* ]]; then
            install -Dm755 "${_file}" "${pkgdir}/${_file}"
        else
            install -Dm644 "${_file}" "${pkgdir}/${_file}"
        fi
    done
}
