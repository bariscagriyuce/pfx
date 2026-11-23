#!/bin/sh
# Installs PFX Certificate Installer for the current user only (no root needed).
# Kullanıcı için kurulum / Instalação apenas para o usuário atual.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/share/pfx-yukleyici"
APPS="$HOME/.local/share/applications"

mkdir -p "$DEST" "$APPS"
install -m 755 "$SRC/pfx_yukleyici.py" "$DEST/pfx_yukleyici.py"
sed "s|^Exec=.*|Exec=/usr/bin/env python3 $DEST/pfx_yukleyici.py %f|" \
  "$SRC/pfx-yukleyici.desktop" > "$APPS/pfx-yukleyici.desktop"

update-desktop-database "$APPS" 2>/dev/null || true
xdg-mime default pfx-yukleyici.desktop application/x-pkcs12 2>/dev/null || true
kbuildsycoca6 >/dev/null 2>&1 || true
echo "OK: $APPS/pfx-yukleyici.desktop"
