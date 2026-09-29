// ═══════════════════════════════════════════════════════════
// H1-AI Service Worker — PWA Cache
// ═══════════════════════════════════════════════════════════
const CACHE_NAME = 'h1ai-v1';
const STATIC_ASSETS = [
    '/admin',
    '/admin/static/app.css',
    '/admin/static/app.js',
    '/admin/static/manifest.json',
    '/admin/static/css/mobile.css',
    '/admin/static/css/dark.css',
    '/admin/static/css/responsive-fix.css',
    '/admin/static/css/mobile-sidebar-fix.css',
    '/admin/static/css/sidebar-force-fix.css',
];

// Install
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys().then(keys => 
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

// Fetch — Network first, Cache fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    
    // API requests — network only
    if (request.url.includes('/v1/') || request.url.includes('/api/')) {
        return;
    }
    
    // Static assets — cache first
    event.respondWith(
        caches.match(request).then(cached => {
            if (cached) return cached;
            
            return fetch(request).then(response => {
                if (!response || response.status !== 200 || response.type === 'opaque') {
                    return response;
                }
                
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, responseClone);
                });
                
                return response;
            }).catch(() => {
                // Offline fallback
                if (request.mode === 'navigate') {
                    return caches.match('/admin');
                }
            });
        })
    );
});
