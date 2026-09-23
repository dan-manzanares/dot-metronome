# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Añadido

- Versión web: metadatos SEO en `index.html` (title, meta description, Open
  Graph, Twitter Card, JSON-LD `WebApplication`), `robots.txt` y
  `sitemap.xml`.
- Botón ◐ en la barra de título (versiones GTK y web) que abre un menú con
  siete temas: el oscuro original, Catppuccin Mocha y Latte, Nord y Nord
  Light, y Gruvbox Dark y Light. La elección se recuerda entre sesiones: en
  GTK, en `~/.config/dot/tema`; en la web, en `localStorage`. Los temas
  claros invierten el relieve de los botones (variables `--luz` y
  `--sombra`), que antes estaba fijo para fondo oscuro.
- Slider de volumen (versiones GTK y web) debajo de las subdivisiones, del
  mismo ancho: 0 a 125 %, con marcas en 25, 50, 75, 100 y 125 %. El tramo por
  encima de 100 % amplifica y se pinta con el rojo del tema. No toca el
  ritmo: en GTK lo aplica un elemento `volume` de GStreamer y en la web una
  ganancia general de Web Audio. Se recuerda entre sesiones, igual que el
  tema (`~/.config/dot/volumen` / `localStorage`).
- Versión web instalable como app (PWA): `manifest.webmanifest`, íconos
  (generados con `webapp/generar-iconos.sh`) y un service worker (`sw.js`)
  que sirve la app desde la caché, así abre sin esperar la red y funciona sin
  conexión. El pie muestra "Install app" solo cuando el navegador ofrece
  instalarla. Reemplaza al enlace de descarga del APK.
- Versión GTK: enlace "Get Dot on your phone" en el pie, hacia la versión web
  instalable.
- Versión web: favicon.

### Corregido

- Versión web: tocar ON dos veces mientras cargaba el sonido arrancaba dos
  planificadores (clics dobles que OFF no detenía).
- Versión web: al apagar seguían sonando los clics ya programados por
  adelantado; ahora se cortan en seco, como en GTK.
- Versión web: el campo BPM aceptaba textos como "120abc".
- Versión web: a 360 px de ancho, los botones −5/+5 se salían de la pantalla
  y las etiquetas del slider se superponían.

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

- Pie reorganizado en las dos versiones: "Install app" (web) / "Get Dot on
  your phone" (GTK) y "Buy me a coffee" en la esquina inferior izquierda; tema (◐) y "Acerca de" (ⓘ) en la
  inferior derecha, fuera de la barra de título. El menú de temas abre hacia
  arriba.
- Versión web alineada con el motor de GTK: los círculos se encienden cuando
  el clic de verdad se oye (descontando la latencia de salida), el beat suena
  mezclado con la subdivisión, cada clic corta al anterior, se recorta el
  silencio inicial del mp3 y el círculo chico se enciende también en el beat.
  La animación deja de correr en reposo.
- Versión web: en pantallas angostas las marcas del slider muestran solo el
  número. El texto de "Acerca de" es el mismo que en GTK (del README).
- El ícono pasó de `packaging/io.github.danmanzanares.Dot.svg` a
  `resources/icono.svg`.
- Versión GTK: el ritmo lo lleva ahora el reloj de la tarjeta de sonido. En
  vez de un temporizador de GLib que arrancaba un `playbin` en cada clic (con
  retrasos variables y deriva acumulada), un único flujo `appsrc` genera el
  audio y coloca cada clic en su muestra exacta, a 48 kHz. Las animaciones se
  sincronizan con la posición real de reproducción.
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
