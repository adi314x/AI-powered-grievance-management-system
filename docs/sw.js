/* Service Worker - PWA Offline Support */
const CACHE_NAME = 'grievance-v2';
const STATIC_CACHE = [
  '/',
  '/index.html',
  '/login.html',
  '/styles.css',
  '/app.js',
  '/government-portal-theme.css',
  '/improved-contrast.css',
  '/design-system.css',
  '/vendor/bootstrap/bootstrap.min.css',
  '/vendor/bootstrap/bootstrap.bundle.min.js',
  '/vendor/tabler/tabler-icons.min.css',
  '/vendor/tabler/fonts/tabler-icons.woff2',
  '/vendor/chartjs/chart.umd.min.js',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_CACHE).catch(() => {});
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/')) return;
  e.respondWith(
    fetch(e.request).catch(() =>
      caches.match(e.request).then((r) => r || caches.match('/index.html'))
    )
  );
});
