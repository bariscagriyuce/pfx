#!/bin/sh
# Builds the package and publishes a GitHub release with it (needs: makepkg, gh).
set -e
cd "$(dirname "$0")"
VER=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' pfx_yukleyici.py)
PKGVER=$(sed -n 's/^pkgver=//p' PKGBUILD)
[ "$VER" = "$PKGVER" ] || { echo "Version mismatch: $VER vs PKGBUILD $PKGVER"; exit 1; }
makepkg -f
PKG=$(ls pfx-yukleyici-"$VER"-*-any.pkg.tar.zst | tail -1)
gh release create "v$VER" "$PKG" --title "v$VER" --notes "${NOTES:-Release v$VER}"
