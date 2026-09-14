# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

## [1.0.0] - 2026-09-14

### Añadido

- Empaquetado como Flatpak: manifest [io.github.danmanzanares.Pulse.json](io.github.danmanzanares.Pulse.json),
  launcher `pulse.sh`, desktop entry, metainfo AppStream (con captura de
  pantalla) e ícono, todo bajo `packaging/`.
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
