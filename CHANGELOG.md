# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Añadido

- Versión web: metadatos SEO en `index.html` (title, meta description, Open
  Graph, Twitter Card, JSON-LD `WebApplication`), `robots.txt` y
  `sitemap.xml`.

### Eliminado

- Empaquetado Flatpak y publicación en Flathub: manifest
  `io.github.danmanzanares.Dot.json`, launcher `dot.sh`, desktop entry y
  metainfo de `packaging/`, y `PACKAGING.md`. La versión GTK se ejecuta con
  `python3 main_gtk.py`.
- Versión Android con Capacitor: `webapp/android/`, `capacitor.config.json`,
  `package.json`/`package-lock.json` y la parte de Android de
  `webapp/generar-iconos.sh`. En el celular se usa la web instalada como PWA.
- `main.py` (versión original en Tkinter) y los sonidos que solo usaba ella,
  `resources/beat_agudo.wav` y `resources/beat_grave.wav`. Dependían de
  `tkinter` y `pygame`, ausentes en el runtime de GNOME, así que nunca podían
  ejecutarse dentro del Flatpak. Siguen disponibles en el historial de git
  (`git show v1.0.0:main.py`).

### Cambiado

- El ícono pasó de `packaging/io.github.danmanzanares.Dot.svg` a
  `resources/icono.svg`.
- Renombrado el proyecto de **Pulse** a **Dot** en las versiones GTK y web:
  ventana, diálogo "Acerca de", ícono y App ID
  (`io.github.danmanzanares.Dot`). El repositorio de GitHub también se
  renombró a `dan-manzanares/dot-metronome`.

## [1.0.0] - 2026-09-14

### Añadido

- Empaquetado como Flatpak: manifest `io.github.danmanzanares.Dot.json`
  (entonces `io.github.danmanzanares.Pulse.json`, ver "Renombrado" más arriba),
  launcher `dot.sh` (entonces `pulse.sh`), desktop entry, metainfo AppStream
  (con captura de pantalla) e ícono, todo bajo `packaging/`.
- `rutas.py`: resuelve las rutas a datos (CSS, `resources/`) desde la
  ubicación del código en vez del directorio de trabajo, para que la app
  funcione igual instalada que en desarrollo.
- Captura de pantalla de la app (`resources/screenshot.png`), referenciada
  desde el metainfo para la ficha de la app en Flathub.
- `.gitignore` para los artefactos de `flatpak-builder` (`.flatpak-builder/`,
  `build-dir/`, `repo/`).
- `LICENSE.md` con el texto completo de la licencia (antes vacío).

### Cambiado

- Renombrado el proyecto de "Metrónomo" a **Pulse** (ventana, diálogo
  "Acerca de", desktop entry, metainfo, App ID).
- App ID definitivo: `io.github.danmanzanares.Pulse` (se probaron antes
  `org.gnome.Metronome` —reservado para GNOME oficial— y
  `app.alteus.Metronome` —dominio propio sin DNS activo todavía—).
- `sonido.py`: migrado de pygame a GStreamer. El runtime de GNOME no incluye
  SDL2/SDL2_mixer (dependencias de pygame) y habría que compilarlas desde
  código fuente dentro del Flatpak; GStreamer ya viene incluido y es el
  mecanismo estándar de audio en apps GTK/Adwaita.
- Licencia cambiada de CC BY-NC-ND 4.0 a **CC BY-NC 4.0** (ya permite obras
  derivadas) en `LICENSE.md`, `interfaz.py` y el metainfo.
- Runtime de Flatpak fijado a `org.gnome.Platform`/`Sdk` versión 50.

### Conocido / pendiente

- El usuario real de GitHub (`dan-manzanares`, con guion) no es representable
  tal cual en el App ID —un guion no es válido en un segmento no-final de un
  Flatpak App ID—, así que la comprobación automática de propiedad de
  Flathub (que arma la URL a partir del App ID) va a fallar; hay que pedirle
  a un revisor que la verifique a mano al enviar la app.
