# Construcción de la ventana y los widgets.

import re
from pathlib import Path

import cairo
import gi

gi.require_version("Rsvg", "2.0")
from gi.repository import Gtk, Adw, Rsvg, GLib

import estado
import motor
import sonido

# Licencia: el README no la menciona, así que este texto queda fijo acá.
URL_LICENCIA = "https://creativecommons.org/licenses/by-nc/4.0/"
TEXTO_LICENCIA = (
    "This work is licensed under Creative Commons "
    "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).\n"
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

# Sitio de la versión web, instalable como app (PWA) en el teléfono.
# Equivalente del botón "Install app" del pie de webapp/www/index.html, que
# allá solo aparece cuando el navegador puede instalarla.
URL_WEB = "https://dot.alteus.app/"

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


##########
#  TEMA  #
##########

# Mismos temas que la app web (webapp/www/css/estilo.css): "oscuro" es el de
# siempre, "catppuccin" es Catppuccin Mocha. Los colores de la interfaz
# viven en estilo.css (clase .tema-catppuccin en la ventana); los de los
# círculos van acá porque cairo no puede leer variables de CSS. Si cambian,
# actualizar también las variables --circulo-* de la app web.
# (id del tema, nombre que se muestra). El id es la clase CSS (tema-<id>) y
# lo que se guarda en disco; "oscuro" es el tema por defecto, sin clase.
# Mantener en sincronía con el menú de webapp/www/index.html.
TEMAS = [
    ("oscuro", "Dark"),
    ("catppuccin", "Catppuccin Mocha"),
    ("latte", "Catppuccin Latte"),
    ("nord", "Nord"),
    ("nord-claro", "Nord Light"),
    ("gruvbox", "Gruvbox Dark"),
    ("gruvbox-claro", "Gruvbox Light"),
]

# (color del centro, color del borde) de cada círculo, en RGB 0-1
COLORES_CIRCULOS = {
    "oscuro": {
        "beat": ((0.55, 0.62, 0.72), (0.30, 0.36, 0.45)),
        "sub": ((0.20, 0.50, 0.60), (0.30, 0.60, 0.80)),
    },
    "catppuccin": {
        "beat": ((0.537, 0.706, 0.980), (0.271, 0.278, 0.353)),  # blue → surface1
        "sub": ((0.455, 0.780, 0.925), (0.796, 0.651, 0.969)),  # sapphire → mauve
    },
    "latte": {
        "beat": ((0.118, 0.400, 0.961), (0.737, 0.753, 0.800)),  # blue → surface1
        "sub": ((0.125, 0.624, 0.710), (0.533, 0.224, 0.937)),  # sapphire → mauve
    },
    "nord": {
        "beat": ((0.506, 0.631, 0.757), (0.263, 0.298, 0.369)),  # nord9 → nord2
        "sub": ((0.533, 0.753, 0.816), (0.561, 0.737, 0.733)),  # nord8 → nord7
    },
    "nord-claro": {
        "beat": ((0.369, 0.506, 0.675), (0.682, 0.722, 0.784)),  # nord10 → nord4 oscurecido
        "sub": ((0.533, 0.753, 0.816), (0.506, 0.631, 0.757)),  # nord8 → nord9
    },
    "gruvbox": {
        "beat": ((0.514, 0.647, 0.596), (0.314, 0.286, 0.271)),  # blue claro → bg2
        "sub": ((0.557, 0.753, 0.486), (0.980, 0.741, 0.184)),  # aqua claro → yellow claro
    },
    "gruvbox-claro": {
        "beat": ((0.027, 0.400, 0.471), (0.835, 0.769, 0.631)),  # blue oscuro → bg2
        "sub": ((0.259, 0.482, 0.345), (0.710, 0.463, 0.078)),  # aqua oscuro → yellow oscuro
    },
}

# Las preferencias (tema, volumen) se guardan cada una en un archivo de texto
# en la carpeta de configuración del usuario, igual que la web las guarda en
# localStorage.
DIR_PREFERENCIAS = Path(GLib.get_user_config_dir()) / "dot"


def leer_preferencia(nombre):
    try:
        return (DIR_PREFERENCIAS / nombre).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def guardar_preferencia(nombre, valor):
    try:
        DIR_PREFERENCIAS.mkdir(parents=True, exist_ok=True)
        (DIR_PREFERENCIAS / nombre).write_text(str(valor), encoding="utf-8")
    except OSError:
        pass  # no poder guardar la preferencia no debe romper la app


def leer_tema_guardado():
    tema = leer_preferencia("tema")
    return tema if tema in dict(TEMAS) else "oscuro"


def guardar_tema(tema):
    guardar_preferencia("tema", tema)


def aplicar_tema(ventana, tema):
    for otro, _etiqueta in TEMAS:
        ventana.remove_css_class("tema-" + otro)
    if tema != "oscuro":
        ventana.add_css_class("tema-" + tema)
    estado.tema = tema
    if estado.area_dibujo is not None:
        estado.area_dibujo.queue_draw()


def elegir_tema(ventana, tema, popover):
    aplicar_tema(ventana, tema)
    guardar_tema(tema)
    popover.popdown()


def crear_boton_temas(ventana):
    # Menú con la lista de temas (equivalente del menú de index.html en la
    # web). Los Gtk.CheckButton agrupados se dibujan como radio buttons, así
    # se ve cuál está activo.
    popover = Gtk.Popover()
    caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    primero = None
    for tema, etiqueta in TEMAS:
        opcion = Gtk.CheckButton(label=etiqueta)
        if primero is None:
            primero = opcion
        else:
            opcion.set_group(primero)
        opcion.set_active(tema == estado.tema)
        # "toggled" también salta al desmarcarse la opción anterior: solo
        # interesa la que quedó activa.
        opcion.connect("toggled", lambda o, t=tema: o.get_active() and elegir_tema(ventana, t, popover))
        caja.append(opcion)
    popover.set_child(caja)

    boton = Gtk.MenuButton(label="◐", popover=popover)
    boton.set_direction(Gtk.ArrowType.UP)  # está en el pie: el menú abre hacia arriba
    boton.set_tooltip_text("Change theme")
    boton.add_css_class("flat")
    boton.add_css_class("boton-info")
    return boton


#############
#  VOLUMEN  #
#############

VOLUMEN_MAX = 125  # más de 100 % amplifica; ese tramo se pinta con el rojo del tema

# El tramo 101-125 % del slider va en rojo. GTK no puede pintar solo una
# parte del relleno según el valor, así que el corte del degradado se
# recalcula en cada cambio y se carga en un proveedor de CSS propio
# (equivalente de la variable --corte de la web).
_css_volumen = Gtk.CssProvider()


def pintar_volumen(valor):
    if valor <= 100:
        _css_volumen.load_from_string("")  # vuelve al estilo normal de estilo.css
        return
    corte = 100 / valor * 100  # dónde termina el 100 % dentro del relleno
    _css_volumen.load_from_string(
        "scale.volumen trough > highlight { background-image: var(--noise), "
        f"linear-gradient(90deg, var(--pista-llena-1) {corte:.2f}%, "
        f"var(--rojo-encendido-1) {corte:.2f}%); }}"
    )


_guardado_volumen_id = None


def _guardar_volumen():
    global _guardado_volumen_id
    _guardado_volumen_id = None
    guardar_preferencia("volumen", estado.volumen)
    return False  # timeout de una sola vez


def cambiar_volumen(slider):
    global _guardado_volumen_id
    estado.volumen = round(slider.get_value())
    sonido.fijar_volumen(estado.volumen)
    pintar_volumen(estado.volumen)
    # Al arrastrar llegan decenas de cambios por segundo: se guarda en disco
    # solo cuando el slider se queda quieto un momento.
    if _guardado_volumen_id is not None:
        GLib.source_remove(_guardado_volumen_id)
    _guardado_volumen_id = GLib.timeout_add(400, _guardar_volumen)


def leer_volumen_guardado():
    try:
        return max(0, min(VOLUMEN_MAX, int(leer_preferencia("volumen"))))
    except (TypeError, ValueError):
        return 100


def crear_slider_volumen():
    slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
    slider.set_range(0, VOLUMEN_MAX)
    slider.set_increments(1, 5)
    slider.set_digits(0)
    slider.add_css_class("volumen")
    slider.set_tooltip_text("Volume")
    for marca in (25, 50, 75, 100, 125):
        slider.add_mark(marca, Gtk.PositionType.BOTTOM, f"{marca}%")
    slider.set_value(estado.volumen)
    slider.connect("value-changed", cambiar_volumen)
    return slider


def dibujar_circulos(area, contexto, ancho, alto):
    centro_x = ancho / 2
    centro_y = alto / 2
    radio_1 = 150
    radio_2 = 50
    colores = COLORES_CIRCULOS[estado.tema]

    # Primer círculo, con gradiente radial (da sensación de volumen) + ruido
    alpha_1 = max(0.2, 1 - estado.progreso_onda)
    gradiente_1 = cairo.RadialGradient(centro_x, centro_y, 0, centro_x, centro_y, radio_1)
    gradiente_1.add_color_stop_rgba(0, *colores["beat"][0], alpha_1)  # centro, más claro
    gradiente_1.add_color_stop_rgba(1, *colores["beat"][1], alpha_1)  # borde, más oscuro

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
    gradiente_2.add_color_stop_rgba(0, *colores["sub"][0], alpha_2)
    gradiente_2.add_color_stop_rgba(1, *colores["sub"][1], alpha_2)

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
    comentarios = f"{COMENTARIOS_README}\n\nLicense: CC BY-NC 4.0\n{URL_LICENCIA}"
    dialogo = Adw.AboutDialog(
        application_name="Dot",
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
    # Por encima de estilo.css, para que el rojo del volumen le gane al
    # relleno normal del slider.
    Gtk.StyleContext.add_provider_for_display(
        ventana.get_display(), _css_volumen, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
    )
    ventana.set_title("Dot")
    ventana.set_default_size(400, 800)
    aplicar_tema(ventana, leer_tema_guardado())

    # Barra de título estilo GNOME (trae los botones de cerrar/minimizar/maximizar)
    barra_titulo = Adw.HeaderBar()


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

    # Tap tempo: clic en cualquier parte de los círculos calcula el BPM a
    # partir de los últimos 3 clics.
    gesto_tap = Gtk.GestureClick.new()
    gesto_tap.connect("pressed", motor.tap_tempo)
    estado.area_dibujo.add_controller(gesto_tap)

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

    # Slider de volumen: mismo ancho que el selector de subdivisión
    estado.volumen = leer_volumen_guardado()
    sonido.fijar_volumen(estado.volumen)
    slider_volumen = crear_slider_volumen()
    slider_volumen.set_margin_start(80)
    slider_volumen.set_margin_end(80)
    slider_volumen.set_margin_top(14)
    pintar_volumen(estado.volumen)
    caja.append(slider_volumen)

    # Pie: enlaces en la esquina inferior izquierda, tema e "Acerca de" en la
    # inferior derecha (igual que el pie de la web).
    # Queda pegado al fondo gracias al vexpand del área de dibujo (ver arriba),
    # no por nada especial de este widget en sí.
    pie = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    pie.set_margin_top(24)
    pie.set_margin_bottom(10)
    pie.set_margin_start(12)
    pie.set_margin_end(12)

    enlaces = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    enlaces.set_hexpand(True)
    enlaces.set_halign(Gtk.Align.START)
    enlaces.set_valign(Gtk.Align.END)

    telefono = Gtk.LinkButton(uri=URL_WEB, label="Get Dot on your phone")
    telefono.add_css_class("enlace-instalar")
    telefono.set_halign(Gtk.Align.START)
    enlaces.append(telefono)

    cafe = Gtk.LinkButton(uri=URL_CAFE, label="☕ Buy me a coffee")
    cafe.add_css_class("bmc")
    cafe.set_halign(Gtk.Align.START)
    enlaces.append(cafe)
    pie.append(enlaces)

    botones = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
    botones.set_valign(Gtk.Align.END)
    botones.append(crear_boton_temas(ventana))

    # Botón "Acerca de" (créditos, licencia completa y link de apoyo).
    # Usa texto en vez de icon_name: los íconos simbólicos (dialog-information
    # -symbolic) no dibujaban el glifo en este sistema —solo el fondo CSS
    # pintaba, confirmado con el inspector— así que en vez de seguir
    # depurando el tema de íconos, usamos el mismo mecanismo de texto que ya
    # funciona en el resto de la interfaz (labels de BPM, créditos, etc.).
    boton_acerca_de = Gtk.Button(label="ⓘ")
    boton_acerca_de.set_tooltip_text("About")
    boton_acerca_de.add_css_class("flat")
    boton_acerca_de.add_css_class("boton-info")
    boton_acerca_de.connect("clicked", lambda boton: mostrar_acerca_de(ventana))
    botones.append(boton_acerca_de)
    pie.append(botones)

    caja.append(pie)

    ventana.set_content(caja)
    ventana.present()
