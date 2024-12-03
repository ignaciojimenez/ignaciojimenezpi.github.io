const CACHE_NAME = 'photography-cache-v1';
const STATIC_ASSETS = [
    '/photography/',
    '/photography/index.html',
    '/photography/css/styles.css',
    '/photography/js/gallery.js',
    'https://cdn.tailwindcss.com',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(name => name !== CACHE_NAME)
                        .map(name => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Helper function to determine if request is for an image
function isImageRequest(request) {
    return request.destination === 'image' || request.url.match(/\.(jpg|jpeg|png|webp)$/i);
}

// Helper function to determine if request is for JSON data
function isJSONRequest(request) {
    return request.url.endsWith('.json');
}

// Fetch event - handle requests
self.addEventListener('fetch', event => {
    // Skip cross-origin requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            // Return cached response if available
            if (cachedResponse) {
                // For JSON files, check if there's a newer version
                if (isJSONRequest(event.request)) {
                    return fetch(event.request)
                        .then(response => {
                            // Update cache with new response
                            const clonedResponse = response.clone();
                            caches.open(CACHE_NAME).then(cache => {
                                cache.put(event.request, clonedResponse);
                            });
                            return response;
                        })
                        .catch(() => cachedResponse);
                }
                return cachedResponse;
            }

            return fetch(event.request).then(response => {
                // Don't cache non-successful responses
                if (!response.ok) {
                    return response;
                }

                // Clone the response
                const responseToCache = response.clone();

                // Cache the fetched response
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseToCache);
                });

                return response;
            });
        })
    );
});
