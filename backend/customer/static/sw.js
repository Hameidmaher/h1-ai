// H1-AI Admin — Service Worker
const CACHE_VERSION = 'h1ai-admin-v' + Date.now();
const CACHE_NAME = 'h1ai-admin-' + CACHE_VERSION;

// الملفات الأساسية للكاش
const PRECACHE = [
  '/chat',
  '/chat/static/app.css',
  '/chat/static/app.js',
  '/chat/static/pwa/manifest.json',
];

// ═══ Install ═══
self.addEventListener('install', (event) => {
  console.log('[SW] Installing:', CACHE_VERSION);
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE.map(url => new Request(url, { credentials: 'same-origin' })))
        .catch(err => console.log('[SW] Precache failed:', err));
    })
  );
  self.skipWaiting();
});

// ═══ Activate ═══
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating:', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter(k => k.startsWith('h1ai-') && k !== CACHE_NAME)
            .map(k => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

// ═══ Fetch — Network First for API, Cache First for assets ═══
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API calls — network only
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/v1/')) {
    return; // default: network
  }

  // Static assets — cache first
  if (url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|woff2?|ttf)$/)) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return cached || fetch(event.request).then((res) => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return res;
        });
      })
    );
    return;
  }

  // HTML — network first, fallback to cache
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }
});

// ═══ Push Notifications ═══
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'H1-AI';
  const options = {
    body: data.body || 'لديك إشعار جديد',
    icon: '/chat/static/pwa/icon-192.png',
    badge: '/chat/static/pwa/icon-192.png',
    dir: 'rtl',
    lang: 'ar',
    data: data.url || '/chat',
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// ═══ Notification click ═══
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data || '/chat')
  );
});
