# Estado compartido del metrónomo.
# Todo lo que vive aquí puede cambiar en cualquier momento mientras la app corre.
# Los demás módulos deben acceder a esto como "estado.algo" (import estado),
# NUNCA como "from estado import algo" — eso copiaría el valor una sola vez
# y dejaría de enterarse de los cambios posteriores.

# Referencias a widgets (se asignan una vez que interfaz.al_activar() los crea)
area_dibujo = None
selector = None
titulo = None

# Parámetros del metrónomo
bpm = 70
ms_bpm = int(60000 / bpm)
subdiv = 1
io = False

# Progreso de las animaciones (0.0 = recién encendido, >=1.0 = terminado/apagado)
progreso_onda = 1.0
progreso_sub = 1.0

# Identificadores de temporizadores (para poder cancelarlos con GLib.source_remove)
pulso_beat_id = None
animar_beat_id = None
pulso_sub_id = []  # lista: puede haber varias subdivisiones pendientes a la vez
animar_sub_id = None
