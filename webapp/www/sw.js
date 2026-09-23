// Service worker de Dot (PWA): la app abre al instante desde la caché y
// funciona sin conexión. No interviene en el audio ni en el ritmo: solo
// sirve los archivos de la página.
//
// Estrategia "stale-while-revalidate": cada archivo se responde desde la
// caché (sin esperar la red) y, en paralelo, se pide la versión nueva para
// la próxima vez. Así, al publicar cambios en el sitio no hace falta tocar
// este archivo: la app se actualiza sola en la visita siguiente.
// VERSION_CACHE solo se sube si cambia la lista de ARCHIVOS o para forzar
// que se descarte todo lo guardado.

const VERSION_CACHE = "dot-v1";

const ARCHIVOS = [
  "./",
  "index.html",
  "css/estilo.css",
  "js/motor.js",
  "js/app.js",
  "resources/beat.mp3",
  "favicon.svg",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/maskable-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(VERSION_CACHE)
      .then((cache) => cache.addAll(ARCHIVOS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (evento) => {
  // Borra las cachés de versiones anteriores
  evento.waitUntil(
    caches.keys()
      .then((nombres) => Promise.all(
        nombres.filter((n) => n !== VERSION_CACHE).map((n) => caches.delete(n))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const pedido = evento.request;
  // Solo archivos propios; los enlaces externos (Buy me a coffee, licencia)
  // van directo a la red.
  if (pedido.method !== "GET" || new URL(pedido.url).origin !== self.location.origin) return;

  evento.respondWith((async () => {
    const cache = await caches.open(VERSION_CACHE);
    const guardada = await cache.match(pedido, { ignoreSearch: true });
    const deRed = fetch(pedido)
      .then((respuesta) => {
        if (respuesta.ok) cache.put(pedido, respuesta.clone());
        return respuesta;
      })
      .catch(() => guardada); // sin conexión: lo que haya en caché
    // Mantiene vivo el service worker hasta que termine la actualización
    evento.waitUntil(deRed.catch(() => {}));
    return guardada || deRed;
  })());
});
