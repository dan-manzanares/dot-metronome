// El "motor" del metrónomo: scheduler de audio y lógica de beat/subdivisión.
// Puerto de motor.py + sonido.py (versión GTK de Dot).
//
// Por qué no alcanza con setTimeout/setInterval "ingenuo":
// el mismo problema de deriva que tenía la versión de escritorio
// (root.after en Tkinter, GLib.timeout_add en GTK) existe también en JS:
// el navegador no garantiza que un timeout dispare exactamente a los ms
// pedidos, y los errores se acumulan pulso tras pulso.
//
// La solución estándar en Web Audio es "look-ahead scheduling": un timer
// corto y frecuente (LOOKAHEAD_MS) no reproduce sonido directamente, sino
// que programa los próximos pulsos con AudioContext.currentTime como reloj
// de referencia (ese sí es de precisión de muestra, no de temporizador de
// SO). Ver: "A Tale of Two Clocks" (Chris Wilson, HTML5Rocks/web.dev).
// Es el mismo principio que usa sonido.py: el reloj es la tarjeta de sonido.

const Motor = (() => {
  const LOOKAHEAD_MS = 25;       // cada cuánto revisamos si hay que programar más pulsos
  const SCHEDULE_AHEAD_S = 0.1;  // cuánto margen (segundos) programamos por adelantado
  // Con la página oculta el navegador frena los timers a ~1 por segundo, así
  // que se programa más adelante para que no haya huecos. El BPM no se puede
  // cambiar mientras la página está oculta, así que no se pierde respuesta.
  const SCHEDULE_AHEAD_OCULTA_S = 1.5;
  const BPM_MIN = 40;
  const BPM_MAX = 220;
  const VOLUMEN_BEAT = 0.7;      // igual que sonido.py
  const VOLUMEN_SUB = 0.15;
  // Igual que UMBRAL_SILENCIO de sonido.py (200 sobre 32768, en 16 bits): se
  // salta el silencio inicial del mp3 para que el clic arranque justo en su
  // instante. Según el navegador, el decodificador lo quita o no.
  const UMBRAL_SILENCIO = 200 / 32768;

  let audioCtx = null;
  let salida = null;   // ganancia general (volumen), equivalente del elemento "volume" de sonido.py
  let volumen = 100;   // porcentaje, 0-125 (más de 100 amplifica)
  let bufferClic = null;
  let offsetClic = 0;  // segundos de silencio inicial a saltar en el buffer

  let bpm = 70;
  let subdiv = 1;      // 1 = "OFF": sin subdivisiones intermedias (igual que estado.py)
  let playing = false;
  let arranque = null; // promesa de iniciar() en curso (evita arrancar dos veces)

  let timerId = null;
  let nextBeatTime = 0;     // próximo beat a programar, en tiempo de audioCtx
  let eventos = [];         // {time, esBeat} de cada clic programado, pendiente de sonar
  let vozActual = [];       // fuentes del último clic (sonido.py es monofónico: cada clic corta al anterior)
  const fuentes = new Set(); // todas las fuentes programadas que no terminaron, para cortarlas al apagar

  // ---- Tap tempo ----
  const TAP_TIMEOUT_MS = 2000; // un clic más lento que esto se toma como el inicio de una cuenta nueva
  let tapTiempos = [];

  // El archivo se descarga apenas carga la página (no hace falta gesto del
  // usuario para eso); decodificarlo sí requiere el AudioContext, que en
  // móviles solo se puede crear tras un toque. Así el primer ON no espera
  // la red.
  const datosClic = fetch("resources/beat.mp3").then((r) => r.arrayBuffer());
  datosClic.catch(() => {}); // si falla, el error se ve al tocar ON (en arrancar)

  function limitarBpm(valor) {
    return Math.max(BPM_MIN, Math.min(BPM_MAX, Math.round(valor)));
  }

  function inicioAudible(buffer) {
    let inicio = buffer.length;
    for (let c = 0; c < buffer.numberOfChannels; c++) {
      const muestras = buffer.getChannelData(c);
      for (let i = 0; i < inicio; i++) {
        if (Math.abs(muestras[i]) > UMBRAL_SILENCIO) { inicio = i; break; }
      }
    }
    return inicio === buffer.length ? 0 : inicio / buffer.sampleRate;
  }

  async function cargarSonido() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: "interactive" });
      salida = audioCtx.createGain();
      salida.gain.value = volumen / 100;
      salida.connect(audioCtx.destination);
    }
    // slice(): decodeAudioData se queda con el ArrayBuffer que recibe
    bufferClic = await audioCtx.decodeAudioData((await datosClic).slice(0));
    offsetClic = inicioAudible(bufferClic);
  }

  function reproducir(tiempo, volumen) {
    const fuente = audioCtx.createBufferSource();
    fuente.buffer = bufferClic;
    const ganancia = audioCtx.createGain();
    ganancia.gain.value = volumen;
    fuente.connect(ganancia).connect(salida);
    fuente.start(tiempo, offsetClic);
    fuentes.add(fuente);
    fuente.onended = () => fuentes.delete(fuente);
    return fuente;
  }

  function cortar(fuente, tiempo) {
    try { fuente.stop(tiempo); } catch (e) {} // ya detenida: nada que hacer
  }

  // Un clic nuevo corta al anterior en su mismo instante, igual que en
  // sonido.py (donde el secuenciador reemplaza la voz que está sonando).
  function clic(tiempo, volumenes, esBeat) {
    vozActual.forEach((f) => cortar(f, tiempo));
    vozActual = volumenes.map((v) => reproducir(tiempo, v));
    eventos.push({ time: tiempo, esBeat });
  }

  function programarBeat(tiempo) {
    // Los cambios de BPM y subdivisión se aplican al empezar cada beat,
    // nunca a mitad de uno (igual que _Secuenciador._disparar).
    const spb = 60.0 / bpm;
    const n = subdiv;
    // Con subdivisiones, el beat suena mezclado con la subdivisión 0, que
    // cae en el mismo instante (CLIP_BEAT_CON_SUB en sonido.py).
    clic(tiempo, n > 1 ? [VOLUMEN_BEAT, VOLUMEN_SUB] : [VOLUMEN_BEAT], true);
    for (let i = 1; i < n; i++) {
      clic(tiempo + (spb * i) / n, [VOLUMEN_SUB], false);
    }
    return spb;
  }

  function planificador() {
    const margen = document.hidden ? SCHEDULE_AHEAD_OCULTA_S : SCHEDULE_AHEAD_S;
    while (nextBeatTime < audioCtx.currentTime + margen) {
      nextBeatTime += programarBeat(nextBeatTime);
    }
  }

  // Instante del reloj de audio que está saliendo AHORA por los parlantes.
  // currentTime va por delante: es lo que el navegador está procesando, que
  // se oye recién después de la latencia de salida (en Android, decenas de
  // ms o más). Equivale a query_position en sonido.py.
  function tiempoAudible() {
    if (audioCtx.getOutputTimestamp) {
      const marca = audioCtx.getOutputTimestamp();
      if (marca.contextTime > 0) return marca.contextTime;
    }
    return audioCtx.currentTime - (audioCtx.outputLatency || audioCtx.baseLatency || 0);
  }

  function eventosSonados() {
    // Devuelve (y consume) los clics que ya salieron por los parlantes:
    // [true, false, ...] (true = beat). Equivalente de sonido.eventos_sonados().
    if (!playing || !eventos.length) return [];
    const audible = tiempoAudible();
    const sonados = [];
    while (eventos.length && eventos[0].time <= audible) {
      sonados.push(eventos.shift().esBeat);
    }
    return sonados;
  }

  async function arrancar() {
    if (!bufferClic) await cargarSonido(); // si falló antes, se reintenta en el próximo ON
    if (audioCtx.state === "suspended") await audioCtx.resume(); // gesto del usuario requerido en móviles

    eventos = [];
    vozActual = [];
    nextBeatTime = audioCtx.currentTime + 0.05;
    playing = true;

    planificador();
    timerId = setInterval(planificador, LOOKAHEAD_MS);
  }

  function iniciar() {
    // Un segundo toque mientras se carga el sonido recibe la misma promesa,
    // en vez de arrancar un segundo planificador.
    if (playing) return Promise.resolve();
    if (!arranque) arranque = arrancar().finally(() => { arranque = null; });
    return arranque;
  }

  function detener() {
    // Corta en seco y descarta lo pendiente, igual que sonido.apagar(): sin
    // esto seguirían sonando los clics ya programados por adelantado.
    playing = false;
    if (timerId) clearInterval(timerId);
    timerId = null;
    fuentes.forEach((f) => cortar(f, 0));
    fuentes.clear();
    vozActual = [];
    eventos = [];
  }

  function setBpm(valor) {
    bpm = limitarBpm(valor);
    return bpm;
  }

  function setSubdiv(valor) {
    subdiv = valor;
  }

  function setVolumen(porcentaje) {
    // Igual que sonido.fijar_volumen(): no toca el planificador (el ritmo),
    // solo la ganancia general. Se puede llamar antes de crear el audio.
    volumen = porcentaje;
    if (salida) salida.gain.value = volumen / 100;
  }

  function tap() {
    // Cada clic se agrega a la cuenta; si tarda demasiado en llegar el
    // siguiente, se asume que el usuario empezó a marcar un tempo distinto
    // y se descartan los clics anteriores en vez de promediarlos con estos.
    const ahora = performance.now();
    if (tapTiempos.length && ahora - tapTiempos[tapTiempos.length - 1] > TAP_TIMEOUT_MS) {
      tapTiempos = [];
    }
    tapTiempos.push(ahora);
    if (tapTiempos.length > 3) tapTiempos.shift(); // solo importan los últimos 3 clics

    if (tapTiempos.length < 3) return null; // todavía no hay suficientes clics para calcular

    let sumaIntervalos = 0;
    for (let i = 1; i < tapTiempos.length; i++) {
      sumaIntervalos += tapTiempos[i] - tapTiempos[i - 1];
    }
    const promedioMs = sumaIntervalos / (tapTiempos.length - 1);
    return Math.round(60000 / promedioMs);
  }

  return {
    iniciar,
    detener,
    setBpm,
    setSubdiv,
    setVolumen,
    tap,
    eventosSonados,
    get bpm() { return bpm; },
    get playing() { return playing; },
    BPM_MIN,
    BPM_MAX,
  };
})();
