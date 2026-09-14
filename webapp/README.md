# Dot — versión web

Puerto a HTML/CSS/JS de la app de escritorio (GTK4/Adwaita) que vive en la
raíz de este repo. Standalone: no requiere backend ni conexión — toda la
lógica de audio y temporización corre en el navegador con Web Audio API.

Qué se portó de dónde:

| Original (GTK) | Web |
|---|---|
| `motor.py` + `sonido.py` | `www/js/motor.js` |
| `interfaz.py` | `www/js/app.js` + `www/index.html` |
| `estilo.css` (CSS de GTK) | `www/css/estilo.css` (reinterpretado en CSS real) |
| `resources/beat.mp3` | `www/resources/beat.mp3` |

`estado.py`/`rutas.py` no tienen equivalente: eran solo para compartir estado
entre módulos de Python y resolver rutas de archivos en el Flatpak — en JS,
`motor.js` guarda su propio estado y las rutas son relativas de por sí.

## Probar en Apache/XAMPP

Esta carpeta ya vive bajo `htdocs/`, así que con Apache corriendo:

```
http://localhost/metronome/webapp/www/
```

No hace falta PHP: es HTML/CSS/JS estático, Apache solo sirve los archivos.

## Generar el APK con Capacitor

Requiere Node.js, el SDK de Android (Android Studio lo puede instalar, pero
ver la nota de JDK abajo — **no** alcanza con el JBR que trae Android Studio
ni con el JDK que tengas por defecto en el sistema).

```bash
cd webapp
npm install
npx cap add android      # solo la primera vez: genera android/
npx cap sync android      # copia www/ + config cada vez que cambie algo ahí
```

### JDK: tiene que ser la versión 21, ni más nueva ni más vieja

Verificado a mano, con errores reales en cada intento:

| JDK probado | Resultado |
| --- | --- |
| El del sistema (26) | Gradle 8.11.1 no lo soporta: `Unsupported class file major version 70` |
| El JBR de Android Studio (25) | Mismo problema: `Unsupported class file major version 69` |
| Temurin 17 | Gradle sí corre, pero el módulo de Capacitor pide Java 21: `error: invalid source release: 21` |
| **Temurin 21** | **Compila.** Es el que exige AGP 8.7.2 (ver `android/build.gradle`), y el más nuevo que tolera Gradle 8.11.1. |

Si no tienes un JDK 21 a mano, se puede bajar portable sin root:

```bash
curl -sL -o /tmp/temurin21.tar.gz \
  "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk"
mkdir -p ~/jdks && tar -xzf /tmp/temurin21.tar.gz -C ~/jdks
```

Luego, para compilar:

```bash
export ANDROID_HOME=~/Android/Sdk        # donde haya quedado el SDK
export JAVA_HOME=~/jdks/jdk-21*           # o el JDK 21 que ya tengas
export PATH="$JAVA_HOME/bin:$PATH"
cd android
echo "sdk.dir=$ANDROID_HOME" > local.properties
./gradlew assembleDebug
# APK en app/build/outputs/apk/debug/app-debug.apk
```

O, más simple si solo quieres abrirlo en Android Studio (que gestiona su
propio JDK internamente sin este lío):

```bash
npx cap open android
```

## Pendiente / decisiones abiertas

- **Sonido de 3 niveles**: la versión Tkinter original distinguía primer
  beat / beat / subdivisión con 3 archivos distintos
  (`beat_agudo.wav`, `beat.mp3`, `beat_grave.wav`). La versión GTK actual
  (y este puerto, fiel a ella) usa 2 niveles: mismo `beat.mp3`, distinto
  volumen. Esos `.wav` ya no están en el repo (se eliminaron junto con
  `main.py`, ver CHANGELOG.md de la raíz) — recuperables desde el historial
  de git (`git show v1.0.0:resources/beat_agudo.wav`) si se quiere retomar.
- **Firma para release**: el APK que genera `assembleDebug` está firmado con
  la clave de debug (no sirve para Play Store). Falta el keystore de release
  y configurar `signingConfigs` en `android/app/build.gradle` cuando llegue
  el momento de publicar.
