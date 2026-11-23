# PFX Certificate Installer

**English** · [Türkçe](README.tr.md) · [Português (Brasil)](README.pt-BR.md)

A small desktop application for Linux (made for CachyOS / Arch Linux) that installs
**PFX / P12 (PKCS#12)** certificates — e.g. e-signature or client authentication
certificates — into your browsers **without using the terminal**.

## Features

- Pick the file or drag & drop it, enter the password, click **Install**.
- Double-clicking a `.pfx` / `.p12` file in the file manager opens the app with that file.
- Detects the certificate stores automatically:
  - Chrome / Chromium / Edge / Brave / Vivaldi (shared NSS store `~/.pki/nssdb`)
  - Firefox, LibreWolf, Waterfox, Floorp, Zen, Thunderbird (all profiles, incl. *profile-sync-daemon*)
  - Flatpak browsers
- Shows the certificate details (subject, issuer, validity) and verifies the password before installing.
- Optionally adds the CA (root/intermediate) certificates of the chain to the system trust store.
- Lists installed personal certificates and lets you remove them.
- Supports legacy-encrypted PFX files.
- Passwords are never passed on the command line.
- Available in **English, Turkish and Brazilian Portuguese** (detected from the system language, can be changed in the app).
- **Automatic updates:** checks GitHub for a new release at startup; if you approve, it downloads and installs it and restarts.

## Installation

1. Download the latest `pfx-yukleyici-*.pkg.tar.zst` from the [Releases](https://github.com/bariscagriyuce/pfx/releases) page.
2. Open it with your package installer, or run:

   ```bash
   sudo pacman -U pfx-yukleyici-*.pkg.tar.zst
   ```

3. Start **PFX Certificate Installer** from the application menu.

After the first installation, updates are offered by the app itself.

### Dependencies

`python`, `pyside6`, `nss`, `openssl`, `polkit`, `p11-kit` — pacman installs them automatically.

### Other distributions

Install the dependencies above with your package manager, then run `sh kur.sh`
in this folder. It installs the app for your user only. With this install the app can't update itself; it only tells you when a new version is available.

## Usage

1. **Install** tab: choose the PFX file, type the password, click **Check** to see the certificate details.
2. Select where the certificate should be installed and click **Install Certificate**.
3. Restart your browsers.

The **Installed Certificates** tab lists personal certificates and lets you delete them.
The **About / Updates** tab shows the version and lets you check for updates manually.

## Uninstall

```bash
sudo pacman -R pfx-yukleyici
```

## Building the package

```bash
makepkg -f
```

To publish a new version: update `__version__` in `pfx_yukleyici.py` and `pkgver`
in `PKGBUILD`, then run `sh release.sh` (needs the GitHub CLI `gh`).
