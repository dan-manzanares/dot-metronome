# Empaquetado y publicación (Flatpak / Flathub)

Procedimiento completo para construir, probar y publicar Pulse.
Todos los comandos se corren desde la raíz del proyecto salvo que se indique.

## Requisitos previos (una sola vez)

```bash
# Runtime y SDK de GNOME (lo que la app usa en tiempo de ejecución)
flatpak install -y flathub org.gnome.Platform//50 org.gnome.Sdk//50

# Herramienta oficial de Flathub: trae flatpak-builder y el linter del CI
flatpak install -y flathub org.flatpak.Builder
```

No hace falta instalar nada más: Gtk4, Adwaita, pycairo, Rsvg y GStreamer
(con decodificador mp3) ya vienen dentro de `org.gnome.Platform`.

## Ciclo de desarrollo: construir, instalar y probar

```bash
# Construir y exportar a un repo OSTree local
flatpak-builder --force-clean --repo=repo build-dir io.github.danmanzanares.Pulse.json

# Registrar el repo local (una sola vez)
flatpak remote-add --user --if-not-exists --no-gpg-verify pulse-local repo

# Instalar desde el repo local
flatpak install --user -y pulse-local io.github.danmanzanares.Pulse

# Correr
flatpak run --user io.github.danmanzanares.Pulse
```

Todo el ciclo va con `--user` a propósito: las operaciones en ámbito *system*
piden autenticación de polkit y se quedan colgadas en terminales sin sesión
gráfica interactiva. Con `--user` no hace falta autenticar nada, y las apps de
usuario igual usan los runtimes instalados a nivel de sistema.

Para reconstruir tras un cambio, basta con repetir el primer comando y
reinstalar. Si algo queda en estado raro:

```bash
flatpak uninstall --user -y io.github.danmanzanares.Pulse
rm -rf .flatpak-builder build-dir repo
```

Nota: el manifest descarga el código por `git` desde el tag publicado, **no**
usa los archivos locales. Para probar cambios sin publicar todavía, cambiar
temporalmente el bloque `sources` por:

```json
"sources": [ { "type": "dir", "path": "." } ]
```

...y revertirlo antes de enviar nada a Flathub (allí el código fuente no se
incluye en el envío).

## Validaciones antes de enviar

```bash
# Metadatos AppStream (sin depender de la red)
appstreamcli validate --no-net packaging/io.github.danmanzanares.Pulse.metainfo.xml

# Entrada de menú
desktop-file-validate packaging/io.github.danmanzanares.Pulse.desktop

# El mismo linter que corre el CI de Flathub
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest io.github.danmanzanares.Pulse.json
flatpak run --command=flatpak-builder-lint org.flatpak.Builder builddir build-dir
```

Errores esperados que **no** son bloqueantes:

- `appstream-external-screenshot-url` — Flathub espeja las capturas a su
  propio CDN durante el build oficial; no ocurre en builds locales.
- `appid-url-not-reachable` — el linter arma la URL del repo a partir del App
  ID (`danmanzanares`, sin guion), pero el usuario real es `dan-manzanares`.
  Un guion solo es válido en el último segmento de un App ID de Flatpak, así
  que no es representable. Requiere verificación manual de un revisor.

## Publicar una versión nueva

```bash
# 1. Taguear el commit que se quiere publicar
git tag -a v1.0.1 -m "Pulse 1.0.1"
git push origin v1.0.1

# 2. Actualizar tag y commit en el manifest
git rev-list -n 1 v1.0.1   # copiar el hash al campo "commit" del manifest

# 3. Reconstruir y validar con los comandos de arriba

# 4. Publicar el cambio del manifest en el PR / repo de Flathub
```

## Envío inicial a Flathub (ya realizado)

PR: <https://github.com/flathub/flathub/pull/10213>

```bash
gh repo fork flathub/flathub --clone=false
git clone --branch=new-pr https://github.com/dan-manzanares/flathub.git /tmp/flathub-submission
cd /tmp/flathub-submission
git checkout -b flathub new-pr
cp /ruta/al/proyecto/io.github.danmanzanares.Pulse.json .
git add io.github.danmanzanares.Pulse.json
git commit -m "Add io.github.danmanzanares.Pulse"
git push -u origin flathub
gh pr create --repo flathub/flathub --base new-pr --head dan-manzanares:flathub \
  --title "Add io.github.danmanzanares.Pulse"
```

Reglas del envío:

- El PR lleva **solo** el manifest. Nada de código fuente ni artefactos de
  build: el manifest los descarga por git desde este repo.
- El PR va contra la rama `new-pr`, no contra `master`.
- No hay que cerrar y reabrir el PR durante la revisión.
- Un revisor puede lanzar un build de prueba comentando `bot, build`.
- Al aprobarse, Flathub crea `flathub/io.github.danmanzanares.Pulse` e invita
  al autor como colaborador (requiere 2FA; aceptar dentro de una semana).

## Qué se instala dentro del Flatpak

| Ruta | Contenido |
|---|---|
| `/app/bin/pulse` | Launcher (`pulse.sh`) |
| `/app/share/pulse/` | Módulos Python, `estilo.css`, `README.md` |
| `/app/share/pulse/resources/` | Sonidos (`.mp3`, `.wav`) |
| `/app/share/applications/` | Entrada de menú |
| `/app/share/metainfo/` | Metadatos AppStream |
| `/app/share/icons/hicolor/scalable/apps/` | Ícono |
| `/app/share/licenses/` | `LICENSE.md` (lo instala flatpak-builder solo) |

Quedan deliberadamente fuera: `main.py` (versión Tkinter original; depende de
`tkinter` y `pygame`, ausentes en el runtime) y `resources/screenshot.png`
(solo sirve para la ficha de la tienda y el README — pesa más que toda la app).
