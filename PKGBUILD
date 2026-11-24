# Maintainer: bariscagriyuce <https://github.com/bariscagriyuce>
pkgname=pfx-yukleyici
pkgver=1.2.0
pkgrel=1
pkgdesc="Install PFX/P12 certificates into browsers and the system without a terminal"
arch=('any')
url="https://github.com/bariscagriyuce/pfx"
license=('MIT')
depends=('python' 'pyside6' 'nss' 'openssl' 'polkit' 'p11-kit')
source=('pfx_yukleyici.py' 'pfx-yukleyici.desktop' 'LICENSE')
sha256sums=('SKIP' 'SKIP' 'SKIP')

package() {
  install -Dm755 "$srcdir/pfx_yukleyici.py" "$pkgdir/usr/bin/pfx-yukleyici"
  install -Dm644 "$srcdir/pfx-yukleyici.desktop" \
    "$pkgdir/usr/share/applications/pfx-yukleyici.desktop"
  install -Dm644 "$srcdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
