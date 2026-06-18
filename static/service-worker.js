// Service worker do Controle de Esmaltes.
// Cache do "app shell" para permitir abrir o app offline. As chamadas de
// API e as fotos (/api, /uploads) sempre vão à rede para refletir os dados.
const CACHE = "esmaltes-shell-v1";
const SHELL = [
  "/",
  "/index.html",
  "/styles.css",
  "/app.js",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((ks) =>
      Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  // Dados dinâmicos: sempre rede.
  if (url.pathname.startsWith("/api") || url.pathname.startsWith("/uploads")) return;
  // App shell: cache primeiro, com atualização em segundo plano.
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const rede = fetch(e.request).then((resp) => {
        if (resp.ok) caches.open(CACHE).then((c) => c.put(e.request, resp.clone()));
        return resp;
      }).catch(() => cached);
      return cached || rede;
    })
  );
});
