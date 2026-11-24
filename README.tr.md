# PFX Sertifika Yükleyici

[English](README.md) · **Türkçe** · [Português (Brasil)](README.pt-BR.md)

**PFX / P12 (PKCS#12)** sertifikalarını (ör. e-imza, mali mühür veya istemci kimlik
doğrulama sertifikaları) **terminal kullanmadan** tarayıcılarınıza yükleyen küçük bir
Linux masaüstü uygulaması (CachyOS / Arch Linux için hazırlandı).

## Özellikler

- Dosyayı seçin ya da sürükleyip bırakın, parolayı girin, **Yükle**'ye tıklayın.
- Dosya yöneticisinde bir `.pfx` / `.p12` dosyasına çift tıklayınca uygulama o dosyayla açılır.
- Sertifika depolarını kendisi bulur:
  - Chrome / Chromium / Edge / Brave / Vivaldi (ortak NSS deposu `~/.pki/nssdb`)
  - Firefox, LibreWolf, Waterfox, Floorp, Zen, Thunderbird (tüm profiller, *profile-sync-daemon* dahil)
  - Flatpak tarayıcılar
- Yüklemeden önce parolayı doğrular ve sertifika bilgilerini (sahibi, veren, geçerlilik) gösterir.
- İsteğe bağlı olarak zincirdeki CA (kök/ara) sertifikalarını sistem güven deposuna ekler.
- Yüklü kişisel sertifikaları (geçerlilik sonuyla) listeler ve silmenizi sağlar.
- Yüklü bir sertifikayı özel anahtarıyla birlikte parolalı bir `.pfx` dosyası olarak **dışa aktarır** (isteğe bağlı olarak eski sistemlerle uyumlu biçimde).
- Eski (legacy) şifrelemeli PFX dosyalarını da destekler.
- Parolalar komut satırında görünmez.
- **İngilizce, Türkçe ve Brezilya Portekizcesi** dillerinde (sistem dilinden algılanır, uygulama içinden değiştirilebilir).
- **Otomatik güncelleme:** açılışta GitHub'da yeni sürüm olup olmadığını denetler; onaylarsanız indirip kurar ve yeniden başlar.

## Kurulum

1. [Releases](https://github.com/bariscagriyuce/pfx/releases) sayfasından en son
   `pfx-yukleyici-*.pkg.tar.zst` dosyasını indirin.
2. Paket yükleyicinizle açın ya da şu komutu çalıştırın:

   ```bash
   sudo pacman -U pfx-yukleyici-*.pkg.tar.zst
   ```

3. Uygulama menüsünden **PFX Sertifika Yükleyici**'yi başlatın.

İlk kurulumdan sonra güncellemeleri uygulama kendisi önerir.

### Bağımlılıklar

`python`, `pyside6`, `nss`, `openssl`, `polkit`, `p11-kit` — pacman bunları otomatik kurar.

### Diğer dağıtımlar

Yukarıdaki bağımlılıkları paket yöneticinizle kurun, ardından bu klasörde
`sh kur.sh` çalıştırın. Bu, uygulamayı yalnızca sizin kullanıcınız için kurar. Bu kurulumda uygulama kendini güncelleyemez; yalnızca yeni sürüm çıktığında haber verir.

## Kullanım

1. **Yükle** sekmesi: PFX dosyasını seçin, parolayı yazın, sertifika bilgilerini görmek için **Kontrol et**'e tıklayın.
2. Sertifikanın yükleneceği yerleri işaretleyip **Sertifikayı Yükle**'ye tıklayın.
3. Tarayıcılarınızı yeniden başlatın.

**Yüklü Sertifikalar** sekmesi kişisel sertifikaları listeler; birini seçip **PFX olarak dışa aktar…** ile kaydedebilir veya silebilirsiniz.
**Hakkında / Güncelleme** sekmesi sürümü gösterir ve güncellemeleri elle denetlemenizi sağlar.

## Kaldırma

```bash
sudo pacman -R pfx-yukleyici
```

## Paketi derleme

```bash
makepkg -f
```

Yeni sürüm yayınlamak için: `pfx_yukleyici.py` içindeki `__version__` ve `PKGBUILD`
içindeki `pkgver` değerini güncelleyin, sonra `sh release.sh` çalıştırın
(GitHub CLI `gh` gerekir).
