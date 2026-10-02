/* =============================================================================
   vorlesen.js — die Karten laut hören, aber nur auf europäischem Portugiesisch
   =============================================================================

   DIE EINE REGEL, DIE ALLES BESTIMMT:
   Es wird ausschließlich mit einer pt-PT-Stimme gesprochen. Findet das Gerät
   keine, bleibt die App stumm und sagt das auch.

   Warum so streng: Auf einem Apple-Gerät stehen neun brasilianische Stimmen
   gegen genau eine europäische (Joana). Wer nur die Sprache anfordert und die
   Stimme dem Browser überlässt, bekommt mit hoher Wahrscheinlichkeit eine
   brasilianische. Sie würde Moritz genau die Aussprache antrainieren, gegen die
   in diesem Projekt jede einzelne Karte geschrieben ist. Lieber kein Ton als
   der falsche.

   Die Eigenheiten der Sprachausgabe auf dem iPhone, und wie sie hier behandelt
   werden:
     - getVoices() ist beim ersten Aufruf oft leer. Deshalb wird auf das
       Ereignis voiceschanged gewartet, mit einer Frist als Notausgang.
     - Das erste Sprechen braucht eine Nutzergeste. Deshalb gibt es einen
       Knopf, und automatisch gesprochen wird erst, nachdem einmal gedrückt wurde.
     - Bildschirmsperre und Wechsel in eine andere App brechen das Sprechen ab.
       Deshalb wird beim Verschwinden der Seite sauber abgebrochen.
     - speechSynthesis bleibt nach längerem Nichtstun manchmal hängen. Deshalb
       vor jedem Sprechen ein cancel().
   ========================================================================== */

(function () {
  'use strict';

  var OPT_KEY = 'pt_vorlesen';
  var stimme = null, bereit = false, geste = false, laeuft = false;
  var warteliste = [];

  function optionen(patch) {
    var o;
    try { o = JSON.parse(localStorage.getItem(OPT_KEY) || 'null'); } catch (e) { o = null; }
    o = o || { an: true, automatisch: false, tempo: 0.95 };
    if (patch) {
      for (var k in patch) o[k] = patch[k];
      try { localStorage.setItem(OPT_KEY, JSON.stringify(o)); } catch (e) {}
    }
    return o;
  }

  function istEuropaeisch(v) {
    // pt-PT, pt_PT oder schlicht pt. Alles mit BR fliegt raus.
    var l = (v.lang || '').replace('_', '-');
    if (/-BR$/i.test(l)) return false;
    return /^pt(-PT)?$/i.test(l);
  }

  function stimmeSuchen() {
    var alle = window.speechSynthesis ? speechSynthesis.getVoices() : [];
    if (!alle.length) return null;
    var pt = alle.filter(istEuropaeisch);
    if (!pt.length) return null;
    // Joana ist auf Apple-Geräten die europäische Stimme. Sonst die erste beste,
    // aber lokale vor solchen, die das Netz brauchen.
    pt.sort(function (a, b) {
      var ja = /joana/i.test(a.name) ? 0 : 1, jb = /joana/i.test(b.name) ? 0 : 1;
      if (ja !== jb) return ja - jb;
      return (a.localService ? 0 : 1) - (b.localService ? 0 : 1);
    });
    return pt[0];
  }

  function init() {
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) { melden(); return; }
    stimme = stimmeSuchen();
    if (stimme) { bereit = true; melden(); return; }
    // Stimmen laden auf dem iPhone verzögert nach.
    speechSynthesis.addEventListener('voiceschanged', function () {
      if (bereit) return;
      stimme = stimmeSuchen();
      bereit = !!stimme;
      melden();
      while (bereit && warteliste.length) sprich(warteliste.shift());
    });
    setTimeout(function () {
      if (bereit) return;
      stimme = stimmeSuchen();
      bereit = !!stimme;
      melden();
    }, 2500);
  }

  function melden() {
    try {
      window.dispatchEvent(new CustomEvent('ptvorlesen:bereit', {
        detail: { bereit: bereit, stimme: stimme ? stimme.name : null }
      }));
    } catch (e) {}
  }

  /**
   * Text vorlesen. Gibt true zurück, wenn tatsächlich gesprochen wurde.
   * Ohne europäische Stimme passiert absichtlich nichts.
   */
  function sprich(text, opt) {
    opt = opt || {};
    if (!text || !optionen().an) return false;
    if (!window.speechSynthesis) return false;
    if (!bereit) { if (warteliste.length < 2) warteliste.push(text); return false; }
    if (opt.nurNachGeste && !geste) return false;

    try {
      speechSynthesis.cancel();   // räumt hängengebliebene Ausgaben weg
      var u = new SpeechSynthesisUtterance(String(text));
      u.voice = stimme;           // ausdrücklich, nicht dem Browser überlassen
      u.lang = stimme.lang || 'pt-PT';
      u.rate = opt.tempo || optionen().tempo || 0.95;
      u.pitch = 1;
      u.onstart = function () { laeuft = true; zustand(); };
      u.onend = u.onerror = function () { laeuft = false; zustand(); };
      speechSynthesis.speak(u);
      return true;
    } catch (e) { return false; }
  }

  function zustand() {
    try { window.dispatchEvent(new CustomEvent('ptvorlesen:zustand', { detail: { laeuft: laeuft } })); } catch (e) {}
  }

  function stopp() {
    try { speechSynthesis.cancel(); } catch (e) {}
    laeuft = false; zustand();
  }

  /** Muss aus einem echten Tippen heraus aufgerufen werden, sonst bleibt iOS stumm. */
  function freischalten() { geste = true; }

  var LAUT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">' +
             '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/><path d="M19 6a8.5 8.5 0 0 1 0 12"/></svg>';

  /**
   * Hängt einen Knopf an ein Element. Der Knopf ist aus, solange keine
   * europäische Stimme da ist, und sagt dann auch warum.
   */
  function knopf(text, beschriftung) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'pt-ton';
    b.innerHTML = LAUT + '<span>' + (beschriftung || 'Vorlesen') + '</span>';
    function pruefen() {
      b.disabled = !bereit;
      b.title = bereit ? 'Mit der europäischen Stimme ' + stimme.name
                       : 'Auf diesem Gerät ist keine europäische Stimme installiert. '
                         + 'Eine brasilianische lese ich absichtlich nicht vor.';
    }
    pruefen();
    window.addEventListener('ptvorlesen:bereit', pruefen);
    window.addEventListener('ptvorlesen:zustand', function (e) {
      b.classList.toggle('laeuft', !!(e.detail && e.detail.laeuft));
    });
    b.addEventListener('click', function () {
      freischalten();
      if (laeuft) { stopp(); return; }
      sprich(typeof text === 'function' ? text() : text);
    });
    return b;
  }

  // Beim Wechsel in eine andere App oder bei Bildschirmsperre bricht die Ausgabe
  // ohnehin ab. Sauber beenden, damit beim Zurückkommen nichts hängt.
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') stopp();
  });
  window.addEventListener('pagehide', stopp);

  window.PTVorlesen = {
    sprich: sprich, stopp: stopp, knopf: knopf, optionen: optionen,
    freischalten: freischalten,
    status: function () { return { bereit: bereit, stimme: stimme ? stimme.name : null, laeuft: laeuft }; }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
