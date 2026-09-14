# Todo lo relacionado a reproducir audio con pygame.
# Se carga UNA sola vez, al importar este módulo.

import pygame as pg

pg.mixer.init()
sonido_beat = pg.mixer.Sound("resources/beat.mp3")


def reproducir_beat():
    sonido_beat.set_volume(0.7)
    sonido_beat.play()


def reproducir_sub():
    sonido_beat.set_volume(0.15)
    sonido_beat.play()
