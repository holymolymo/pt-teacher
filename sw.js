// Service Worker: macht die App installierbar und offline nutzbar.
// HTML: Netz zuerst (immer frische Inhalte), Cache als Fallback.
// Alles andere (CSS/JS/Icons/Fonts): Cache zuerst, im Hintergrund aktualisieren.
// Bei Änderungen an der Liste oder Strategie: CACHE-Version hochzählen.

const CACHE = 'pt-teacher-v3';
const CORE = [
  './', './index.html', './lernen.html', './fortschritt.html', './vokabeln.html',
  './diagnose-test.html', './print-sheets.html', './grammatik-bibliothek.html', './cheat-sheet.html',
  './uebung-perfeito-tempus.html',
  './tiefenuebung-01-unregelmaessige.html', './tiefenuebung-02-preterito-perfeito.html', './tiefenuebung-03-imperfeito.html',
  './lektion-01-chamar-se.html', './lektion-02-ser-artigos.html', './lektion-03-nacionalidades-profissoes.html',
  './lektion-04-ter-numeros.html', './lektion-05-ar-verben.html', './lektion-06-kontraktionen.html',
  './lektion-07-fragewoerter.html', './lektion-08-estar-vs-ser.html', './lektion-09-preterito-perfeito.html',
  './lektion-10-mega-session.html', './lektion-11-preterito-imperfeito.html', './lektion-12-possessivpronomen.html',
  './lektion-13-ir-infinitiv.html', './lektion-14-estar-a-uhrzeit.html', './lektion-15-ir-verben.html',
  './lektion-16-objektpronomen.html', './lektion-17-demonstrativ.html', './lektion-18-komparativ-zeit.html',
  './lektion-19-reflexive-stellung.html', './lektion-20-konditional.html', './lektion-21-por-vs-para.html',
  './wiederholung-01.html', './wiederholung-02.html', './wiederholung-03.html', './wiederholung-04.html',
  './wiederholung-05.html', './wiederholung-komplett.html',
  './css/app-shell.css?v=20260819b', './js/progress.js?v=20260819b', './js/app-shell.js?v=20260819b',
  './icons/icon-192.png', './icons/icon-512.png', './icons/icon-apple.png', './manifest.json'
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c =>
      Promise.allSettled(CORE.map(url => c.add(url).catch(() => null)))
    )
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const isHTML = req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');

  if (isHTML) {
    e.respondWith(
      fetch(req).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(req, clone));
        return res;
      }).catch(() => caches.match(req).then(c => c || caches.match('./index.html')))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then(cached => {
      const network = fetch(req).then(res => {
        if (res && res.status === 200) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
