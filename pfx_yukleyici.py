#!/usr/bin/env python3
"""PFX Certificate Installer / PFX Sertifika Yükleyici / Instalador de Certificados PFX

Installs PFX (PKCS#12) certificates without a terminal into the NSS
certificate stores used by Chrome / Chromium / Edge / Brave / Vivaldi
(~/.pki/nssdb), Firefox and its derivatives, and optionally adds the CA
certificates of the chain to the system trust store.

Runtime requirements: python, pyside6, nss (pk12util, certutil), openssl,
polkit (pkexec), p11-kit (trust)
"""

from __future__ import annotations

import configparser
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QLocale, QSettings, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

__version__ = "1.2.0"
REPO = "bariscagriyuce/pfx"
INSTALLED_PATH = Path("/usr/bin/pfx-yukleyici")
HOME = Path.home()

# --------------------------------------------------------------------------- #
# Translations
# --------------------------------------------------------------------------- #
LANGUAGES = {"en": "English", "tr": "Türkçe", "pt_BR": "Português (Brasil)"}

STRINGS: dict[str, dict[str, str]] = {
    "app_name": {
        "en": "PFX Certificate Installer",
        "tr": "PFX Sertifika Yükleyici",
        "pt_BR": "Instalador de Certificados PFX",
    },
    "language": {"en": "Language:", "tr": "Dil:", "pt_BR": "Idioma:"},
    "tab_install": {"en": "Install", "tr": "Yükle", "pt_BR": "Instalar"},
    "tab_installed": {
        "en": "Installed Certificates",
        "tr": "Yüklü Sertifikalar",
        "pt_BR": "Certificados Instalados",
    },
    "tab_about": {"en": "About / Updates", "tr": "Hakkında / Güncelleme",
                  "pt_BR": "Sobre / Atualizações"},
    "grp_file": {"en": "1. Certificate file", "tr": "1. Sertifika dosyası",
                 "pt_BR": "1. Arquivo do certificado"},
    "file_placeholder": {
        "en": "Choose a PFX / P12 file or drag it here",
        "tr": "PFX / P12 dosyasını seçin veya buraya sürükleyin",
        "pt_BR": "Escolha um arquivo PFX / P12 ou arraste-o para cá",
    },
    "browse": {"en": "Browse…", "tr": "Gözat…", "pt_BR": "Procurar…"},
    "file": {"en": "File:", "tr": "Dosya:", "pt_BR": "Arquivo:"},
    "password": {"en": "Password:", "tr": "Parola:", "pt_BR": "Senha:"},
    "pw_placeholder": {"en": "PFX password", "tr": "PFX parolası",
                       "pt_BR": "Senha do PFX"},
    "show": {"en": "Show", "tr": "Göster", "pt_BR": "Mostrar"},
    "check": {"en": "Check", "tr": "Kontrol et", "pt_BR": "Verificar"},
    "grp_targets": {"en": "2. Install into", "tr": "2. Yüklenecek yerler",
                    "pt_BR": "2. Instalar em"},
    "sys_ca": {
        "en": "Also add the CA (root/intermediate) certificates of the chain to "
              "the system trust store (administrator password required)",
        "tr": "Zincirdeki CA (kök/ara) sertifikalarını sistem güven deposuna da "
              "ekle (yönetici parolası istenir)",
        "pt_BR": "Adicionar também os certificados de AC (raiz/intermediários) da "
                 "cadeia ao repositório de confiança do sistema (requer senha de "
                 "administrador)",
    },
    "rescan": {"en": "Rescan", "tr": "Yeniden tara", "pt_BR": "Procurar novamente"},
    "install_btn": {"en": "  Install Certificate", "tr": "  Sertifikayı Yükle",
                    "pt_BR": "  Instalar Certificado"},
    "choose_cert": {"en": "Choose certificate", "tr": "Sertifika seç",
                    "pt_BR": "Escolher certificado"},
    "file_filter": {
        "en": "PKCS#12 certificates (*.pfx *.p12 *.PFX *.P12);;All files (*)",
        "tr": "PKCS#12 sertifikaları (*.pfx *.p12 *.PFX *.P12);;Tüm dosyalar (*)",
        "pt_BR": "Certificados PKCS#12 (*.pfx *.p12 *.PFX *.P12);;Todos os arquivos (*)",
    },
    "invalid_file": {
        "en": "Please choose a valid PFX/P12 file.",
        "tr": "Lütfen geçerli bir PFX/P12 dosyası seçin.",
        "pt_BR": "Escolha um arquivo PFX/P12 válido.",
    },
    "owner": {"en": "Subject", "tr": "Sahibi", "pt_BR": "Titular"},
    "issuer": {"en": "Issuer", "tr": "Veren", "pt_BR": "Emissor"},
    "validity": {"en": "Validity", "tr": "Geçerlilik", "pt_BR": "Validade"},
    "serial": {"en": "Serial", "tr": "Seri no", "pt_BR": "Número de série"},
    "chain_count": {
        "en": "The chain contains {n} CA certificate(s).",
        "tr": "Zincirde {n} CA sertifikası var.",
        "pt_BR": "A cadeia contém {n} certificado(s) de AC.",
    },
    "pw_ok": {"en": "Password is correct.", "tr": "Parola doğru.",
              "pt_BR": "Senha correta."},
    "pick_target": {"en": "Select at least one target.",
                    "tr": "En az bir hedef seçin.",
                    "pt_BR": "Selecione pelo menos um destino."},
    "sys_store": {"en": "System trust store", "tr": "Sistem güven deposu",
                  "pt_BR": "Repositório de confiança do sistema"},
    "no_ca": {"en": "the PFX contains no CA certificate.",
              "tr": "PFX içinde CA sertifikası yok.",
              "pt_BR": "o PFX não contém certificado de AC."},
    "installed_ok": {"en": "✔ Installed:", "tr": "✔ Yüklendi:",
                     "pt_BR": "✔ Instalado:"},
    "error": {"en": "❌ Error:", "tr": "❌ Hata:", "pt_BR": "❌ Erro:"},
    "restart_browsers": {
        "en": "Restart your browsers for the changes to take effect.",
        "tr": "Değişikliklerin görünmesi için tarayıcıları yeniden başlatın.",
        "pt_BR": "Reinicie os navegadores para que as alterações tenham efeito.",
    },
    "installed_label": {
        "en": "Personal certificates installed together with their private key:",
        "tr": "Özel anahtarıyla birlikte yüklü kişisel sertifikalar:",
        "pt_BR": "Certificados pessoais instalados com a chave privada:",
    },
    "col_cert": {"en": "Certificate", "tr": "Sertifika", "pt_BR": "Certificado"},
    "col_loc": {"en": "Location", "tr": "Konum", "pt_BR": "Local"},
    "col_expires": {"en": "Expires", "tr": "Geçerlilik sonu", "pt_BR": "Expira em"},
    "refresh": {"en": "Refresh", "tr": "Yenile", "pt_BR": "Atualizar"},
    "delete_sel": {"en": "Delete selected", "tr": "Seçileni sil",
                   "pt_BR": "Excluir selecionado"},
    "confirm_delete": {
        "en": "Permanently delete the certificate “{name}” and its private key "
              "from\n{loc}?\n\nThis cannot be undone (your PFX file is not deleted).",
        "tr": "“{name}” sertifikası ve özel anahtarı\n{loc}\nkonumundan kalıcı "
              "olarak silinsin mi?\n\nBu işlem geri alınamaz (PFX dosyanız silinmez).",
        "pt_BR": "Excluir permanentemente o certificado “{name}” e sua chave "
                 "privada de\n{loc}?\n\nIsso não pode ser desfeito (seu arquivo "
                 "PFX não é excluído).",
    },
    "delete_failed": {"en": "Could not delete:\n{err}", "tr": "Silinemedi:\n{err}",
                      "pt_BR": "Não foi possível excluir:\n{err}"},
    "missing_tools": {
        "en": "Missing tools: {tools}\n\nInstall the 'nss' and 'openssl' packages.",
        "tr": "Eksik araçlar: {tools}\n\n'nss' ve 'openssl' paketlerini kurun.",
        "pt_BR": "Ferramentas ausentes: {tools}\n\nInstale os pacotes 'nss' e 'openssl'.",
    },
    # Database labels
    "db_chromium": {
        "en": "Chrome / Chromium / Edge / Brave / Vivaldi (system)",
        "tr": "Chrome / Chromium / Edge / Brave / Vivaldi (sistem)",
        "pt_BR": "Chrome / Chromium / Edge / Brave / Vivaldi (sistema)",
    },
    "profile": {"en": "profile", "tr": "profil", "pt_BR": "perfil"},
    "firefox_derivative": {"en": "Firefox derivative", "tr": "Firefox türevi",
                           "pt_BR": "Derivado do Firefox"},
    # Errors
    "err_password": {"en": "Wrong password.", "tr": "Parola yanlış.",
                     "pt_BR": "Senha incorreta."},
    "err_read": {"en": "Could not read the PFX file:\n{err}",
                 "tr": "PFX dosyası okunamadı:\n{err}",
                 "pt_BR": "Não foi possível ler o arquivo PFX:\n{err}"},
    "err_locked": {
        "en": "The database is locked – close the browser and try again.",
        "tr": "Veritabanı kilitli – tarayıcıyı kapatıp tekrar deneyin.",
        "pt_BR": "O banco de dados está bloqueado – feche o navegador e tente novamente.",
    },
    "err_auth": {"en": "Authorization was cancelled.",
                 "tr": "Yetkilendirme iptal edildi.",
                 "pt_BR": "A autorização foi cancelada."},
    # About / updates
    "version": {"en": "Version {v}", "tr": "Sürüm {v}", "pt_BR": "Versão {v}"},
    "about_text": {
        "en": "Installs PFX/P12 certificates into browsers and the system "
              "without using the terminal.",
        "tr": "PFX/P12 sertifikalarını terminal kullanmadan tarayıcılara ve "
              "sisteme yükler.",
        "pt_BR": "Instala certificados PFX/P12 nos navegadores e no sistema "
                 "sem usar o terminal.",
    },
    "auto_check": {"en": "Check for updates at startup",
                   "tr": "Açılışta güncellemeleri denetle",
                   "pt_BR": "Verificar atualizações ao iniciar"},
    "check_updates": {"en": "Check for updates now",
                      "tr": "Şimdi güncellemeleri denetle",
                      "pt_BR": "Verificar atualizações agora"},
    "checking": {"en": "Checking for updates…",
                 "tr": "Güncellemeler denetleniyor…",
                 "pt_BR": "Verificando atualizações…"},
    "up_to_date": {"en": "You are using the latest version ({v}).",
                   "tr": "En güncel sürümü kullanıyorsunuz ({v}).",
                   "pt_BR": "Você está usando a versão mais recente ({v})."},
    "update_failed_check": {
        "en": "Could not check for updates:\n{err}",
        "tr": "Güncelleme denetlenemedi:\n{err}",
        "pt_BR": "Não foi possível verificar atualizações:\n{err}",
    },
    "update_available": {
        "en": "A new version is available: {new}\n(installed: {cur})\n\n"
              "{notes}\nDo you want to update now?",
        "tr": "Yeni bir sürüm çıktı: {new}\n(kurulu sürüm: {cur})\n\n"
              "{notes}\nŞimdi güncellemek ister misiniz?",
        "pt_BR": "Uma nova versão está disponível: {new}\n(instalada: {cur})\n\n"
                 "{notes}\nDeseja atualizar agora?",
    },
    "update_title": {"en": "Update available", "tr": "Güncelleme var",
                     "pt_BR": "Atualização disponível"},
    "downloading": {"en": "Downloading the update…",
                    "tr": "Güncelleme indiriliyor…",
                    "pt_BR": "Baixando a atualização…"},
    "installing": {"en": "Installing the update (administrator password required)…",
                   "tr": "Güncelleme kuruluyor (yönetici parolası istenir)…",
                   "pt_BR": "Instalando a atualização (requer senha de administrador)…"},
    "update_done": {
        "en": "Updated to version {v}. The application will now restart.",
        "tr": "{v} sürümüne güncellendi. Uygulama şimdi yeniden başlatılacak.",
        "pt_BR": "Atualizado para a versão {v}. O aplicativo será reiniciado agora.",
    },
    "update_error": {"en": "Update failed:\n{err}",
                     "tr": "Güncelleme başarısız:\n{err}",
                     "pt_BR": "Falha na atualização:\n{err}"},
    "err_checksum": {"en": "Checksum of the downloaded file does not match.",
                     "tr": "İndirilen dosyanın sağlama toplamı uyuşmuyor.",
                     "pt_BR": "A soma de verificação do arquivo baixado não confere."},
    "err_no_asset": {"en": "The release contains no package file.",
                     "tr": "Sürümde paket dosyası bulunamadı.",
                     "pt_BR": "A versão não contém arquivo de pacote."},
    "manual_update": {
        "en": "This copy was not installed as a system package, so it cannot "
              "update itself. Open the download page?",
        "tr": "Bu kopya sistem paketi olarak kurulmadığı için kendini "
              "güncelleyemez. İndirme sayfası açılsın mı?",
        "pt_BR": "Esta cópia não foi instalada como pacote do sistema, então não "
                 "pode se atualizar sozinha. Abrir a página de download?",
    },
    # Export
    "export_sel": {"en": "Export as PFX…", "tr": "PFX olarak dışa aktar…",
                   "pt_BR": "Exportar como PFX…"},
    "export_title": {"en": "Export certificate", "tr": "Sertifikayı dışa aktar",
                     "pt_BR": "Exportar certificado"},
    "export_info": {
        "en": "The certificate “{name}” will be saved together with its private key. "
              "Choose a password to protect the PFX file:",
        "tr": "“{name}” sertifikası özel anahtarıyla birlikte kaydedilecek. "
              "PFX dosyasını korumak için bir parola belirleyin:",
        "pt_BR": "O certificado “{name}” será salvo junto com a chave privada. "
                 "Escolha uma senha para proteger o arquivo PFX:",
    },
    "new_password": {"en": "New password:", "tr": "Yeni parola:",
                     "pt_BR": "Nova senha:"},
    "repeat_password": {"en": "Repeat password:", "tr": "Parola (tekrar):",
                        "pt_BR": "Repita a senha:"},
    "legacy_export": {
        "en": "Compatible with older systems (Windows 7, old Java) – weaker encryption",
        "tr": "Eski sistemlerle uyumlu (Windows 7, eski Java) – daha zayıf şifreleme",
        "pt_BR": "Compatível com sistemas antigos (Windows 7, Java antigo) – "
                 "criptografia mais fraca",
    },
    "pw_empty": {"en": "The password cannot be empty.",
                 "tr": "Parola boş olamaz.",
                 "pt_BR": "A senha não pode ficar vazia."},
    "pw_mismatch": {"en": "The passwords do not match.",
                    "tr": "Parolalar eşleşmiyor.",
                    "pt_BR": "As senhas não coincidem."},
    "save_pfx": {"en": "Save PFX file", "tr": "PFX dosyasını kaydet",
                 "pt_BR": "Salvar arquivo PFX"},
    "export_done": {
        "en": "The certificate was saved to:\n{path}\n\nKeep this file and its "
              "password safe – anyone who has both can use your certificate.",
        "tr": "Sertifika şuraya kaydedildi:\n{path}\n\nBu dosyayı ve parolasını "
              "güvenli saklayın – ikisine birden sahip olan herkes sertifikanızı "
              "kullanabilir.",
        "pt_BR": "O certificado foi salvo em:\n{path}\n\nGuarde este arquivo e a "
                 "senha em segurança – quem tiver os dois pode usar seu certificado.",
    },
    "export_failed": {"en": "Export failed:\n{err}",
                      "tr": "Dışa aktarma başarısız:\n{err}",
                      "pt_BR": "Falha na exportação:\n{err}"},
    "select_cert_first": {"en": "Select a certificate in the list first.",
                          "tr": "Önce listeden bir sertifika seçin.",
                          "pt_BR": "Selecione primeiro um certificado na lista."},
    "open_project": {"en": "Project page", "tr": "Proje sayfası",
                     "pt_BR": "Página do projeto"},
}

_lang = "en"


def detect_language() -> str:
    name = QLocale.system().name()  # e.g. tr_TR, pt_BR, en_US
    if name.startswith("tr"):
        return "tr"
    if name.startswith("pt"):
        return "pt_BR"
    return "en"


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in LANGUAGES else "en"


def tr(key: str, **kw) -> str:
    entry = STRINGS[key]
    text = entry.get(_lang) or entry["en"]
    return text.format(**kw) if kw else text


def settings() -> QSettings:
    return QSettings("pfx-yukleyici", "pfx-yukleyici")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    env = dict(os.environ, LC_ALL="C.UTF-8")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, **kw)


class SecretFile:
    """Temporary 0600 file so passwords never appear on the command line."""

    def __init__(self, secret: str):
        base = os.environ.get("XDG_RUNTIME_DIR") or None
        fd, self.path = tempfile.mkstemp(prefix="pfx-", dir=base)
        with os.fdopen(fd, "w") as f:
            f.write(secret + "\n")

    def __enter__(self):
        return self.path

    def __exit__(self, *exc):
        try:
            os.unlink(self.path)
        except OSError:
            pass


@dataclass
class NssDb:
    label: str
    path: Path
    default: bool = True

    @property
    def spec(self) -> str:
        return f"sql:{self.path}"


class PfxError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Locating NSS databases
# --------------------------------------------------------------------------- #
def _walk_for(root: Path, filename: str, max_depth: int):
    """Search for a file up to a depth without following symlinks."""
    if not root.is_dir():
        return
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if len(Path(dirpath).parts) - root_depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in ("Crash Reports", "cache2", "storage")]
        if filename in filenames:
            yield Path(dirpath) / filename


def _browser_name(path: Path) -> str:
    s = str(path).lower()
    for key, name in (
        ("librewolf", "LibreWolf"),
        ("waterfox", "Waterfox"),
        ("floorp", "Floorp"),
        ("zen", "Zen Browser"),
        ("thunderbird", "Thunderbird"),
        ("mozilla", "Firefox"),
    ):
        if key in s:
            return name
    return tr("firefox_derivative")


def find_databases() -> list[NssDb]:
    dbs: list[NssDb] = []
    seen: set[Path] = set()

    def add(label: str, path: Path, default: bool = True):
        try:
            real = path.resolve()
        except OSError:
            return
        if real in seen:
            return
        seen.add(real)
        dbs.append(NssDb(label, path, default))

    # Chromium-based browsers (native) share one NSS store
    add(tr("db_chromium"), HOME / ".pki" / "nssdb")

    flatpak_root = HOME / ".var" / "app"
    roots = [HOME]
    if flatpak_root.is_dir():
        roots += sorted(p for p in flatpak_root.iterdir() if p.is_dir())

    # Flatpak Chromium derivatives
    for app in roots[1:]:
        db = app / ".pki" / "nssdb"
        if (db / "cert9.db").exists():
            add(f"{app.name} (Flatpak)", db)

    # Firefox and derivatives: read profiles from profiles.ini
    ff_bases = [
        ".mozilla", ".config/mozilla", ".librewolf", ".config/librewolf",
        ".waterfox", ".floorp", ".zen", ".thunderbird",
    ]
    for root in roots:
        for rel in ff_bases:
            for ini in _walk_for(root / rel, "profiles.ini", 3):
                cp = configparser.RawConfigParser()
                try:
                    cp.read(ini, encoding="utf-8")
                except (configparser.Error, OSError):
                    continue
                for sect in cp.sections():
                    if not sect.startswith("Profile") or "Path" not in cp[sect]:
                        continue
                    p = cp[sect]["Path"]
                    rel_flag = cp[sect].get("IsRelative", "1") == "1"
                    prof = (ini.parent / p) if rel_flag else Path(p)
                    if not (prof / "cert9.db").exists():
                        continue
                    name = cp[sect].get("Name", prof.name)
                    flat = " (Flatpak)" if root != HOME else ""
                    add(f"{_browser_name(prof)}{flat} – {tr('profile')}: {name}", prof)

    return dbs


# --------------------------------------------------------------------------- #
# PFX operations
# --------------------------------------------------------------------------- #
def _openssl_pkcs12(pfx: Path, password: str, extra: list[str]) -> str:
    with SecretFile(password) as pw:
        for legacy in ([], ["-legacy"]):
            r = run(["openssl", "pkcs12", "-in", str(pfx), "-passin",
                     f"file:{pw}", "-nokeys", *legacy, *extra])
            if r.returncode == 0:
                return r.stdout
        err = r.stderr.lower()
    if "mac verify" in err or "invalid password" in err or "bad decrypt" in err:
        raise PfxError(tr("err_password"))
    raise PfxError(tr("err_read", err=r.stderr.strip()[-600:]))


def _split_pem(text: str) -> list[str]:
    return re.findall(r"-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----",
                      text, re.S)


def cert_info(pem: str) -> dict[str, str]:
    r = run(["openssl", "x509", "-noout", "-subject", "-issuer", "-startdate",
             "-enddate", "-serial", "-nameopt", "oneline,-esc_msb"],
            input=pem)
    info = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip()
    return info


def read_pfx(pfx: Path, password: str) -> tuple[list[str], list[str]]:
    """Return (user certificates, CA certificates) as PEM lists."""
    clc = _split_pem(_openssl_pkcs12(pfx, password, ["-clcerts"]))
    cas = _split_pem(_openssl_pkcs12(pfx, password, ["-cacerts"]))
    return clc, cas


def import_into(db: NssDb, pfx: Path, password: str) -> str:
    db.path.mkdir(parents=True, exist_ok=True)
    if not (db.path / "cert9.db").exists():
        r = run(["certutil", "-N", "-d", db.spec, "--empty-password"])
        if r.returncode != 0:
            raise PfxError(r.stderr.strip())
    cmd = ["pk12util", "-i", str(pfx), "-d", db.spec, "-K", ""]
    if password:
        with SecretFile(password) as pw:
            r = run(cmd + ["-w", pw])
    else:
        r = run(cmd + ["-W", ""])
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        if "SEC_ERROR_BAD_PASSWORD" in out or "PKCS12 decode not verified" in out:
            raise PfxError(tr("err_password"))
        if "SEC_ERROR_BAD_DATABASE" in out or "SEC_ERROR_LOCKED_DATABASE" in out:
            raise PfxError(tr("err_locked"))
        raise PfxError(out[-600:])
    return out


def install_system_ca(cas: list[str]) -> None:
    if not cas:
        return
    with tempfile.TemporaryDirectory() as td:
        files = []
        for i, pem in enumerate(cas):
            f = Path(td) / f"ca{i}.pem"
            f.write_text(pem + "\n")
            files.append(str(f))
        os.chmod(td, 0o755)
        for f in files:
            os.chmod(f, 0o644)
        script = "set -e; for f in \"$@\"; do trust anchor --store \"$f\"; done"
        r = run(["pkexec", "/bin/sh", "-c", script, "sh", *files])
        if r.returncode in (126, 127):
            raise PfxError(tr("err_auth"))
        if r.returncode != 0:
            raise PfxError(r.stderr.strip()[-600:])


@dataclass
class InstalledCert:
    nickname: str
    trust: str
    db: NssDb


def list_user_certs(db: NssDb) -> list[InstalledCert]:
    """List personal certificates (those with a private key)."""
    r = run(["certutil", "-L", "-d", db.spec])
    res = []
    for line in r.stdout.splitlines()[4:]:
        # Long nicknames are separated from the trust flags by a single space,
        # so take the trust flags as the last token.
        m = re.match(r"^(.*\S)\s+([A-Za-z]*,[A-Za-z]*,[A-Za-z]*)\s*$", line)
        if m and "u" in m.group(2):
            res.append(InstalledCert(m.group(1), m.group(2), db))
    return res


def cert_expiry(c: InstalledCert) -> str:
    r = run(["certutil", "-L", "-d", c.db.spec, "-n", c.nickname, "-a"])
    pems = _split_pem(r.stdout)
    return cert_info(pems[0]).get("notAfter", "") if pems else ""


def display_name(nickname: str) -> str:
    return nickname.split(":", 1)[1] if nickname.startswith("NSS Certificate DB:") else nickname


def export_cert(c: InstalledCert, target: Path, password: str,
                legacy: bool = False) -> None:
    """Export a certificate with its private key (and chain) as PKCS#12."""
    if not password:
        raise PfxError(tr("pw_empty"))
    cmd = ["pk12util", "-o", str(target), "-n", c.nickname, "-d", c.db.spec, "-K", ""]
    if legacy:
        des3 = "PKCS #12 V2 PBE With SHA-1 And 3KEY Triple DES-CBC"
        cmd += ["-c", des3, "-C", des3, "-M", "SHA-1"]
    old_umask = os.umask(0o077)  # the file contains a private key
    try:
        with SecretFile(password) as pw:
            r = run(cmd + ["-w", pw])
    finally:
        os.umask(old_umask)
    if r.returncode != 0:
        try:
            target.unlink()
        except OSError:
            pass
        raise PfxError((r.stderr or r.stdout).strip()[-600:])


def safe_filename(name: str) -> str:
    name = re.sub(r"\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", "", name)
    name = re.sub(r'[\\/:*?"<>|]+', "_", name).strip(" ._")
    return name or "certificate"


class ExportDialog(QDialog):
    def __init__(self, parent: QWidget, name: str):
        super().__init__(parent)
        self.setWindowTitle(tr("export_title"))
        lay = QVBoxLayout(self)
        info = QLabel(tr("export_info", name=name))
        info.setWordWrap(True)
        lay.addWidget(info)
        form = QFormLayout()
        self.pw1 = QLineEdit()
        self.pw1.setEchoMode(QLineEdit.Password)
        self.pw2 = QLineEdit()
        self.pw2.setEchoMode(QLineEdit.Password)
        form.addRow(tr("new_password"), self.pw1)
        form.addRow(tr("repeat_password"), self.pw2)
        lay.addLayout(form)
        self.legacy = QCheckBox(tr("legacy_export"))
        lay.addWidget(self.legacy)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.resize(460, self.sizeHint().height())

    def validate(self):
        if not self.pw1.text():
            QMessageBox.warning(self, tr("app_name"), tr("pw_empty"))
        elif self.pw1.text() != self.pw2.text():
            QMessageBox.warning(self, tr("app_name"), tr("pw_mismatch"))
        else:
            self.accept()


def delete_cert(c: InstalledCert) -> None:
    r = run(["certutil", "-F", "-n", c.nickname, "-d", c.db.spec])
    if r.returncode != 0:
        r = run(["certutil", "-D", "-n", c.nickname, "-d", c.db.spec])
        if r.returncode != 0:
            raise PfxError(r.stderr.strip())


# --------------------------------------------------------------------------- #
# Updates (GitHub releases)
# --------------------------------------------------------------------------- #
@dataclass
class Release:
    version: str
    notes: str
    page: str
    asset_url: str | None
    asset_name: str | None
    sha256: str | None


def parse_version(v: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", v)
    return tuple(int(n) for n in nums[:3]) or (0,)


def is_newer(remote: str, local: str = __version__) -> bool:
    return parse_version(remote) > parse_version(local)


def _http_get(url: str, accept: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": f"pfx-yukleyici/{__version__}",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_latest_release() -> Release:
    data = json.loads(_http_get(
        f"https://api.github.com/repos/{REPO}/releases/latest",
        "application/vnd.github+json"))
    asset = next((a for a in data.get("assets", [])
                  if a.get("name", "").endswith(".pkg.tar.zst")), None)
    sha = None
    if asset and str(asset.get("digest", "")).startswith("sha256:"):
        sha = asset["digest"].split(":", 1)[1]
    return Release(
        version=data.get("tag_name", "0").lstrip("vV"),
        notes=(data.get("body") or "").strip(),
        page=data.get("html_url", f"https://github.com/{REPO}/releases"),
        asset_url=asset.get("browser_download_url") if asset else None,
        asset_name=asset.get("name") if asset else None,
        sha256=sha,
    )


def download_release(rel: Release) -> Path:
    if not rel.asset_url or not rel.asset_name:
        raise PfxError(tr("err_no_asset"))
    if not rel.asset_url.startswith("https://github.com/"):
        raise PfxError(rel.asset_url)
    data = _http_get(rel.asset_url, "application/octet-stream")
    if rel.sha256 and hashlib.sha256(data).hexdigest() != rel.sha256.lower():
        raise PfxError(tr("err_checksum"))
    d = Path(tempfile.mkdtemp(prefix="pfx-update-"))
    target = d / Path(rel.asset_name).name
    target.write_bytes(data)
    return target


def install_package(pkg: Path) -> None:
    r = run(["pkexec", "/usr/bin/pacman", "-U", "--noconfirm", str(pkg)])
    if r.returncode in (126, 127):
        raise PfxError(tr("err_auth"))
    if r.returncode != 0:
        raise PfxError((r.stderr or r.stdout).strip()[-800:])


def installed_as_package() -> bool:
    try:
        me = Path(sys.argv[0]).resolve()
    except OSError:
        return False
    return me == INSTALLED_PATH and shutil.which("pacman") is not None


class Worker(QThread):
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args):
        super().__init__()
        self.fn, self.args = fn, args

    def run(self):
        try:
            self.done.emit(self.fn(*self.args))
        except Exception as e:  # noqa: BLE001 – shown to the user
            self.failed.emit(str(e))


class Updater:
    """Checks GitHub for a newer release and installs it on approval."""

    def __init__(self, parent: QWidget):
        self.parent = parent
        self.worker: Worker | None = None
        self.progress: QProgressDialog | None = None

    def check(self, silent: bool):
        if self.worker and self.worker.isRunning():
            return
        if not silent:
            self._show_progress(tr("checking"))
        self.worker = Worker(fetch_latest_release)
        self.worker.done.connect(lambda rel: self._on_checked(rel, silent))
        self.worker.failed.connect(lambda err: self._on_check_failed(err, silent))
        self.worker.start()

    def _show_progress(self, text: str):
        if self.progress is None:
            self.progress = QProgressDialog(self.parent)
            self.progress.setWindowTitle(tr("app_name"))
            self.progress.setRange(0, 0)
            self.progress.setCancelButton(None)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.setMinimumDuration(0)
        self.progress.setLabelText(text)
        self.progress.show()

    def _hide_progress(self):
        if self.progress:
            self.progress.hide()

    def _on_check_failed(self, err: str, silent: bool):
        self._hide_progress()
        if not silent:
            QMessageBox.warning(self.parent, tr("app_name"),
                                tr("update_failed_check", err=err))

    def _on_checked(self, rel: Release, silent: bool):
        self._hide_progress()
        if not is_newer(rel.version):
            if not silent:
                QMessageBox.information(self.parent, tr("app_name"),
                                        tr("up_to_date", v=__version__))
            return
        notes = rel.notes[:800] + ("…" if len(rel.notes) > 800 else "")
        notes = notes + "\n" if notes else ""
        ans = QMessageBox.question(
            self.parent, tr("update_title"),
            tr("update_available", new=rel.version, cur=__version__, notes=notes))
        if ans != QMessageBox.Yes:
            return
        if not installed_as_package() or not rel.asset_url:
            if QMessageBox.question(self.parent, tr("update_title"),
                                    tr("manual_update")) == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl(rel.page))
            return
        self._show_progress(tr("downloading"))
        self.worker = Worker(download_release, rel)
        self.worker.done.connect(lambda pkg: self._install(pkg, rel))
        self.worker.failed.connect(self._on_update_failed)
        self.worker.start()

    def _install(self, pkg: Path, rel: Release):
        self._show_progress(tr("installing"))
        self.worker = Worker(install_package, pkg)
        self.worker.done.connect(lambda _: self._on_installed(pkg, rel))
        self.worker.failed.connect(self._on_update_failed)
        self.worker.start()

    def _on_update_failed(self, err: str):
        self._hide_progress()
        QMessageBox.warning(self.parent, tr("app_name"), tr("update_error", err=err))

    def _on_installed(self, pkg: Path, rel: Release):
        self._hide_progress()
        shutil.rmtree(pkg.parent, ignore_errors=True)
        QMessageBox.information(self.parent, tr("app_name"),
                                tr("update_done", v=rel.version))
        args = [a for a in sys.argv[1:] if Path(a).is_file()]
        os.execv(sys.executable, [sys.executable, str(INSTALLED_PATH), *args])


# --------------------------------------------------------------------------- #
# User interface
# --------------------------------------------------------------------------- #
class DropLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setPlaceholderText(tr("file_placeholder"))

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            self.setText(urls[0].toLocalFile())


class InstallTab(QWidget):
    def __init__(self, initial_file: str | None, on_installed):
        super().__init__()
        self.on_installed = on_installed
        lay = QVBoxLayout(self)

        fbox = QGroupBox(tr("grp_file"))
        fl = QFormLayout(fbox)
        row = QHBoxLayout()
        self.file_edit = DropLineEdit()
        browse = QPushButton(QIcon.fromTheme("document-open"), tr("browse"))
        browse.clicked.connect(self.browse)
        row.addWidget(self.file_edit)
        row.addWidget(browse)
        fl.addRow(tr("file"), row)

        prow = QHBoxLayout()
        self.pw_edit = QLineEdit()
        self.pw_edit.setEchoMode(QLineEdit.Password)
        self.pw_edit.setPlaceholderText(tr("pw_placeholder"))
        self.pw_edit.returnPressed.connect(self.check)
        show = QCheckBox(tr("show"))
        show.toggled.connect(lambda on: self.pw_edit.setEchoMode(
            QLineEdit.Normal if on else QLineEdit.Password))
        check_btn = QPushButton(tr("check"))
        check_btn.clicked.connect(self.check)
        prow.addWidget(self.pw_edit)
        prow.addWidget(show)
        prow.addWidget(check_btn)
        fl.addRow(tr("password"), prow)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        fl.addRow(self.info)
        lay.addWidget(fbox)

        tbox = QGroupBox(tr("grp_targets"))
        tl = QVBoxLayout(tbox)
        self.targets = QListWidget()
        tl.addWidget(self.targets)
        self.sys_ca = QCheckBox(tr("sys_ca"))
        tl.addWidget(self.sys_ca)
        refresh = QPushButton(QIcon.fromTheme("view-refresh"), tr("rescan"))
        refresh.clicked.connect(self.load_targets)
        tl.addWidget(refresh, alignment=Qt.AlignRight)
        lay.addWidget(tbox, 1)

        self.install_btn = QPushButton(QIcon.fromTheme("dialog-ok-apply"),
                                       tr("install_btn"))
        self.install_btn.setMinimumHeight(40)
        f = self.install_btn.font()
        f.setBold(True)
        self.install_btn.setFont(f)
        self.install_btn.clicked.connect(self.install)
        lay.addWidget(self.install_btn)

        self.load_targets()
        if initial_file:
            self.file_edit.setText(initial_file)
            self.pw_edit.setFocus()

    def load_targets(self):
        self.targets.clear()
        for db in find_databases():
            it = QListWidgetItem(f"{db.label}\n    {db.path}")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if db.default else Qt.Unchecked)
            it.setData(Qt.UserRole, db)
            self.targets.addItem(it)

    def browse(self):
        cur = self.file_edit.text()
        start = str(Path(cur).parent) if cur else str(HOME)
        fn, _ = QFileDialog.getOpenFileName(self, tr("choose_cert"), start,
                                            tr("file_filter"))
        if fn:
            self.file_edit.setText(fn)
            self.info.clear()
            self.pw_edit.setFocus()

    def _pfx(self) -> Path | None:
        p = Path(self.file_edit.text().strip())
        if not p.is_file():
            QMessageBox.warning(self, tr("app_name"), tr("invalid_file"))
            return None
        return p

    def check(self) -> tuple[list[str], list[str]] | None:
        pfx = self._pfx()
        if not pfx:
            return None
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            clc, cas = read_pfx(pfx, self.pw_edit.text())
        except PfxError as e:
            QApplication.restoreOverrideCursor()
            self.info.setText(f"<span style='color:#c0392b'>❌ {e}</span>")
            return None
        QApplication.restoreOverrideCursor()
        lines = []
        for pem in clc:
            i = cert_info(pem)
            lines.append(
                f"<b>{tr('owner')}:</b> {i.get('subject', '?')}<br>"
                f"<b>{tr('issuer')}:</b> {i.get('issuer', '?')}<br>"
                f"<b>{tr('validity')}:</b> {i.get('notBefore', '?')} → "
                f"{i.get('notAfter', '?')}<br>"
                f"<b>{tr('serial')}:</b> {i.get('serial', '?')}")
        lines.append(f"<i>{tr('chain_count', n=len(cas))}</i>")
        self.info.setText(f"<span style='color:#27ae60'>✔ {tr('pw_ok')}</span><br>"
                          + "<br><br>".join(lines))
        return clc, cas

    def install(self):
        res = self.check()
        if res is None:
            return
        _, cas = res
        pfx = self._pfx()
        sel = [self.targets.item(i).data(Qt.UserRole)
               for i in range(self.targets.count())
               if self.targets.item(i).checkState() == Qt.Checked]
        if not sel and not self.sys_ca.isChecked():
            QMessageBox.warning(self, tr("app_name"), tr("pick_target"))
            return

        ok, fail = [], []
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for db in sel:
            try:
                import_into(db, pfx, self.pw_edit.text())
                ok.append(db.label)
            except PfxError as e:
                fail.append(f"{db.label}: {e}")
        QApplication.restoreOverrideCursor()

        if self.sys_ca.isChecked():
            if not cas:
                fail.append(f"{tr('sys_store')}: {tr('no_ca')}")
            else:
                try:
                    install_system_ca(cas)
                    ok.append(f"{tr('sys_store')} ({len(cas)} CA)")
                except PfxError as e:
                    fail.append(f"{tr('sys_store')}: {e}")

        msg = ""
        if ok:
            msg += tr("installed_ok") + "\n  • " + "\n  • ".join(ok) + "\n\n"
        if fail:
            msg += tr("error") + "\n  • " + "\n  • ".join(fail) + "\n\n"
        if ok:
            msg += tr("restart_browsers")
        (QMessageBox.warning if fail else QMessageBox.information)(
            self, tr("app_name"), msg)
        if ok:
            self.pw_edit.clear()
            self.on_installed()


class ManageTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(tr("installed_label")))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("col_cert"), tr("col_expires"), tr("col_loc")])
        self.tree.setColumnWidth(0, 360)
        lay.addWidget(self.tree, 1)
        row = QHBoxLayout()
        r = QPushButton(QIcon.fromTheme("view-refresh"), tr("refresh"))
        r.clicked.connect(self.refresh)
        d = QPushButton(QIcon.fromTheme("edit-delete"), tr("delete_sel"))
        d.clicked.connect(self.delete)
        e = QPushButton(QIcon.fromTheme("document-export",
                                        QIcon.fromTheme("document-save-as")),
                        tr("export_sel"))
        e.clicked.connect(self.export)
        row.addStretch(1)
        row.addWidget(r)
        row.addWidget(e)
        row.addWidget(d)
        lay.addLayout(row)
        self.refresh()

    def refresh(self):
        self.tree.clear()
        for db in find_databases():
            if not (db.path / "cert9.db").exists():
                continue
            for c in list_user_certs(db):
                it = QTreeWidgetItem([display_name(c.nickname), cert_expiry(c), db.label])
                it.setToolTip(0, c.nickname)
                it.setToolTip(2, str(db.path))
                it.setData(0, Qt.UserRole, c)
                self.tree.addTopLevelItem(it)

    def export(self):
        it = self.tree.currentItem()
        if not it:
            QMessageBox.information(self, tr("app_name"), tr("select_cert_first"))
            return
        c: InstalledCert = it.data(0, Qt.UserRole)
        name = display_name(c.nickname)
        dlg = ExportDialog(self, name)
        if dlg.exec() != QDialog.Accepted:
            return
        default = str(HOME / f"{safe_filename(name)}.pfx")
        fn, _ = QFileDialog.getSaveFileName(self, tr("save_pfx"), default,
                                            tr("file_filter"))
        if not fn:
            return
        target = Path(fn)
        if target.suffix.lower() not in (".pfx", ".p12"):
            target = target.with_suffix(target.suffix + ".pfx")
        try:
            export_cert(c, target, dlg.pw1.text(), dlg.legacy.isChecked())
        except PfxError as err:
            QMessageBox.warning(self, tr("app_name"), tr("export_failed", err=err))
            return
        QMessageBox.information(self, tr("app_name"), tr("export_done", path=target))

    def delete(self):
        it = self.tree.currentItem()
        if not it:
            return
        c: InstalledCert = it.data(0, Qt.UserRole)
        if QMessageBox.question(
                self, tr("app_name"),
                tr("confirm_delete", name=display_name(c.nickname), loc=c.db.label)) != QMessageBox.Yes:
            return
        try:
            delete_cert(c)
        except PfxError as e:
            QMessageBox.warning(self, tr("app_name"), tr("delete_failed", err=e))
        self.refresh()


class AboutTab(QWidget):
    def __init__(self, updater: Updater):
        super().__init__()
        lay = QVBoxLayout(self)
        title = QLabel(f"<h2>{tr('app_name')}</h2>{tr('version', v=__version__)}")
        lay.addWidget(title)
        desc = QLabel(tr("about_text"))
        desc.setWordWrap(True)
        lay.addWidget(desc)
        link = QLabel(f"<a href='https://github.com/{REPO}'>{tr('open_project')}: "
                      f"github.com/{REPO}</a>")
        link.setOpenExternalLinks(True)
        lay.addWidget(link)
        lay.addSpacing(12)

        s = settings()
        self.auto = QCheckBox(tr("auto_check"))
        self.auto.setChecked(s.value("auto_update_check", True, type=bool))
        self.auto.toggled.connect(lambda on: settings().setValue("auto_update_check", on))
        lay.addWidget(self.auto)
        btn = QPushButton(QIcon.fromTheme("system-software-update"), tr("check_updates"))
        btn.clicked.connect(lambda: updater.check(silent=False))
        lay.addWidget(btn, alignment=Qt.AlignLeft)
        lay.addStretch(1)


class MainWindow(QWidget):
    def __init__(self, initial_file: str | None):
        super().__init__()
        self.setWindowIcon(QIcon.fromTheme("application-pkcs12",
                                           QIcon.fromTheme("security-high")))
        self.resize(780, 660)
        self.updater = Updater(self)
        self.layout_ = QVBoxLayout(self)
        self.content: QWidget | None = None
        self.build(initial_file)

    def build(self, initial_file: str | None):
        if self.content is not None:
            self.layout_.removeWidget(self.content)
            self.content.deleteLater()
        self.setWindowTitle(tr("app_name"))

        self.content = QWidget()
        v = QVBoxLayout(self.content)
        v.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        top.addStretch(1)
        top.addWidget(QLabel(tr("language")))
        self.lang_box = QComboBox()
        for code, name in LANGUAGES.items():
            self.lang_box.addItem(name, code)
        self.lang_box.setCurrentIndex(list(LANGUAGES).index(_lang))
        self.lang_box.currentIndexChanged.connect(self.change_language)
        top.addWidget(self.lang_box)
        v.addLayout(top)

        tabs = QTabWidget()
        self.manage_tab = ManageTab()
        self.install_tab = InstallTab(initial_file, self.manage_tab.refresh)
        tabs.addTab(self.install_tab, QIcon.fromTheme("list-add"), tr("tab_install"))
        tabs.addTab(self.manage_tab, QIcon.fromTheme("view-certificate"),
                    tr("tab_installed"))
        tabs.addTab(AboutTab(self.updater), QIcon.fromTheme("help-about"),
                    tr("tab_about"))
        v.addWidget(tabs)
        self.layout_.addWidget(self.content)

    def change_language(self, idx: int):
        code = self.lang_box.itemData(idx)
        set_language(code)
        settings().setValue("language", code)
        current_file = self.install_tab.file_edit.text() or None
        self.build(current_file)


def main():
    app = QApplication(sys.argv)
    app.setDesktopFileName("pfx-yukleyici")
    set_language(settings().value("language", detect_language()))
    app.setApplicationName(tr("app_name"))

    missing = [c for c in ("pk12util", "certutil", "openssl") if not shutil.which(c)]
    if missing:
        QMessageBox.critical(None, tr("app_name"),
                             tr("missing_tools", tools=", ".join(missing)))
        return 1

    initial = None
    for a in sys.argv[1:]:
        if a.startswith("file://"):
            from urllib.parse import unquote, urlparse
            a = unquote(urlparse(a).path)
        if Path(a).is_file():
            initial = a
            break

    w = MainWindow(initial)
    w.show()
    if settings().value("auto_update_check", True, type=bool):
        QTimer.singleShot(1500, lambda: w.updater.check(silent=True))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
