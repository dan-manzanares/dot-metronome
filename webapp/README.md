# Dot — versión web

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

`estado.py`/`rutas.py` no tienen equivalente: son solo para compartir estado
entre módulos de Python y resolver rutas de archivos sin depender del
directorio actual — en JS, `motor.js` guarda su propio estado y las rutas son
relativas de por sí.

## Probar en Apache/XAMPP

Esta carpeta ya vive bajo `htdocs/`, así que con Apache corriendo:

```
http://localhost/metronome/webapp/www/
```

No hace falta PHP: es HTML/CSS/JS estático, Apache solo sirve los archivos.

## Pendiente / decisiones abiertas

- **Sonido de 3 niveles**: la versión Tkinter original distinguía primer
  beat / beat / subdivisión con 3 archivos distintos
  (`beat_agudo.wav`, `beat.mp3`, `beat_grave.wav`). La versión GTK actual
  (y este puerto, fiel a ella) usa 2 niveles: mismo `beat.mp3`, distinto
  volumen. Esos `.wav` ya no están en el repo (se eliminaron junto con
  `main.py`, ver CHANGELOG.md de la raíz) — recuperables desde el historial
  de git (`git show v1.0.0:resources/beat_agudo.wav`) si se quiere retomar.
