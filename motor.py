# El "motor" del metrónomo: temporizadores y lógica de beat/subdivisión.
# Nota: aquí ya no se usa "global" en ningún lado — eso solo hace falta para
# variables del PROPIO módulo. Como bpm, subdiv, etc. viven en estado.py,
# simplemente se leen/escriben como estado.bpm, estado.subdiv, ...

import time

from gi.repository import GLib

import estado
import sonido

# Tap tempo: un clic más lento que esto se toma como el inicio de una cuenta
# nueva, en vez de promediarlo con los clics anteriores.
TAP_TIMEOUT_S = 2.0


def animar_beat():
    estado.progreso_onda += 0.05
    estado.area_dibujo.queue_draw()
    return estado.progreso_onda < 1.0  # True mientras no termine, False cuando acaba


def animar_sub():
    estado.progreso_sub += 0.05
    estado.area_dibujo.queue_draw()
    return estado.progreso_sub < 1.0


def _limitar_bpm(valor):
    return max(40, min(220, valor))


def aplicar_bpm(nuevo_bpm):
    # Único lugar que sincroniza bpm + slider + label numérico: lo usan
    # los botones -5/+5, el campo editable y pulso_beat, así que slider,
    # label y estado.bpm nunca quedan desalineados entre sí.
    estado.bpm = _limitar_bpm(nuevo_bpm)
    estado.selector.set_value(estado.bpm)
    estado.titulo.set_text(str(estado.bpm) + " BPM")


def cambiar_bpm_por_boton(delta):
    aplicar_bpm(estado.bpm + delta)


def confirmar_bpm_editado(editable_label, param):
    # "notify::editing" se dispara al entrar Y al salir del modo edición;
    # solo nos interesa el segundo caso (editing pasa a False).
    if editable_label.get_editing():
        return
    try:
        # El texto es "120 BPM" completo; solo el primer token es el número.
        nuevo_bpm = int(editable_label.get_text().split()[0])
    except (ValueError, IndexError):
        nuevo_bpm = estado.bpm  # texto inválido: se descarta y vuelve al valor previo
    aplicar_bpm(nuevo_bpm)


def bpm_desde_slider(selector):
    # El slider se movió directamente (arrastre, teclado, click en la barra):
    # refleja el valor en el label sin volver a tocar el slider, para no
    # generar un bucle de señales "value-changed".
    estado.bpm = int(selector.get_value())
    estado.titulo.set_text(str(estado.bpm) + " BPM")


def pulso_beat():
    aplicar_bpm(int(estado.selector.get_value()))
    estado.ms_bpm = int(60000 / estado.bpm)

    estado.progreso_onda = 0.0
    estado.area_dibujo.queue_draw()

    # Subdivisión 0: coincide exactamente con este beat, se llama directo (sin after)
    estado.pulso_sub_id = []
    pulso_sub()

    # Subdivisiones intermedias de este beat
    for i in range(1, estado.subdiv):
        offset = int(estado.ms_bpm * i / estado.subdiv)
        estado.pulso_sub_id.append(GLib.timeout_add(offset, pulso_sub))

    sonido.reproducir_beat()
    estado.animar_beat_id = GLib.timeout_add(15, animar_beat)
    estado.pulso_beat_id = GLib.timeout_add(estado.ms_bpm, pulso_beat)
    return False  # pulso_beat se reprograma a sí misma arriba, no por retorno


def pulso_sub():
    estado.progreso_sub = 0.0
    estado.area_dibujo.queue_draw()

    if estado.subdiv > 1:
        sonido.reproducir_sub()

    estado.animar_sub_id = GLib.timeout_add(15, animar_sub)
    return False  # no se reprograma sola; pulso_beat() la dispara cada vez


def onoff(clicked):
    if estado.io == False:
        pulso_beat()  # pulso_beat gobierna su propio reloj y el de las subdivisiones
        clicked.set_label("OFF")
        clicked.add_css_class("io-encendido")
    else:
        clicked.set_label("ON")
        clicked.remove_css_class("io-encendido")
        GLib.source_remove(estado.pulso_beat_id)
        for id in estado.pulso_sub_id:
            GLib.source_remove(id)
    estado.io = not estado.io


def cambiar_sub(grupo, param):
    estado.subdiv = int(grupo.get_active_name())


def tap_tempo(gesto=None, n_press=None, x=None, y=None):
    # Clic en los círculos: se guardan los últimos 3 clics y el BPM se calcula
    # promediando los 2 intervalos entre ellos. Los args del gesto no se usan
    # (no importa dónde dentro del área de dibujo se haga clic).
    ahora = time.monotonic()
    if estado.tap_tiempos and ahora - estado.tap_tiempos[-1] > TAP_TIMEOUT_S:
        estado.tap_tiempos.clear()
    estado.tap_tiempos.append(ahora)
    del estado.tap_tiempos[:-3]  # solo importan los últimos 3 clics

    if len(estado.tap_tiempos) < 3:
        return  # todavía no hay suficientes clics para calcular

    intervalos = [b - a for a, b in zip(estado.tap_tiempos, estado.tap_tiempos[1:])]
    promedio = sum(intervalos) / len(intervalos)
    aplicar_bpm(round(60 / promedio))
