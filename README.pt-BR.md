# Instalador de Certificados PFX

[English](README.md) · [Türkçe](README.tr.md) · **Português (Brasil)**

Um pequeno aplicativo de desktop para Linux (feito para CachyOS / Arch Linux) que
instala certificados **PFX / P12 (PKCS#12)** — por exemplo, certificados digitais
A1 (e-CPF, e-CNPJ) ou de autenticação de cliente — nos seus navegadores
**sem usar o terminal**.

## Recursos

- Escolha o arquivo ou arraste-o, digite a senha e clique em **Instalar**.
- Clicar duas vezes em um arquivo `.pfx` / `.p12` no gerenciador de arquivos abre o aplicativo com esse arquivo.
- Detecta automaticamente os repositórios de certificados:
  - Chrome / Chromium / Edge / Brave / Vivaldi (repositório NSS compartilhado `~/.pki/nssdb`)
  - Firefox, LibreWolf, Waterfox, Floorp, Zen, Thunderbird (todos os perfis, inclusive com *profile-sync-daemon*)
  - Navegadores Flatpak
- Verifica a senha e mostra os dados do certificado (titular, emissor, validade) antes de instalar.
- Opcionalmente adiciona os certificados de AC (raiz/intermediários) da cadeia ao repositório de confiança do sistema.
- Lista os certificados pessoais instalados e permite removê-los.
- Suporta arquivos PFX com criptografia antiga (legacy).
- As senhas nunca são passadas pela linha de comando.
- Disponível em **inglês, turco e português do Brasil** (detectado pelo idioma do sistema, pode ser alterado no aplicativo).
- **Atualizações automáticas:** ao iniciar, verifica no GitHub se há uma nova versão; se você aprovar, baixa, instala e reinicia.

## Instalação

1. Baixe o arquivo `pfx-yukleyici-*.pkg.tar.zst` mais recente na página
   [Releases](https://github.com/bariscagriyuce/pfx/releases).
2. Abra-o com o seu instalador de pacotes ou execute:

   ```bash
   sudo pacman -U pfx-yukleyici-*.pkg.tar.zst
   ```

3. Inicie o **Instalador de Certificados PFX** pelo menu de aplicativos.

Depois da primeira instalação, o próprio aplicativo oferece as atualizações.

### Dependências

`python`, `pyside6`, `nss`, `openssl`, `polkit`, `p11-kit` — o pacman as instala automaticamente.

### Outras distribuições

Instale as dependências acima com o seu gerenciador de pacotes e execute
`sh kur.sh` nesta pasta. Isso instala o aplicativo só para o seu usuário. Nesse caso o aplicativo não se atualiza sozinho; ele apenas avisa quando há uma nova versão.

## Uso

1. Aba **Instalar**: escolha o arquivo PFX, digite a senha e clique em **Verificar** para ver os dados do certificado.
2. Marque onde o certificado deve ser instalado e clique em **Instalar Certificado**.
3. Reinicie os navegadores.

A aba **Certificados Instalados** lista os certificados pessoais e permite excluí-los.
A aba **Sobre / Atualizações** mostra a versão e permite verificar atualizações manualmente.

## Desinstalação

```bash
sudo pacman -R pfx-yukleyici
```

## Compilando o pacote

```bash
makepkg -f
```

Para publicar uma nova versão: atualize `__version__` em `pfx_yukleyici.py` e
`pkgver` no `PKGBUILD` e execute `sh release.sh` (requer o GitHub CLI `gh`).
