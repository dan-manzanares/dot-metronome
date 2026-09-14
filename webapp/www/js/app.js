// Cableado de la interfaz: equivalente web de interfaz.py.
// El motor (motor.js) no sabe nada del DOM; este archivo es el único que
// toca elementos de la página.

(() => {
  const campoBpm = document.getElementById("campo-bpm");
  const sliderBpm = document.getElementById("slider-bpm");
  const botonMenos5 = document.getElementById("boton-menos5");
  const botonMas5 = document.getElementById("boton-mas5");
  const botonIo = document.getElementById("boton-io");
  const grupoSubdiv = document.getElementById("grupo-subdiv");
  const botonAcercaDe = document.getElementById("boton-acerca-de");
  const dialogoAcercaDe = document.getElementById("dialogo-acerca-de");
  const canvas = document.getElementById("area-dibujo");
  const ctx = canvas.getContext("2d");

  // ---- BPM: único lugar que sincroniza slider + campo + motor ----
  // (mismo rol que motor.aplicar_bpm en la versión GTK: los -5/+5, el
  // campo editable y el slider nunca quedan desalineados entre sí)
  function aplicarBpm(nuevoBpm) {
    const bpm = Motor.setBpm(nuevoBpm);
    sliderBpm.value = bpm;
    campoBpm.value = bpm + " BPM";
    // La pista clara a la izquierda de la manija se dibuja con un gradiente
    // en CSS; acá se le pasa el corte, porque WebKit no tiene equivalente a
    // ::-moz-range-progress.
    const pct = ((bpm - Motor.BPM_MIN) / (Motor.BPM_MAX - Motor.BPM_MIN)) * 100;
    sliderBpm.style.setProperty("--pct", pct + "%");
  }

  botonMenos5.addEventListener("click", () => aplicarBpm(Motor.bpm - 5));
  botonMas5.addEventListener("click", () => aplicarBpm(Motor.bpm + 5));

  sliderBpm.addEventListener("input", () => aplicarBpm(sliderBpm.value));

  campoBpm.addEventListener("focus", () => campoBpm.select());
  campoBpm.addEventListener("blur", confirmarBpmEditado);
  campoBpm.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") campoBpm.blur();
  });

  function confirmarBpmEditado() {
    // El texto es "120 BPM" completo; solo el primer token es el número.
    const token = campoBpm.value.trim().split(/\s+/)[0];
    const valor = parseInt(token, 10);
    aplicarBpm(Number.isNaN(valor) ? Motor.bpm : valor);
  }

  // ---- ON / OFF ----
  botonIo.addEventListener("click", async () => {
    if (!Motor.playing) {
      await Motor.iniciar();
      botonIo.textContent = "OFF";
      botonIo.classList.add("io-encendido");
    } else {
      Motor.detener();
      botonIo.textContent = "ON";
      botonIo.classList.remove("io-encendido");
      apagarCirculos();
    }
  });

  // ---- Selector de subdivisión ----
  grupoSubdiv.addEventListener("click", (evento) => {
    const boton = evento.target.closest(".toggle-sub");
    if (!boton) return;
    grupoSubdiv.querySelectorAll(".toggle-sub").forEach((b) => b.classList.remove("activo"));
    boton.classList.add("activo");
    Motor.setSubdiv(parseInt(boton.dataset.valor, 10));
  });

  // ---- Diálogo "Acerca de" ----
  botonAcercaDe.addEventListener("click", () => dialogoAcercaDe.showModal());
  dialogoAcercaDe.querySelector(".cerrar-dialogo").addEventListener("click", (evento) => {
    evento.preventDefault();
    dialogoAcercaDe.close();
  });

  // ---- Círculos animados (equivalente de dibujar_circulos en interfaz.py) ----
  // progreso: 0 = recién disparado (máxima opacidad), 1 = totalmente apagado.
  // animarA300ms reproduce el mismo ritmo de fade que animar_beat/animar_sub
  // (20 pasos de 0.05 cada 15ms ≈ 300ms), pero con requestAnimationFrame
  // en vez de un contador de pasos discretos.
  const DURACION_FADE_MS = 300;
  let progresoOnda = 1.0;
  let progresoSub = 1.0;
  let inicioOnda = null;
  let inicioSub = null;

  function animarA300ms(timestamp) {
    if (inicioOnda !== null) {
      progresoOnda = Math.min(1, (timestamp - inicioOnda) / DURACION_FADE_MS);
      if (progresoOnda >= 1) inicioOnda = null;
    }
    if (inicioSub !== null) {
      progresoSub = Math.min(1, (timestamp - inicioSub) / DURACION_FADE_MS);
      if (progresoSub >= 1) inicioSub = null;
    }
    dibujarCirculos();
    requestAnimationFrame(animarA300ms);
  }

  function apagarCirculos() {
    progresoOnda = 1.0;
    progresoSub = 1.0;
    inicioOnda = null;
    inicioSub = null;
    dibujarCirculos();
  }

  // El canvas se redimensiona con el layout y se escala por devicePixelRatio,
  // si no, en pantallas densas (cualquier móvil) los círculos salen borrosos.
  let anchoCss = 0;
  let altoCss = 0;

  function redimensionarCanvas() {
    const dpr = window.devicePixelRatio || 1;
    anchoCss = canvas.clientWidth;
    altoCss = canvas.clientHeight;
    canvas.width = Math.round(anchoCss * dpr);
    canvas.height = Math.round(altoCss * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    dibujarCirculos();
  }

  // Ruido: se genera una sola vez y se reutiliza como patrón, igual que
  // PATRON_RUIDO en interfaz.py (renderizarlo en cada frame sería costoso).
  const patronRuido = (() => {
    const lienzo = document.createElement("canvas");
    lienzo.width = lienzo.height = 120;
    const c = lienzo.getContext("2d");
    const datos = c.createImageData(120, 120);
    for (let i = 0; i < datos.data.length; i += 4) {
      const v = (Math.random() * 255) | 0;
      datos.data[i] = datos.data[i + 1] = datos.data[i + 2] = v;
      datos.data[i + 3] = 255;
    }
    c.putImageData(datos, 0, 0);
    return ctx.createPattern(lienzo, "repeat");
  })();

  function circuloConRuido(cx, cy, radio, paradas, alpha) {
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radio);
    grad.addColorStop(0, paradas[0]);
    grad.addColorStop(1, paradas[1]);

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radio, 0, Math.PI * 2);
    ctx.clip();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.globalAlpha = alpha * 0.045;  // textura apenas perceptible, como en GTK
    ctx.fillStyle = patronRuido;
    ctx.fill();
    ctx.restore();
  }

  function dibujarCirculos() {
    if (!anchoCss || !altoCss) return;
    const cx = anchoCss / 2;
    const cy = altoCss / 2;
    // Proporciones del original: radios de 150 y 50 sobre un área de 400.
    const base = Math.min(anchoCss, altoCss);
    const radio1 = base * 0.375;
    const radio2 = base * 0.125;

    ctx.clearRect(0, 0, anchoCss, altoCss);
    circuloConRuido(cx, cy, radio1, ["#8c9eb8", "#4d5c73"], Math.max(0.2, 1 - progresoOnda));
    circuloConRuido(cx, cy, radio2, ["#338099", "#4d99cc"], Math.max(0.1, 1 - progresoSub));
  }

  Motor.onVisualEvent = (kind) => {
    const ahora = performance.now();
    if (kind === "beat") {
      progresoOnda = 0;
      inicioOnda = ahora;
    } else {
      progresoSub = 0;
      inicioSub = ahora;
    }
  };

  new ResizeObserver(redimensionarCanvas).observe(canvas);
  redimensionarCanvas();
  aplicarBpm(Motor.bpm);
  requestAnimationFrame(animarA300ms);
})();
