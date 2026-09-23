# Todo lo relacionado a reproducir audio.
# El reloj del metrónomo ES la tarjeta de sonido: en vez de disparar un
# reproductor en cada pulso con un temporizador de GLib (que depende de que el
# hilo de la interfaz esté libre justo a tiempo), hay un único flujo de audio
# continuo (appsrc → tarjeta) y nosotros generamos sus muestras: silencio, y
# el clic copiado en la muestra EXACTA donde le toca sonar. A 48 kHz eso da
# una precisión de ~0,02 ms, y aunque la interfaz se trabe un momento, el
# audio ya está en el búfer de la tarjeta y sale igual a tiempo.
# (Es el mismo principio que usa la versión web con la Web Audio API.)

import atexit
import sys
from array import array
from collections import deque

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

import estado
import rutas

Gst.init(None)

TASA = 48000  # muestras por segundo (mono, 16 bits)
BYTES_POR_MUESTRA = 2
MUESTRAS_POR_BLOQUE = 512  # ~10,7 ms por bloque entregado a GStreamer
VOLUMEN_BEAT = 0.7
VOLUMEN_SUB = 0.15
# El mp3 trae ~23 ms de silencio al inicio (relleno del codificador): se
# recorta todo lo que esté por debajo de este umbral para que el clic arranque
# justo en su muestra.
UMBRAL_SILENCIO = 200

FORMATO = f"audio/x-raw,format=S16LE,channels=1,rate={TASA},layout=interleaved"


#####################
# CARGA DEL SONIDO  #
#####################

def _decodificar(archivo):
    # Decodifica el archivo UNA sola vez a muestras crudas, con el mismo
    # formato que el flujo de salida, para luego solo copiar bytes.
    pipeline = Gst.parse_launch(
        "filesrc name=origen ! decodebin ! audioconvert ! audioresample ! "
        f"{FORMATO} ! appsink name=destino sync=false"
    )
    pipeline.get_by_name("origen").set_property("location", rutas.ruta(archivo))
    destino = pipeline.get_by_name("destino")

    pipeline.set_state(Gst.State.PLAYING)
    datos = bytearray()
    while (muestra := destino.emit("pull-sample")) is not None:  # None = fin del archivo
        buffer = muestra.get_buffer()
        datos += buffer.extract_dup(0, buffer.get_size())
    pipeline.set_state(Gst.State.NULL)

    muestras = array("h", bytes(datos))
    if sys.byteorder == "big":
        muestras.byteswap()
    if not muestras:
        raise RuntimeError(f"No se pudo decodificar {archivo}")

    inicio = next((i for i, m in enumerate(muestras) if abs(m) > UMBRAL_SILENCIO), 0)
    return muestras[inicio:]


def _escalar(muestras, volumen):
    return array("h", (int(m * volumen) for m in muestras))


def _mezclar(a, b):
    largo = max(len(a), len(b))
    a = a + array("h", bytes(BYTES_POR_MUESTRA * (largo - len(a))))
    b = b + array("h", bytes(BYTES_POR_MUESTRA * (largo - len(b))))
    return array("h", (max(-32768, min(32767, x + y)) for x, y in zip(a, b)))


def _a_bytes(muestras):
    if sys.byteorder == "big":
        muestras = array("h", muestras)
        muestras.byteswap()
    return muestras.tobytes()


_clic = _decodificar("resources/beat.mp3")
CLIP_BEAT = _a_bytes(_escalar(_clic, VOLUMEN_BEAT))
CLIP_SUB = _a_bytes(_escalar(_clic, VOLUMEN_SUB))
# El beat y la primera subdivisión caen en la misma muestra: se pre-mezclan
# en un solo clip, así en tiempo real nunca hace falta sumar sonidos.
CLIP_BEAT_CON_SUB = _a_bytes(_mezclar(_escalar(_clic, VOLUMEN_BEAT), _escalar(_clic, VOLUMEN_SUB)))


#################
# SECUENCIADOR  #
#################

class _Secuenciador:
    # Vive en el hilo de audio de GStreamer. Toda la cuenta del tiempo se hace
    # en muestras absolutas desde que se encendió (no "cuánto falta desde el
    # último clic"), así los redondeos nunca se acumulan.

    def __init__(self):
        self.muestra = 0          # muestras ya generadas
        self.inicio_beat = 0.0    # muestra (fraccionaria) donde empieza el beat actual
        self.periodo = 0.0        # muestras por beat, fijado al comenzar cada beat
        self.subdiv = 1           # fijado al comenzar cada beat
        self.paso = 0             # subdivisión actual dentro del beat
        self.proximo = 0          # muestra del próximo clic
        self.voz = b""            # clip sonando ahora
        self.voz_pos = 0          # por qué muestra de ese clip vamos
        # (muestra, es_beat) de cada clic generado, para que la interfaz
        # anime cuando de verdad se oye. deque es seguro entre hilos.
        self.eventos = deque()

    def _disparar(self):
        if self.paso == 0:
            # Los cambios de BPM y subdivisión se aplican al empezar el
            # siguiente beat, nunca a mitad de uno.
            self.periodo = 60 * TASA / estado.bpm
            self.subdiv = estado.subdiv
            self.voz = CLIP_BEAT_CON_SUB if self.subdiv > 1 else CLIP_BEAT
        else:
            self.voz = CLIP_SUB
        self.voz_pos = 0
        self.eventos.append((self.proximo, self.paso == 0))

        self.paso += 1
        if self.paso >= self.subdiv:
            self.paso = 0
            self.inicio_beat += self.periodo
        self.proximo = round(self.inicio_beat + self.paso * self.periodo / self.subdiv)

    def generar(self, n):
        salida = bytearray(n * BYTES_POR_MUESTRA)  # arranca en silencio
        cursor, fin = self.muestra, self.muestra + n
        while cursor < fin:
            while self.proximo <= cursor:
                self._disparar()
            hasta = min(fin, self.proximo)
            k = min(hasta - cursor, len(self.voz) // BYTES_POR_MUESTRA - self.voz_pos)
            if k > 0:
                d = (cursor - self.muestra) * BYTES_POR_MUESTRA
                o = self.voz_pos * BYTES_POR_MUESTRA
                salida[d:d + k * BYTES_POR_MUESTRA] = self.voz[o:o + k * BYTES_POR_MUESTRA]
                self.voz_pos += k
            cursor = hasta
        self.muestra = fin
        return bytes(salida)


_secuenciador = _Secuenciador()


def _al_necesitar_datos(fuente, _longitud):
    # Lo llama GStreamer desde su hilo de audio cada vez que quiere otro bloque.
    inicio = _secuenciador.muestra
    buffer = Gst.Buffer.new_wrapped(_secuenciador.generar(MUESTRAS_POR_BLOQUE))
    buffer.pts = inicio * Gst.SECOND // TASA
    buffer.duration = MUESTRAS_POR_BLOQUE * Gst.SECOND // TASA
    fuente.emit("push-buffer", buffer)


# El volumen general lo aplica el elemento "volume" de GStreamer, no el
# secuenciador: así cambiarlo no toca la cuenta de muestras (el ritmo). Por
# encima de 1.0 amplifica, y en S16 satura en vez de dar la vuelta.
_pipeline = Gst.parse_launch(
    "appsrc name=fuente format=time ! volume name=volumen ! "
    "audioconvert ! audioresample ! autoaudiosink"
)
_fuente = _pipeline.get_by_name("fuente")
_volumen = _pipeline.get_by_name("volumen")
_fuente.set_property("caps", Gst.Caps.from_string(FORMATO))
# Cola corta: el secuenciador genera solo unos bloques por delante, así los
# cambios de BPM se notan enseguida (el colchón contra tirones lo da el
# búfer de la tarjeta, que está después).
_fuente.set_property("max-bytes", 2 * MUESTRAS_POR_BLOQUE * BYTES_POR_MUESTRA)
_fuente.connect("need-data", _al_necesitar_datos)
# Si la app se cierra con el metrónomo sonando, el hilo de audio seguiría
# llamando a Python mientras el intérprete se apaga (y eso lo hace abortar).
atexit.register(lambda: _pipeline.set_state(Gst.State.NULL))


def fijar_volumen(porcentaje):
    # 0-125 %, igual que el slider de la interfaz. Se puede llamar sonando o
    # apagado: el elemento conserva el valor entre encendidos.
    _volumen.set_property("volume", porcentaje / 100)


def encender():
    global _secuenciador
    _secuenciador = _Secuenciador()  # el primer beat cae en la muestra 0
    _pipeline.set_state(Gst.State.PLAYING)


def apagar():
    _pipeline.set_state(Gst.State.NULL)  # corta en seco y descarta lo pendiente
    _secuenciador.eventos.clear()


def eventos_sonados():
    # Devuelve (y consume) los clics que ya salieron por los parlantes, según
    # la posición real de reproducción: [True, False, ...] (True = beat).
    ok, posicion = _pipeline.query_position(Gst.Format.TIME)
    if not ok:
        return []
    reproducida = posicion * TASA // Gst.SECOND
    eventos = _secuenciador.eventos
    sonados = []
    while eventos and eventos[0][0] < reproducida:
        sonados.append(eventos.popleft()[1])
    return sonados
