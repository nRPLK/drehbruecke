// Service Worker für Erinnerungen (Push) von Drehbrücke
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('push',e=>{
  let d={};try{d=e.data?e.data.json():{}}catch(_){}
  const n=d.notification||d.data||{};
  e.waitUntil(self.registration.showNotification(n.title||'Drehbrücke 🌉',{body:n.body||'Komm zurück und spiel eine Runde!',icon:'icon-192.png',badge:'icon-192.png',tag:'drehbruecke',data:{url:(d.data&&d.data.url)||'./'}}));
});
self.addEventListener('notificationclick',e=>{e.notification.close();const url=(e.notification.data&&e.notification.data.url)||'./';
  e.waitUntil(self.clients.matchAll({type:'window'}).then(cs=>{for(const c of cs){if('focus' in c)return c.focus()}return self.clients.openWindow(url)}))});
