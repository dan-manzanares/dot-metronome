# El "motor" del metrónomo: controles de BPM/subdivisión, encendido y animación
# (el ritmo en sí lo lleva sonido.py, con el reloj de la tarjeta de sonido).
# Nota: aquí ya no se usa "global" en ningún lado — eso solo hace falta para
# variables del PROPIO módulo. Como bpm, subdiv, etc. viven en estado.py,
# simplemente se leen/escriben como estado.bpm, estado.subdiv, ...

import time

import estado
import sonido

# Tap tempo: un clic más lento que esto se toma como el inicio de una cuenta
# nueva, en vez de promediarlo con los clics anteriores.
TAP_TIMEOUT_S = 2.0


# Duración del desvanecido de los círculos tras cada clic (antes: 20 pasos de 15 ms).
DURACION_ANIMACION_S = 0.3


def _al_cuadro(area, reloj_cuadros):
    # Se ejecuta una vez por cuadro de pantalla mientras hay algo que animar.
    # No decide CUÁNDO suena nada (eso lo hace sonido.py con la tarjeta):
    # solo pregunta qué clics ya se oyeron y anima a partir de ese momento.
    ahora = reloj_cuadros.get_frame_time() / 1_000_000
    for es_beat in sonido.eventos_sonados():
        if es_beat:
            estado.inicio_onda = ahora
        estado.inicio_sub = ahora  # cada clic (beat incluido) enciende el círculo chico

    onda = min(1.0, (ahora - estado.inicio_onda) / DURACION_ANIMACION_S)
    sub = min(1.0, (ahora - estado.inicio_sub) / DURACION_ANIMACION_S)
    if (onda, sub) != (estado.progreso_onda, estado.progreso_sub):
        estado.progreso_onda, estado.progreso_sub = onda, sub
        area.queue_draw()

    if not estado.io and onda >= 1.0 and sub >= 1.0:
        estado.animacion_id = None
        return False  # apagado y animaciones terminadas: deja de correr
    return True


def _limitar_bpm(valor):
    return max(40, min(220, valor))


def aplicar_bpm(nuevo_bpm):
    # Único lugar que sincroniza bpm + slider + label numérico: lo usan
    # los botones -5/+5, el campo editable y el tap tempo, así que slider,
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


def onoff(clicked):
    if estado.io == False:
        sonido.encender()  # desde acá el ritmo lo lleva la tarjeta de sonido
        if estado.animacion_id is None:
            estado.animacion_id = estado.area_dibujo.add_tick_callback(_al_cuadro)
        clicked.set_label("OFF")
        clicked.add_css_class("io-encendido")
    else:
        sonido.apagar()
        clicked.set_label("ON")
        clicked.remove_css_class("io-encendido")
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
