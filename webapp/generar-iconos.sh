#!/usr/bin/env bash
# Genera los íconos de la web (favicon y los de la PWA) a partir del ícono de
# la app (resources/icono.svg).
#
# Requiere rsvg-convert (librsvg) e ImageMagick (magick).
# Uso: ./generar-iconos.sh   (desde webapp/)

set -euo pipefail
cd "$(dirname "$0")"

SVG=../resources/icono.svg
FONDO_ICONO="#ece8f7"   # claro, para que el cuerpo oscuro del metrónomo contraste

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cp "$SVG" www/favicon.svg

# ---- PWA (www/icons, referenciados desde manifest.webmanifest) ----
mkdir -p www/icons
# "any": cuadrado redondeado, se ve bien en cualquier fondo
for lado in 192 512; do
  dibujo=$(python3 -c "print(round($lado*0.78))")
  radio=$(python3 -c "print(round($lado*0.18))")
  rsvg-convert -w "$dibujo" -h "$dibujo" "$SVG" -o "$TMP/pwa.png"
  magick -size "${lado}x${lado}" xc:none -fill "$FONDO_ICONO" \
    -draw "roundrectangle 0,0,$((lado-1)),$((lado-1)),$radio,$radio" \
    "$TMP/pwa.png" -gravity center -composite "www/icons/icon-$lado.png"
done
# "maskable": fondo a sangre y el dibujo dentro de la zona segura (el círculo
# central del 80 %), porque Android recorta el ícono con la forma del launcher
rsvg-convert -w 330 -h 330 "$SVG" -o "$TMP/pwa.png"
magick -size 512x512 "xc:$FONDO_ICONO" "$TMP/pwa.png" -gravity center -composite \
  www/icons/maskable-512.png
# iOS: cuadrado lleno (el sistema redondea las esquinas)
rsvg-convert -w 140 -h 140 "$SVG" -o "$TMP/pwa.png"
magick -size 180x180 "xc:$FONDO_ICONO" "$TMP/pwa.png" -gravity center -composite \
  www/icons/apple-touch-icon.png

echo "Íconos de la web y de la PWA generados."
