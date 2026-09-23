# Estado compartido del metrónomo.
# Todo lo que vive aquí puede cambiar en cualquier momento mientras la app corre.
# Los demás módulos deben acceder a esto como "estado.algo" (import estado),
# NUNCA como "from estado import algo" — eso copiaría el valor una sola vez
# y dejaría de enterarse de los cambios posteriores.

# Referencias a widgets (se asignan una vez que interfaz.al_activar() los crea)
area_dibujo = None
selector = None
titulo = None

# Tema visual actual ("oscuro" o "catppuccin"; ver interfaz.TEMAS)
tema = "oscuro"

# Parámetros del metrónomo
bpm = 70
volumen = 100  # porcentaje, 0-125 (más de 100 amplifica)
subdiv = 1
io = False

# Progreso de las animaciones (0.0 = recién encendido, >=1.0 = terminado/apagado)
progreso_onda = 1.0
progreso_sub = 1.0

# Instante (segundos, reloj de cuadros de GTK) en que sonó el último beat y el
# último clic de cualquier tipo; de ahí salen progreso_onda / progreso_sub.
inicio_onda = float("-inf")
inicio_sub = float("-inf")

# Identificador del tick callback que anima los círculos (None = no corre)
animacion_id = None

# Tap tempo: instantes (time.monotonic()) de los últimos clics en los círculos
tap_tiempos = []
