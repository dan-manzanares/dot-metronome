# PULSE — metrónomo en GTK4/Adwaita
# La versión original en Tkinter vive en el historial de git (git show v1.0.0:main.py)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk

import interfaz
import rutas

###########
# ESTILOS #
###########

proveedor = Gtk.CssProvider()
proveedor.load_from_path(rutas.ruta("estilo.css"))

Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    proveedor,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

#############
# EJECUCIÓN #
#############

# org.gnome.* está reservado para apps oficiales de GNOME; este proyecto usa
# el esquema io.github.<usuario> para verificar la app en Flathub vía GitHub.
# Nota: el usuario real de GitHub es "dan-manzanares" (con guion), pero el
# guion no es válido en un segmento no-final de un App ID de Flatpak — de ahí
# que este segmento vaya sin guion. Al enviar a Flathub, la comprobación
# automática de propiedad (que arma la URL a partir del App ID) va a buscar
# github.com/danmanzanares/pulse y no va a encontrarlo; hay que aclarar en la
# solicitud que el usuario real es dan-manzanares para que un revisor lo
# verifique a mano.
app = Adw.Application(application_id="io.github.danmanzanares.Pulse")
app.connect("activate", interfaz.al_activar)
app.run(None)
