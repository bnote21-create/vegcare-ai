// Service Worker for VegCare AI
const CACHE_NAME = 'vegcare-ai-v1';
const STATIC_ASSETS = [
  '/',
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-maskable.png',
  '/samples/cabbage_healthy.png',
  '/samples/tomato_blight.png',
  '/samples/chili_leaf_curl.png',
  '/samples/cucumber_downy_mildew.png',
  '/samples/kale_caterpillar.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // ข้ามการแคชสำหรับ API analyze หรือ API ที่ใช้ POST
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/analyze')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // ดึงข้อมูลใหม่จากเครือข่ายเบื้องหลัง (Stale-while-revalidate)
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, networkResponse);
            });
          }
        }).catch(() => {});
        return cachedResponse;
      }

      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }

        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return response;
      }).catch(() => {
        // ออฟไลน์และไม่มีในแคช
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      });
    })
  );
});
