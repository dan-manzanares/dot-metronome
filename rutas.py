# Rutas a los archivos de datos de la app (CSS, sonidos, README).
#
# Esos archivos viven junto al código fuente, pero la app puede lanzarse desde
# cualquier directorio (p. ej. `python3 /ruta/a/main_gtk.py`), así que una ruta
# relativa tipo "resources/beat.mp3" dejaría de encontrarse. Por eso todo se
# resuelve desde la carpeta de este archivo.

from pathlib import Path

DIR_BASE = Path(__file__).resolve().parent


def ruta(*partes):
    return str(DIR_BASE.joinpath(*partes))
