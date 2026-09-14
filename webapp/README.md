# Pulse — versión web

Puerto a HTML/CSS/JS de la app de escritorio (GTK4/Adwaita) que vive en la
raíz de este repo. Standalone: no requiere backend ni conexión — toda la
lógica de audio y temporización corre en el navegador con Web Audio API.

Qué se portó de dónde:

| Original (GTK) | Web |
|---|---|
| `motor.py` + `sonido.py` | `www/js/motor.js` |
| `interfaz.py` | `www/js/app.js` + `www/index.html` |
| `estilo.css` (CSS de GTK) | `www/css/estilo.css` (reinterpretado en CSS real) |
| `resources/beat.mp3` | `www/resources/beat.mp3` |

`estado.py`/`rutas.py` no tienen equivalente: eran solo para compartir estado
entre módulos de Python y resolver rutas de archivos en el Flatpak — en JS,
`motor.js` guarda su propio estado y las rutas son relativas de por sí.

## Probar en Apache/XAMPP

Esta carpeta ya vive bajo `htdocs/`, así que con Apache corriendo:

```
http://localhost/metronome/webapp/www/
```

No hace falta PHP: es HTML/CSS/JS estático, Apache solo sirve los archivos.

## Generar el APK con Capacitor

Requiere Node.js (ya verificado: node instalado) y Android Studio / SDK de
Android instalado para compilar.

```bash
cd webapp
npm install
npx cap init   # solo la primera vez si npm install no generó nada nuevo (ya hay capacitor.config.json)
npx cap add android
npx cap sync
npx cap open android   # abre el proyecto en Android Studio para compilar/firmar el APK
```

Cada vez que cambies algo en `www/`, antes de recompilar el APK:

```bash
npx cap sync
```

El `webDir` en `capacitor.config.json` apunta a `www/`, que queda embebido
dentro del APK — el metrónomo funciona sin red también en el teléfono.

## Pendiente / decisiones abiertas

- **Sonido de 3 niveles**: la versión Tkinter original distinguía primer
  beat / beat / subdivisión con 3 archivos distintos
  (`beat_agudo.wav`, `beat.mp3`, `beat_grave.wav`, ver `resources/` en la
  raíz del repo). La versión GTK actual simplificó a 2 niveles (mismo
  `beat.mp3`, distinto volumen) — este puerto siguió fielmente esa versión.
  Si quieren recuperar el tercer nivel, los `.wav` ya existen en
  `resources/`, solo falta cargarlos en `motor.js` y usarlos en
  `programarBeat()` cuando `esPrimero` sea true.
- **Ícono/splash de Android**: `npx cap add android` genera unos genéricos;
  hay que reemplazarlos con `resources/screenshot.png` o un ícono dedicado
  (Capacitor tiene `@capacitor/assets` para generarlos desde una sola imagen).
