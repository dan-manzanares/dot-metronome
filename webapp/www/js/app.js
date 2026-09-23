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
  const sliderVolumen = document.getElementById("slider-volumen");
  const botonAcercaDe = document.getElementById("boton-acerca-de");
  const dialogoAcercaDe = document.getElementById("dialogo-acerca-de");
  const menuTemas = document.getElementById("menu-temas");
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
    // Igual que int() en motor.py: "120abc" es inválido (parseInt lo
    // aceptaría como 120), y un texto inválido vuelve al valor previo.
    const token = campoBpm.value.trim().split(/\s+/)[0];
    aplicarBpm(/^[+-]?\d+$/.test(token) ? parseInt(token, 10) : Motor.bpm);
  }

  // ---- ON / OFF ----
  let arrancando = false;
  botonIo.addEventListener("click", async () => {
    if (arrancando) return; // el sonido todavía se está cargando
    if (!Motor.playing) {
      arrancando = true;
      try {
        await Motor.iniciar();
      } finally {
        arrancando = false;
      }
      botonIo.textContent = "OFF";
      botonIo.classList.add("io-encendido");
      animar();
    } else {
      // Como en motor.onoff: el sonido se corta en seco, pero el
      // desvanecido de los círculos que ya estaba en curso termina solo.
      Motor.detener();
      botonIo.textContent = "ON";
      botonIo.classList.remove("io-encendido");
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

  // ---- Volumen (equivalente de cambiar_volumen en interfaz.py) ----
  const VOLUMEN_MAX = 125; // más de 100 % amplifica; ese tramo se pinta con el rojo del tema

  function aplicarVolumen(valor) {
    const volumen = Math.max(0, Math.min(VOLUMEN_MAX, Math.round(valor)));
    Motor.setVolumen(volumen);
    sliderVolumen.value = volumen;
    // --f: fracción del valor, que el CSS usa para ubicar el fin del relleno
    // y el inicio del rojo en la marca de 100 %. --corte: dónde empieza el
    // rojo dentro de la barra de progreso de Firefox, que mide solo la parte
    // rellena (f × ancho) mientras que la marca está en el recorrido de la
    // manija (igual idea que pintar_volumen en interfaz.py).
    const f = volumen / VOLUMEN_MAX;
    sliderVolumen.style.setProperty("--f", f);
    let corte = "100%";
    if (volumen > 100) {
      const ancho = sliderVolumen.clientWidth || 1;
      const marca100 = 9.5 + (ancho - 19) * (100 / VOLUMEN_MAX);
      corte = (marca100 / (f * ancho)) * 100 + "%";
    }
    sliderVolumen.style.setProperty("--corte", corte);
    return volumen;
  }

  sliderVolumen.addEventListener("input", () => aplicarVolumen(sliderVolumen.value));
  // Se guarda al soltar el slider, no en cada paso del arrastre
  sliderVolumen.addEventListener("change", () => {
    try { localStorage.setItem("volumen", sliderVolumen.value); } catch (e) {}
  });

  function leerVolumenGuardado() {
    try {
      const guardado = parseInt(localStorage.getItem("volumen"), 10);
      if (!Number.isNaN(guardado)) return guardado;
    } catch (e) {}
    return 100;
  }

  // ---- Tap tempo: clic en los círculos ----
  canvas.addEventListener("click", () => {
    const nuevoBpm = Motor.tap();
    if (nuevoBpm !== null) aplicarBpm(nuevoBpm);
  });

  // ---- Diálogo "Acerca de" ----
  botonAcercaDe.addEventListener("click", () => dialogoAcercaDe.showModal());
  dialogoAcercaDe.querySelector(".cerrar-dialogo").addEventListener("click", (evento) => {
    evento.preventDefault();
    dialogoAcercaDe.close();
  });

  // ---- Tema ----
  // El tema es un atributo data-tema en <html> que redefine las variables de
  // estilo.css; "oscuro" es la ausencia del atributo. El tema guardado ya se
  // aplicó en el <head> de index.html, antes de cargar el CSS. Las etiquetas
  // de cada tema están en el menú de index.html (equivalente de TEMAS en
  // interfaz.py).
  const COLOR_BARRA = {
    oscuro: "#24212c", catppuccin: "#181825", latte: "#dce0e8",
    nord: "#2e3440", "nord-claro": "#d8dee9",
    gruvbox: "#282828", "gruvbox-claro": "#ebdbb2",
  };
  const metaColorTema = document.querySelector('meta[name="theme-color"]');
  const opcionesTema = menuTemas.querySelectorAll(".opcion-tema");

  function aplicarTema(tema) {
    if (tema === "oscuro") delete document.documentElement.dataset.tema;
    else document.documentElement.dataset.tema = tema;
    metaColorTema.content = COLOR_BARRA[tema];
    opcionesTema.forEach((o) => o.classList.toggle("activo", o.dataset.tema === tema));
    try { localStorage.setItem("tema", tema); } catch (e) {}
    leerColoresCirculos();
    dibujarCirculos();
  }

  menuTemas.addEventListener("click", (evento) => {
    const opcion = evento.target.closest(".opcion-tema");
    if (!opcion) return;
    aplicarTema(opcion.dataset.tema);
    menuTemas.hidePopover();
  });

  // ---- Círculos animados (equivalente de dibujar_circulos en interfaz.py) ----
  // progreso: 0 = recién disparado (máxima opacidad), 1 = totalmente apagado.
  // alCuadro es el equivalente de _al_cuadro en motor.py: corre una vez por
  // cuadro solo mientras hay algo que animar (así no gasta batería en
  // reposo), no decide cuándo suena nada, y enciende los círculos cuando el
  // clic de verdad se oye.
  const DURACION_ANIMACION_MS = 300;
  let progresoOnda = 1.0;
  let progresoSub = 1.0;
  let inicioOnda = -Infinity;
  let inicioSub = -Infinity;
  let cuadroId = null;

  function alCuadro(ahora) {
    for (const esBeat of Motor.eventosSonados()) {
      if (esBeat) inicioOnda = ahora;
      inicioSub = ahora; // cada clic (beat incluido) enciende el círculo chico
    }

    const onda = Math.min(1, (ahora - inicioOnda) / DURACION_ANIMACION_MS);
    const sub = Math.min(1, (ahora - inicioSub) / DURACION_ANIMACION_MS);
    if (onda !== progresoOnda || sub !== progresoSub) {
      progresoOnda = onda;
      progresoSub = sub;
      dibujarCirculos();
    }

    if (!Motor.playing && onda >= 1 && sub >= 1) {
      cuadroId = null; // apagado y animaciones terminadas: deja de correr
      return;
    }
    cuadroId = requestAnimationFrame(alCuadro);
  }

  function animar() {
    if (cuadroId === null) cuadroId = requestAnimationFrame(alCuadro);
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

  // Los colores de los círculos viven en estilo.css (--circulo-*). Se leen una
  // vez por tema y no en cada frame, porque getComputedStyle es costoso.
  let coloresCirculos;
  function leerColoresCirculos() {
    const estilo = getComputedStyle(document.documentElement);
    const color = (nombre) => estilo.getPropertyValue(nombre).trim();
    coloresCirculos = {
      beat: [color("--circulo-beat-1"), color("--circulo-beat-2")],
      sub: [color("--circulo-sub-1"), color("--circulo-sub-2")],
    };
  }
  leerColoresCirculos();

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
    circuloConRuido(cx, cy, radio1, coloresCirculos.beat, Math.max(0.2, 1 - progresoOnda));
    circuloConRuido(cx, cy, radio2, coloresCirculos.sub, Math.max(0.1, 1 - progresoSub));
  }

  new ResizeObserver(redimensionarCanvas).observe(canvas);
  redimensionarCanvas();
  aplicarBpm(Motor.bpm);
  aplicarVolumen(leerVolumenGuardado());
  // --corte depende del ancho del slider
  new ResizeObserver(() => aplicarVolumen(sliderVolumen.value)).observe(sliderVolumen);
  // Marca la opción del menú y lee los colores de los círculos del tema que
  // el <head> ya aplicó. Va acá, no en la sección del tema, porque necesita
  // las funciones de dibujo que se definen más abajo.
  aplicarTema(document.documentElement.dataset.tema || "oscuro");
})();
