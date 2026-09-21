// H1-AI Service Worker v2 — Stable URL Only
const CACHE_NAME = 'h1ai-v2';
const STABLE_DOMAIN = 'h.tailc0256.ts.net';

self.addEventListener('install', (event) => {
    console.log('[SW] Installing v2...');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[SW] Activating v2...');
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // تجاهل أي host مش الـ stable domain
    if (url.hostname !== STABLE_DOMAIN &&
        url.hostname !== 'localhost' &&
        url.hostname !== '127.0.0.1') {
        return;
    }

    // API — network only
    if (url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/v1/') ||
        url.pathname.startsWith('/webhook/')) {
        return;
    }

    // Static assets — cache first
    if (event.request.method === 'GET' &&
        (url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.svg'))) {
        event.respondWith(
            caches.match(event.request).then(cached => {
                return cached || fetch(event.request).then(res => {
                    const clone = res.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    return res;
                });
            })
        );
    }
});
