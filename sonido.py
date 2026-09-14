# Todo lo relacionado a reproducir audio.
# Migrado de pygame a GStreamer: pygame necesita SDL2/SDL2_mixer, que el
# runtime de GNOME no trae (habría que compilarlas desde código fuente dentro
# del Flatpak). GStreamer sí viene incluido, con soporte para mp3, y es el
# mecanismo estándar de audio en apps GTK/Adwaita.

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

import rutas

Gst.init(None)


def _crear_reproductor(archivo):
    # "playbin" arma automáticamente el pipeline completo (decodifica el
    # archivo y lo manda a la salida de audio); se crea una sola vez y se
    # reutiliza en cada pulso, en vez de armar un pipeline nuevo cada vez.
    reproductor = Gst.ElementFactory.make("playbin", None)
    reproductor.set_property("uri", Gst.filename_to_uri(rutas.ruta(archivo)))
    return reproductor


# Dos reproductores separados (no uno solo) porque el beat y la primera
# subdivisión de cada compás suenan casi al mismo tiempo (ver motor.pulso_beat);
# con uno solo, el segundo "play" cortaría al primero a mitad de sonido.
_reproductor_beat = _crear_reproductor("resources/beat.mp3")
_reproductor_sub = _crear_reproductor("resources/beat.mp3")


def _reproducir(reproductor, volumen):
    # Volver a NULL antes de reproducir descarta cualquier reproducción
    # anterior todavía en curso y reinicia la posición al principio del
    # archivo, para que cada pulso suene desde el inicio del sonido.
    reproductor.set_state(Gst.State.NULL)
    reproductor.set_property("volume", volumen)
    reproductor.set_state(Gst.State.PLAYING)


def reproducir_beat():
    _reproducir(_reproductor_beat, 0.7)


def reproducir_sub():
    _reproducir(_reproductor_sub, 0.15)
