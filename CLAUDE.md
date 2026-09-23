# Dot — metrónomo

## Reglas del proyecto

1. **La app es la versión web** (`webapp/www/`): HTML/CSS/JS estático con
   Web Audio, servido por Apache e instalable como PWA. Es la única versión
   que se distribuye y la referencia de comportamiento y de diseño.
2. **Función antes que herramientas.** Lo esencial es reducir la latencia y
   asegurar que el metrónomo funcione como se espera: clics a tiempo, sin
   deriva, y animaciones sincronizadas con el sonido. Ninguna herramienta,
   librería o técnica se adopta si compromete eso, y ante la duda gana la
   opción más simple y precisa. Tiene prioridad sobre las demás reglas.
3. **`legacy/` es la versión GTK original** (Python + GTK4/libadwaita, se
   ejecuta con `python3 legacy/main_gtk.py`), solo para uso personal. No se
   versiona (está en `.gitignore`; su última versión commiteada es el tag
   `gtk-final`) y ya no se mantiene a la par de la web: los cambios de la
   web no se portan allá, y no hace falta tocarla salvo que se pida
   explícitamente.
4. Los comentarios de la web que nombran contrapartes en Python (p. ej.
   "igual que sonido.py") se refieren a los archivos de `legacy/`. Son
   históricos: no hace falta agregar nuevos ni mantenerlos al día.

## Web y PWA

- La web es una PWA. Si se agrega, renombra o quita un archivo de
  `webapp/www/` que la app necesita para funcionar sin conexión, actualizar
  `ARCHIVOS` en `webapp/www/sw.js` y subir `VERSION_CACHE`.
- Lista de temas: el menú `#menu-temas` de `webapp/www/index.html`,
  `COLOR_BARRA` en `webapp/www/js/app.js` y la lista del script del `<head>`
  de `index.html` (ese script corre antes que app.js, por eso está repetida).
- Ícono: `resources/icono.svg` es la fuente; el favicon y los íconos de la
  PWA se regeneran con `webapp/generar-iconos.sh`.

## Convenciones

- Código, comentarios, nombres y CHANGELOG en español; los textos visibles
  de la UI en inglés.
- En los `.css` no escribir la secuencia de cierre de comentario dentro de un
  comentario (p. ej. al mencionar variables con comodín): corta el comentario
  antes de tiempo.
- Registrar los cambios visibles en `CHANGELOG.md`, sección `[Unreleased]`.
- En `legacy/` (si se toca): `estado.py` se importa como `import estado`, y
  las rutas a archivos de datos van con `rutas.ruta(...)`. El README que lee
  el diálogo "Acerca de" es el de la raíz del proyecto.
