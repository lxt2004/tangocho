const CACHE = "tangocho-en-v3";   // jp 版と同じ名前にすると、片方の activate がもう片方のキャッシュを消す
const ROOT  = new URL("./", self.registration.scope).pathname;
const ASSETS = ["./", "./index.html", "./manifest.webmanifest",
                "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];
// フォントの CSS は別オリジンで、返るのは opaque response。
// addAll は status 0 を弾いて install ごと失敗させるので、put で個別に温める。
const WARM = ["https://fonts.googleapis.com/css2?family=Klee+One:wght@400;600&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;500&display=swap"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c =>
    c.addAll(ASSETS).then(() => Promise.all(WARM.map(u =>
      fetch(u, {mode:"no-cors"}).then(r => c.put(u, r)).catch(() => {})
    )))
  ).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const isFont = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);

  // ページ本体は network-first。キャッシュのキーは実URLにする（別アプリを上書きしないため）
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request)
      .then(res => { const c = res.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return res; })
      .catch(() => caches.match(e.request).then(r => r || caches.match(ROOT))));
    return;
  }
  if (url.origin === location.origin || isFont) {
    e.respondWith(caches.match(e.request).then(hit => hit ||
      fetch(e.request).then(res => { const c = res.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return res; })));
  }
});
