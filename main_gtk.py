# Metrónomo en GTK
# PULSE
# ver main.py para más detalles (versión original en Tkinter)
# Migración a sistema GNOME

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk

import interfaz

###########
# ESTILOS #
###########

proveedor = Gtk.CssProvider()
proveedor.load_from_path("estilo.css")

Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    proveedor,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

#############
# EJECUCIÓN #
#############

app = Adw.Application(application_id="org.gnome.Metronome")
app.connect("activate", interfaz.al_activar)
app.run(None)
