#############
# METRONOME #
#############

# Este proyecto es mi primer aplicación con Python, es un metronomo que se puede usar para tocar música.
# La intención es crear una aplicación de escritorio que sea capaz de reproducir un sonido en un tempo determinado por el usuario.
# Además, el usuario podrá crear subdivisiones para poder tocar con más precisión.
# Existen tres niveles de sonidos: primer beat, beats y subdivisiones.

# La app muestra un círculo que se ilumina en el beats.
# Dentro del círculo principal, hay otro círculo que se ilumina en las subdivisiones.
# Debajo del círculo, está el texto que indica el tempo y el beat actual.

# El estilo visual es apegado a las guías de GNOME.

# Autor: Daniel Alejandro Manzanares Chichil

import tkinter as tk #Importamos la libreria
import pygame as pg

pg.mixer.init() # Iniciar el mezclador de audio

# Rutas de archivos de audio
sonido_firstbeat = pg.mixer.Sound("resources/beat_agudo.wav")
sonido_beat = pg.mixer.Sound("resources/beat.mp3")
sonido_sub = pg.mixer.Sound("resources/beat_grave.wav")

root = tk.Tk() #Creamos la ventana

root.geometry("800x800") #Tamaño de la ventana
root.title("Metronome") #Titulo de la ventana

###########
# WIDGETS #
###########

label = tk.Label(root, text="Metronome", font=("Montserrat Alternates", 20)) #Creamos un label
label.pack(padx=20, pady=20) #Lo mostramos en la ventana

canvas = tk.Canvas(root, width=400, height=400)
canvas.pack()

circulo_beat = canvas.create_oval(50,50,350,350, fill="gray")
circulo_sub = canvas.create_oval(150,150,250,250, fill="gray")

# Slider beat
slider = tk.Scale(root, from_=40, to=200, orient="horizontal")
slider.pack()

# Texto BPM
label_bpm = tk.Label(root, text="BPM = 40", font=("Montserrat Alternates", 15))
label_bpm.pack(padx=20, pady=10)

# Texto beat actual
label_beat = tk.Label(root, text="0", font=("Montserrat Alternates", 10))
label_beat.pack(padx=5, pady=5)

# Botones para seleccionar subdiv

# » seleccionar subdivisión #
def seleccionar_subdiv(valor):
    global subdivision
    subdivision = int(valor)

frame_botones = tk.Frame(root)
frame_botones.pack(pady=10)

boton_cuartos = tk.Button(frame_botones, text="Cuartos", font=("Montserrat Alternates", 10), command=lambda: seleccionar_subdiv(1))
boton_cuartos.pack(side="left", padx=5)

boton_octavos = tk.Button(frame_botones, text="Octavos", font=("Montserrat Alternates", 10), command=lambda: seleccionar_subdiv(2))
boton_octavos.pack(side="left", padx=5)

boton_triplet = tk.Button(frame_botones, text="Triplet", font=("Montserrat Alternates", 10), command=lambda: seleccionar_subdiv(3))
boton_triplet.pack(side="left", padx=5)

boton_dieciseisavos = tk.Button(frame_botones, text="Dieciseisavos", font=("Montserrat Alternates", 10), command=lambda: seleccionar_subdiv(4))
boton_dieciseisavos.pack(side="left", padx=5)

encendido = False
id_beat = None
ids_sub = []  # lista: puede haber varias subdivisiones pendientes a la vez

def iniciar():
    global encendido
    if not encendido:
        pulso_beat()
    else:
        root.after_cancel(id_beat)
        for id in ids_sub:
            root.after_cancel(id)

    encendido = not encendido

io = tk.Button(text="ON/OFF", font=("Montserrat Alternates", 14), command=iniciar)
io.add_css_class("io")
io.pack(pady=10)

#############
# VARIABLES #
#############

beat_actual = 0 # beat actual
compas = 4 # compás

subdivision = 2 # 2 es octavos, 4 es dieciseisavos, 3 es tresillos, etc.


#############
# FUNCIONES #
#############

# » BEAT #

# Función para el 'pulso' del círculo
def pulso_beat():
    global beat_actual
    global compas
    global subdivision
    global id_beat
    global ids_sub

    if beat_actual % compas == 0:
        canvas.itemconfig(circulo_beat, fill="purple") # Enciende el círculo
        sonido_firstbeat.play()
    else:
        canvas.itemconfig(circulo_beat, fill="black") # Enciende el círculo
        sonido_beat.play()
    root.after(50, apagar_beat) # apaga el círculo, efecto visual

    ms_por_beat = int(60000/slider.get())
    beat_actual += 1
    beat_compas = ((beat_actual - 1) % compas)

    pulso_subdiv() # Subdivisión 0: coincide exactamente con este beat, por eso se llama directo (sin after)

    # Subdivisiones intermedias de este beat (offset 0 ya se disparó arriba con pulso_subdiv())
    ids_sub = []
    for i in range(1, subdivision):
        ids_sub.append(root.after(int(ms_por_beat * i / subdivision), pulso_subdiv))

    label_beat.config(text=str(beat_compas + 1))
    label_bpm.config(text="BPM = " + str(slider.get()))

    id_beat = root.after(ms_por_beat, pulso_beat) # después de ms_por_bpm se ejecuta la función pulso

def apagar_beat():
    canvas.itemconfig(circulo_beat, fill="gray") # Apaga el círculo

# » SUBBEAT #

def pulso_subdiv():
    # Efecto visual
    canvas.itemconfig(circulo_sub, fill="black")
    root.after(50, apagar_sub)
    sonido_sub.play() # Reproduce el sonido de subdivisión

def apagar_sub():
    canvas.itemconfig(circulo_sub, fill="gray")

#############
# EJECUCIÓN #
#############

root.mainloop() # Esto ejecuta la ventana