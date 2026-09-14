# Construcción de la ventana y los widgets.

import re
from pathlib import Path

import cairo
import gi

gi.require_version("Rsvg", "2.0")
from gi.repository import Gtk, Adw, Rsvg

import estado
import motor

# Licencia: el README no la menciona, así que este texto queda fijo acá.
URL_LICENCIA = "https://creativecommons.org/licenses/by-nc/4.0/"
TEXTO_LICENCIA = (
    "Este trabajo está licenciado bajo Creative Commons "
    "Atribución-NoComercial 4.0 Internacional (CC BY-NC 4.0).\n"
    f"{URL_LICENCIA}"
)


def leer_readme():
    # El diálogo "Acerca de" y el footer toman los créditos, el año y el link
    # de café directo de README.md — un solo lugar para editar esos datos,
    # en vez de duplicarlos a mano acá.
    texto = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

    match_autor = re.search(r"Made with .*? by (.+?), (\d{4})\.", texto)
    desarrollador = match_autor.group(1) if match_autor else "Daniel Manzanares"
    anio = match_autor.group(2) if match_autor else "2026"

    match_cafe = re.search(r"\[Buy Me a Coffee\]\((https?://\S+)\)", texto)
    url_cafe = match_cafe.group(1) if match_cafe else "https://buymeacoffee.com/daniel_manzanares"

    # Párrafo bajo "## What's this?" tal cual está en el README, como
    # descripción de la app en el diálogo "Acerca de".
    match_comentarios = re.search(r"## What's this\?\s*\n\n(.+?)\n\nIf you like it", texto, re.S)
    comentarios = match_comentarios.group(1).strip() if match_comentarios else texto.strip()

    return desarrollador, anio, url_cafe, comentarios


DESARROLLADOR, ANIO_COPYRIGHT, URL_CAFE, COMENTARIOS_README = leer_readme()

# Mismo ruido que usa estilo.css, pero como SVG "crudo" (sin escapar para URL),
# porque aquí se lo damos directo a Rsvg, no a una hoja de estilos.
RUIDO_SVG = b"""<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'>
<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.5' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>
<rect width='100%' height='100%' filter='url(#n)' opacity='0.35'/>
</svg>"""


def crear_patron_ruido():
    # Renderiza el SVG UNA sola vez a una superficie pequeña, y arma un
    # patrón que se puede repetir (mosaico) sobre cualquier área.
    handle = Rsvg.Handle.new_from_data(RUIDO_SVG)
    superficie = cairo.ImageSurface(cairo.FORMAT_ARGB32, 120, 120)
    cr_temporal = cairo.Context(superficie)
    viewport = Rsvg.Rectangle()
    viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, 120, 120
    handle.render_document(cr_temporal, viewport)

    patron = cairo.SurfacePattern(superficie)
    patron.set_extend(cairo.Extend.REPEAT)
    return patron


# Se crea una sola vez al importar el módulo — NUNCA dentro de dibujar_circulos,
# por la misma razón que cargábamos los sonidos una sola vez: renderizar el SVG
# es relativamente costoso comparado con solo usar el patrón ya hecho.
PATRON_RUIDO = crear_patron_ruido()


def dibujar_circulos(area, contexto, ancho, alto):
    centro_x = ancho / 2
    centro_y = alto / 2
    radio_1 = 150
    radio_2 = 50

    # Primer círculo, con gradiente radial (da sensación de volumen) + ruido
    alpha_1 = max(0.2, 1 - estado.progreso_onda)
    gradiente_1 = cairo.RadialGradient(centro_x, centro_y, 0, centro_x, centro_y, radio_1)
    gradiente_1.add_color_stop_rgba(0, 0.55, 0.62, 0.72, alpha_1)  # centro, más claro
    gradiente_1.add_color_stop_rgba(1, 0.30, 0.36, 0.45, alpha_1)  # borde, más oscuro

    contexto.arc(centro_x, centro_y, radio_1, 0, 2 * 3.14159)
    contexto.set_source(gradiente_1)
    contexto.fill_preserve()  # rellena, pero conserva el trazo del círculo

    contexto.clip()  # limita cualquier dibujo posterior a la forma del círculo
    contexto.set_source(PATRON_RUIDO)
    contexto.paint_with_alpha(alpha_1)  # pinta el ruido sobre toda el área recortada
    contexto.reset_clip()  # ¡importante! si no, todo lo que sigue quedaría recortado también

    # Segundo círculo
    alpha_2 = max(0.1, 1 - estado.progreso_sub)
    gradiente_2 = cairo.RadialGradient(centro_x, centro_y, 0, centro_x, centro_y, radio_2)
    gradiente_2.add_color_stop_rgba(0,0.2,0.5,0.6, alpha_2)
    gradiente_2.add_color_stop_rgba(1,0.3,0.6,0.8, alpha_2)

    contexto.arc(centro_x, centro_y, radio_2, 0, 2 * 3.14159)
    contexto.set_source(gradiente_2)
    contexto.fill_preserve()

    contexto.clip()
    contexto.set_source(PATRON_RUIDO)
    contexto.paint_with_alpha(alpha_2)
    contexto.reset_clip()


def mostrar_acerca_de(ventana):
    # La licencia va concatenada en "comments" (no solo en license_type/
    # license) para que se lea directo en el diálogo principal, sin tener
    # que entrar a la subpágina "Legal" a buscarla.
    comentarios = f"{COMENTARIOS_README}\n\nLicencia: CC BY-NC 4.0\n{URL_LICENCIA}"
    dialogo = Adw.AboutDialog(
        application_name="Pulse",
        developer_name=DESARROLLADOR,
        version="1.0",
        comments=comentarios,
        license_type=Gtk.License.CUSTOM,
        license=TEXTO_LICENCIA,
        support_url=URL_CAFE,  # esto agrega el botón "Support the App" en el diálogo
    )
    dialogo.present(ventana)


def al_activar(app):
    ventana = Adw.ApplicationWindow(application=app)
    ventana.set_title("Pulse")
    ventana.set_default_size(400, 800)

    # Barra de título estilo GNOME (trae los botones de cerrar/minimizar/maximizar)
    barra_titulo = Adw.HeaderBar()

    # Botón "Acerca de" (créditos, licencia completa y link de apoyo).
    # Usa texto en vez de icon_name: los íconos simbólicos (dialog-information
    # -symbolic) no dibujaban el glifo en este sistema —solo el fondo CSS
    # pintaba, confirmado con el inspector— así que en vez de seguir
    # depurando el tema de íconos, usamos el mismo mecanismo de texto que ya
    # funciona en el resto de la interfaz (labels de BPM, créditos, etc.).
    boton_acerca_de = Gtk.Button(label="ⓘ")
    boton_acerca_de.set_tooltip_text("Acerca de")
    boton_acerca_de.add_css_class("flat")
    boton_acerca_de.add_css_class("boton-info")
    boton_acerca_de.connect("clicked", lambda boton: mostrar_acerca_de(ventana))
    barra_titulo.pack_end(boton_acerca_de)

    # Contenedor vertical: aquí se apilan la barra de título y el resto de widgets
    caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    caja.append(barra_titulo)

    # Fila de BPM: -5 | número editable | +5
    fila_bpm = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    fila_bpm.set_halign(Gtk.Align.CENTER)
    fila_bpm.set_margin_top(20)
    fila_bpm.set_margin_bottom(20)

    boton_menos5 = Gtk.Button(label="−5")
    boton_menos5.add_css_class("bpm-paso")
    boton_menos5.connect("clicked", lambda boton: motor.cambiar_bpm_por_boton(-5))
    fila_bpm.append(boton_menos5)

    # "120 BPM" como un solo texto editable (no separamos el número de la
    # unidad): al editar se ve y se escribe todo junto.
    estado.titulo = Gtk.EditableLabel(text=str(estado.bpm) + " BPM")
    estado.titulo.add_css_class("title-1")
    estado.titulo.set_alignment(0.5)
    estado.titulo.set_width_chars(7)
    estado.titulo.connect("notify::editing", motor.confirmar_bpm_editado)
    fila_bpm.append(estado.titulo)

    boton_mas5 = Gtk.Button(label="+5")
    boton_mas5.add_css_class("bpm-paso")
    boton_mas5.connect("clicked", lambda boton: motor.cambiar_bpm_por_boton(5))
    fila_bpm.append(boton_mas5)

    caja.append(fila_bpm)

    # Slider
    estado.selector = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
    estado.selector.set_range(40, 220)
    estado.selector.set_value(estado.bpm)
    estado.selector.set_digits(0)
    estado.selector.set_margin_start(30)
    estado.selector.set_margin_end(30)
    estado.selector.connect("value-changed", motor.bpm_desde_slider)
    estado.selector.add_mark(40, Gtk.PositionType.BOTTOM, "40 BPM")
    estado.selector.add_mark(70, Gtk.PositionType.BOTTOM, "70 BPM")
    estado.selector.add_mark(100, Gtk.PositionType.BOTTOM, "100 BPM")
    estado.selector.add_mark(130, Gtk.PositionType.BOTTOM, "130 BPM")
    estado.selector.add_mark(160, Gtk.PositionType.BOTTOM, "160 BPM")
    estado.selector.add_mark(190, Gtk.PositionType.BOTTOM, "190 BPM")
    estado.selector.add_mark(220, Gtk.PositionType.BOTTOM, "220 BPM")
    caja.append(estado.selector)

    # Área de círculos
    estado.area_dibujo = Gtk.DrawingArea()
    estado.area_dibujo.set_content_width(400)
    estado.area_dibujo.set_content_height(400)
    estado.area_dibujo.set_draw_func(dibujar_circulos)
    # vexpand=True: si la ventana se agranda, este widget absorbe todo el
    # espacio extra (dibujar_circulos ya centra los círculos según ancho/alto).
    # Así el resto de los widgets de abajo —botón, toggles, footer— quedan
    # siempre pegados entre sí y el footer siempre pegado al fondo, en vez de
    # flotar en el medio con un hueco vacío debajo.
    estado.area_dibujo.set_vexpand(True)
    caja.append(estado.area_dibujo)

    # Botón ON / OFF
    boton = Gtk.Button(label="ON")
    boton.set_margin_top(30)
    boton.set_margin_bottom(30)
    boton.set_margin_start(140)
    boton.set_margin_end(140)
    boton.add_css_class("io")
    boton.connect("clicked", motor.onoff)
    caja.append(boton)

    # Grupo de botones (selector de subdivisión)
    grupo = Adw.ToggleGroup()
    grupo.add(Adw.Toggle(name="1", label="OFF"))
    grupo.add(Adw.Toggle(name="2", label="2"))
    grupo.add(Adw.Toggle(name="3", label="3"))
    grupo.add(Adw.Toggle(name="4", label="4"))
    grupo.add(Adw.Toggle(name="5", label="5"))
    grupo.add(Adw.Toggle(name="6", label="6"))
    grupo.add(Adw.Toggle(name="7", label="7"))
    grupo.set_margin_start(80)
    grupo.set_margin_end(80)
    grupo.set_active_name("1")
    grupo.connect("notify::active-name", motor.cambiar_sub)
    caja.append(grupo)

    # Footer: créditos, licencia y link de apoyo.
    # Queda pegado al fondo gracias al vexpand del área de dibujo (ver arriba),
    # no por nada especial de este widget en sí.
    pie = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    pie.set_halign(Gtk.Align.CENTER)
    pie.set_margin_top(40)
    pie.set_margin_bottom(14)

    cafe = Gtk.LinkButton(uri=URL_CAFE, label="☕ Buy me a coffee")
    cafe.add_css_class("bmc")
    pie.append(cafe)

    caja.append(pie)

    ventana.set_content(caja)
    ventana.present()
