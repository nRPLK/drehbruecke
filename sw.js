// Service Worker für Drehbrücke: macht das Spiel installierbar, offline-fähig
// und nimmt die Erinnerungen (Push) entgegen.
const V = 'db-v2';
const SHELL = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL).catch(() => {})));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Netz zuerst, Cache als Reserve: Updates kommen sofort an, offline läuft es trotzdem.
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  let u;
  try { u = new URL(r.url); } catch (_) { return; }
  if (u.origin !== location.origin) return;           // Firebase & Co. nie abfangen
  e.respondWith(
    fetch(r).then(resp => {
      if (resp && resp.ok) { const cp = resp.clone(); caches.open(V).then(c => c.put(r, cp)).catch(() => {}); }
      return resp;
    }).catch(() => caches.match(r).then(m => m || caches.match('./index.html')))
  );
});

// ---- Erinnerungen ----
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) {}
  const n = d.notification || d.data || {};
  e.waitUntil(self.registration.showNotification(n.title || 'Drehbrücke 🌉', {
    body: n.body || 'Komm zurück und spiel eine Runde!',
    icon: 'icon-192.png', badge: 'icon-192.png', tag: 'drehbruecke',
    data: { url: (d.data && d.data.url) || './' }
  }));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(self.clients.matchAll({ type: 'window' }).then(cs => {
    for (const c of cs) { if ('focus' in c) return c.focus(); }
    return self.clients.openWindow(url);
  }));
});
