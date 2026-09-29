/* =============================================================================
   vokabel-sync.js — jede Antwort sofort sichern, auch ohne Netz
   =============================================================================

   Moritz' Anforderung war: alles muss direkt nach der Eingabe gespeichert und
   immer abrufbar sein, damit nichts verloren geht.

   Deshalb drei Schichten, von schnell nach dauerhaft:

     1. localStorage, sofort und ohne Netz. Hier steht der Lernstand.
     2. eine Warteschlange, ebenfalls lokal. Jede Antwort landet hier, bevor
        irgendetwas verschickt wird.
     3. Supabase, im Hintergrund und gebündelt. Nur Anhängen, nie Ändern.
        Jede Zeile trägt den errechneten Termin gleich mit, damit ein zweites
        Gerät den Stand übernehmen kann, ohne nachzurechnen, und damit ich den
        Stand lesen kann, ohne die Datendatei zu kennen.

   WICHTIG: Das Supabase-Projekt liegt im Gratis-Tarif und pausiert nach etwa
   einer Woche ohne Zugriff. Dann schlagen die Sendeversuche fehl. Das ist kein
   Datenverlust: die Warteschlange bleibt liegen und wird abgearbeitet, sobald
   die Datenbank wieder da ist. Die App funktioniert währenddessen vollständig.
   ========================================================================== */

(function () {
  'use strict';

  var SB = {
    url: 'https://zhddqcgvrfhajbgpekon.supabase.co',
    key: 'sb_publishable_FuqpDPiql_-yAbBauzq06Q_of3BWnMd',
    tabelle: 'pt_vokabel_log',
    sicht: 'pt_vokabel_stand'
  };
  var KOPF = { 'apikey': SB.key, 'Authorization': 'Bearer ' + SB.key, 'Content-Type': 'application/json' };

  var Q_KEY    = 'pt_vokabel_queue';
  var META_KEY = 'pt_vokabel_sync_meta';
  var Q_MAX    = 3000;          // reicht für Monate ohne Netz
  var BUENDEL  = 50;

  function lies(k, e) { try { var r = localStorage.getItem(k); return r ? JSON.parse(r) : e; } catch (x) { return e; } }
  function schreib(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (x) { return false; } }
  function meta(patch) {
    var m = lies(META_KEY, {});
    if (patch) { for (var k in patch) m[k] = patch[k]; schreib(META_KEY, m); }
    return m;
  }

  function geraet() {
    var ua = navigator.userAgent;
    var g = /iPhone/.test(ua) ? 'iPhone' : /iPad/.test(ua) ? 'iPad' : /Android/.test(ua) ? 'Android'
          : /Macintosh/.test(ua) ? 'Mac' : /Windows/.test(ua) ? 'Windows' : 'Gerät';
    var app = window.matchMedia && window.matchMedia('(display-mode: standalone)').matches;
    return g + (app ? ' (App)' : '');
  }

  function kennung() {
    // Eindeutig genug, ohne Zufallsquelle zu brauchen, die es überall gibt.
    return 'v' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
  }

  /** Eine Antwort in die Warteschlange legen. Wird von srs.js bei JEDER Antwort gerufen. */
  function merke(zeile) {
    var q = lies(Q_KEY, []);
    zeile.client_id = kennung();
    zeile.client_ts = new Date().toISOString();
    zeile.device = geraet();
    q.push(zeile);
    // Läuft die Warteschlange über, fallen die ÄLTESTEN Einträge heraus. Der
    // Lernstand selbst steht in localStorage und bleibt davon unberührt.
    if (q.length > Q_MAX) q = q.slice(q.length - Q_MAX);
    schreib(Q_KEY, q);
    planeSenden();
    return zeile.client_id;
  }

  var timer = null, laeuft = false;
  function planeSenden() {
    if (timer) return;
    timer = setTimeout(function () { timer = null; sende(); }, 4000);
  }

  /** Warteschlange abarbeiten. Fehler sind harmlos, es wird später erneut versucht. */
  async function sende() {
    if (laeuft || !navigator.onLine) return { gesendet: 0, offen: offen() };
    var q = lies(Q_KEY, []);
    if (!q.length) return { gesendet: 0, offen: 0 };
    laeuft = true;
    var gesendet = 0;
    try {
      while (q.length) {
        var teil = q.slice(0, BUENDEL);
        var res = await fetch(SB.url + '/rest/v1/' + SB.tabelle + '?on_conflict=client_id', {
          method: 'POST',
          headers: Object.assign({}, KOPF, { 'Prefer': 'resolution=ignore-duplicates,return=minimal' }),
          body: JSON.stringify(teil)
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        q = q.slice(teil.length);
        schreib(Q_KEY, q);
        gesendet += teil.length;
      }
      meta({ letzterVersand: new Date().toISOString(), fehler: null });
    } catch (e) {
      meta({ letzterVersand: meta().letzterVersand || null, fehler: String(e.message || e) });
    } finally {
      laeuft = false;
    }
    melde();
    return { gesendet: gesendet, offen: offen() };
  }

  function offen() { return lies(Q_KEY, []).length; }

  function melde() {
    try { window.dispatchEvent(new CustomEvent('ptvokabel:sync', { detail: status() })); } catch (e) {}
  }

  function status() {
    var m = meta();
    return {
      offen: offen(), letzterVersand: m.letzterVersand || null, fehler: m.fehler || null,
      letzterAbruf: m.letzterAbruf || null, online: navigator.onLine
    };
  }

  /**
   * Stand aus der Cloud holen. Nur nötig auf einem zweiten Gerät oder nachdem
   * lokal etwas verloren ging. Höchstens alle zwei Stunden.
   */
  async function hole(erzwingen) {
    var m = meta();
    if (!erzwingen && m.letzterAbruf && (Date.now() - new Date(m.letzterAbruf)) < 2 * 3600 * 1000) return null;
    if (!navigator.onLine) return null;
    try {
      var res = await fetch(SB.url + '/rest/v1/' + SB.sicht +
        '?select=aufgabe_id,richtung,note,wdh,intervall,faktor,faellig,client_ts&limit=5000', { headers: KOPF });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var zeilen = await res.json();
      var uebernommen = window.PTSrs ? window.PTSrs.uebernehme(zeilen) : 0;
      meta({ letzterAbruf: new Date().toISOString(), fehler: null });
      melde();
      return { geholt: zeilen.length, uebernommen: uebernommen };
    } catch (e) {
      meta({ fehler: String(e.message || e) });
      return null;
    }
  }

  /** Notausgang ohne Cloud: alles als Datei speichern. */
  function alsDatei() {
    var daten = {
      erzeugt: new Date().toISOString(),
      geraet: geraet(),
      stand: window.PTSrs ? window.PTSrs.staende() : {},
      warteschlange: lies(Q_KEY, [])
    };
    var blob = new Blob([JSON.stringify(daten, null, 1)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'pt-vokabelstand-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  window.PTVokabelSync = {
    merke: merke, sende: sende, hole: hole, status: status, alsDatei: alsDatei,
    SUPABASE: { url: SB.url, tabelle: SB.tabelle }
  };

  window.addEventListener('online', function () { sende(); });
  // Beim Verlassen der Seite noch einmal versuchen, damit nichts liegen bleibt.
  window.addEventListener('pagehide', function () {
    var q = lies(Q_KEY, []);
    if (!q.length || !navigator.sendBeacon) return;
    try {
      var url = SB.url + '/rest/v1/' + SB.tabelle + '?apikey=' + encodeURIComponent(SB.key);
      // Obergrenze für sendBeacon liegt bei 64 kB. Deshalb nur zwanzig Zeilen
      // und ohne die langen Textfelder; die kommen beim nächsten regulären
      // Versand ohnehin mit, die Warteschlange bleibt ja stehen.
      var schlank = q.slice(0, 20).map(function (z) {
        return { client_id: z.client_id, client_ts: z.client_ts, device: z.device,
                 aufgabe_id: z.aufgabe_id, paket: z.paket, richtung: z.richtung, note: z.note,
                 richtig: z.richtig, ms: z.ms, wdh: z.wdh, intervall: z.intervall,
                 faktor: z.faktor, faellig: z.faellig };
      });
      var blob = new Blob([JSON.stringify(schlank)], { type: 'application/json' });
      navigator.sendBeacon(url, blob);   // best effort, die Warteschlange bleibt trotzdem stehen
    } catch (e) {}
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { sende(); });
  else sende();
})();
