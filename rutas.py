# Rutas a los archivos de datos de la app (CSS, sonidos, README).
#
# En desarrollo, esos archivos viven junto al código fuente. Empaquetada como
# Flatpak, el ejecutable se lanza con un $PWD arbitrario (el del launcher de
# GNOME, no el del proyecto), así que cualquier ruta relativa tipo
# "resources/beat.mp3" dejaría de encontrarse. Por eso todo se resuelve desde
# la carpeta de este archivo, que el manifest instala junto al resto de datos.

from pathlib import Path

DIR_BASE = Path(__file__).resolve().parent


def ruta(*partes):
    return str(DIR_BASE.joinpath(*partes))
