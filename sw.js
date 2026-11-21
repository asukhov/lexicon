/* Lexicon service worker: offline shell + cached dictionary data. */
const VERSION = 'lexicon-v25';
const SHELL = [
  './',
  './index.html',
  './assets/styles.css',
  './assets/app.js',
  './assets/fonts/inter-latin.woff2',
  './assets/favicon.svg',
  './manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(async (keys) => {
      const stale = keys.filter((key) => key !== VERSION);
      await Promise.all(stale.map((key) => caches.delete(key)));
      await self.clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const isData = url.pathname.includes('/data/');
  if (isData) {
    event.respondWith(
      caches.open(VERSION).then(async (cache) => {
        try {
          const response = await fetch(request, { cache: 'no-store' });
          if (response && response.ok) cache.put(request, response.clone());
          return response;
        } catch (error) {
          const cached = await cache.match(request);
          if (cached) return cached;
          throw error;
        }
      })
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response && response.ok) {
            caches.open(VERSION).then((cache) => cache.put(request, response.clone()));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
