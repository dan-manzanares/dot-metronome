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

const Motor = (() => {
  const LOOKAHEAD_MS = 25;       // cada cuánto revisamos si hay que programar más pulsos
  const SCHEDULE_AHEAD_S = 0.1;  // cuánto margen (segundos) programamos por adelantado
  const BPM_MIN = 40;
  const BPM_MAX = 220;
  const COMPAS = 4;              // beats por compás (fijo, igual que la versión GTK)

  let audioCtx = null;
  let bufferBeat = null;
  let bufferSub = null;

  let bpm = 70;
  let subdiv = 1;      // 1 = "OFF": sin subdivisiones intermedias (igual que estado.py)
  let playing = false;

  let timerId = null;
  let nextBeatTime = 0;   // próximo beat a programar, en tiempo de audioCtx
  let beatIndex = 0;      // beats absolutos desde que se encendió, para saber cuál es "primero"
  let scheduled = [];     // eventos ya programados en audio, pendientes de reflejarse en la UI
  let onVisualEvent = null; // callback(kind, esPrimero) -> 'beat' | 'sub'

  // ---- Tap tempo ----
  const TAP_TIMEOUT_MS = 2000; // un clic más lento que esto se toma como el inicio de una cuenta nueva
  let tapTiempos = [];

  function limitarBpm(valor) {
    return Math.max(BPM_MIN, Math.min(BPM_MAX, Math.round(valor)));
  }

  async function cargarBuffer(url) {
    const respuesta = await fetch(url);
    const datos = await respuesta.arrayBuffer();
    return audioCtx.decodeAudioData(datos);
  }

  async function cargarSonidos() {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    // Igual que sonido.py: un mismo archivo para beat y subdivisión,
    // diferenciados solo por volumen (0.7 vs 0.15).
    [bufferBeat, bufferSub] = await Promise.all([
      cargarBuffer("resources/beat.mp3"),
      cargarBuffer("resources/beat.mp3"),
    ]);
  }

  function reproducir(buffer, tiempo, volumen) {
    const fuente = audioCtx.createBufferSource();
    fuente.buffer = buffer;
    const ganancia = audioCtx.createGain();
    ganancia.gain.value = volumen;
    fuente.connect(ganancia).connect(audioCtx.destination);
    fuente.start(tiempo);
  }

  function segundosPorBeat() {
    return 60.0 / bpm;
  }

  function programarBeat(tiempo) {
    const esPrimero = beatIndex % COMPAS === 0;
    reproducir(bufferBeat, tiempo, 0.7);
    scheduled.push({ time: tiempo, kind: "beat", first: esPrimero });

    // Subdivisión 0 coincide exactamente con el beat (ya sonó arriba);
    // acá solo programamos las intermedias, igual que motor.py.
    const spb = segundosPorBeat();
    for (let i = 1; i < subdiv; i++) {
      const t = tiempo + (spb * i) / subdiv;
      reproducir(bufferSub, t, 0.15);
      scheduled.push({ time: t, kind: "sub", first: false });
    }

    beatIndex++;
  }

  function planificador() {
    // Mientras el próximo beat caiga dentro de la ventana de anticipación,
    // seguimos programando (bpm puede haber cambiado desde el último pulso).
    while (nextBeatTime < audioCtx.currentTime + SCHEDULE_AHEAD_S) {
      programarBeat(nextBeatTime);
      nextBeatTime += segundosPorBeat();
    }
  }

  function bucleVisual() {
    if (!playing) return;
    const ahora = audioCtx.currentTime;
    while (scheduled.length && scheduled[0].time <= ahora) {
      const evento = scheduled.shift();
      if (onVisualEvent) onVisualEvent(evento.kind, evento.first);
    }
    requestAnimationFrame(bucleVisual);
  }

  async function iniciar() {
    if (playing) return;
    if (!audioCtx) await cargarSonidos();
    if (audioCtx.state === "suspended") await audioCtx.resume(); // gesto del usuario requerido en móviles

    beatIndex = 0;
    scheduled = [];
    nextBeatTime = audioCtx.currentTime + 0.05;
    playing = true;

    planificador();
    timerId = setInterval(planificador, LOOKAHEAD_MS);
    requestAnimationFrame(bucleVisual);
  }

  function detener() {
    playing = false;
    if (timerId) clearInterval(timerId);
    timerId = null;
    scheduled = [];
  }

  function setBpm(valor) {
    bpm = limitarBpm(valor);
    return bpm;
  }

  function setSubdiv(valor) {
    subdiv = valor;
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
    tap,
    get bpm() { return bpm; },
    get playing() { return playing; },
    set onVisualEvent(fn) { onVisualEvent = fn; },
    BPM_MIN,
    BPM_MAX,
  };
})();
