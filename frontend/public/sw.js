const CACHE_NAME = "xuexibao-shell-v2";
const SHELL_ASSETS = ["/", "/manifest.webmanifest", "/icon.svg"];
const API_PREFIXES = [
  "/auth", "/courses", "/practice", "/questions", "/wrongbook", "/imports",
  "/library", "/chat", "/exams", "/admin", "/tags", "/recommendations",
  "/analytics", "/exports", "/bookmarks", "/health",
];

function isApiRequest(url) {
  return API_PREFIXES.some((prefix) => url.pathname === prefix || url.pathname.startsWith(`${prefix}/`));
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match("/")));
    return;
  }

  // Learning records must always come from the server while online. Caching
  // API responses here caused stale statistics, wrong-book entries and exams.
  if (isApiRequest(url)) {
    event.respondWith(fetch(request));
    return;
  }

  if (["script", "style", "image", "font"].includes(request.destination)) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request).then((response) => {
        if (response.ok) {
          caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
        }
        return response;
      })),
    );
  }
});
