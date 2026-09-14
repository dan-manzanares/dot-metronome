#!/bin/sh
# Launcher instalado en /app/bin: el runtime ya trae python3 con PyGObject,
# pycairo, Rsvg y GStreamer, así que solo hace falta apuntar al script principal.
exec python3 /app/share/pulse/main_gtk.py "$@"
