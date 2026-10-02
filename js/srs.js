/* =============================================================================
   srs.js — wann eine Aufgabe wieder drankommt, und welche heute
   =============================================================================

   Drei Knöpfe, so wie Moritz sie wollte:
       0 = nicht gut      1 = geht so      2 = sitzt

   Die Abstände wachsen in festen Stufen: 1, 3, 7, 16 Tage. Danach übernimmt ein
   Faktor je Aufgabe zwischen 1,5 und 2,8. Ein sauber gelerntes Wort sieht er
   also an Tag 1, 4, 11, 27, 64, 149, 344 — sieben Wiederholungen im ersten Jahr.

   Drei Entscheidungen, die wichtiger sind als die Formel:

   1. Die Zahl der fälligen Aufgaben wird NIE angezeigt. Wer nach zwei Wochen
      Pause "je 240 fällig" liest, macht die App zu und nie wieder auf.
   2. Nach einer Pause wird der Rückstand über bis zu 21 Tage verteilt, statt
      ihn an einem Tag abzuladen.
   3. Neue Aufgaben kommen nicht mit fester Rate, sondern füllen nur auf, was
      von der Sitzung übrig ist. Wer viel übt, bekommt mehr Neues. Wer wenig
      übt, ertrinkt nicht.

   Die Häufigkeit aus der Datendatei greift NIE in die Abstände ein. Sie
   entscheidet nur, in welcher Reihenfolge Neues eingeführt und was bei zu viel
   Stoff abgeschnitten wird. Sonst würde sie das Gedächtnismodell verfälschen.

   Der Tag beginnt um 4 Uhr morgens, nicht um Mitternacht. Wer um halb eins noch
   übt, ist für die App am selben Tag.
   ========================================================================== */

(function () {
  'use strict';

  var STAND_KEY = 'pt_vokabel_stand';     // { aufgabeId|richtung: [stufe, ease, iv, faellig, wdh, patzer] }
  var TAG_KEY   = 'pt_vokabel_tage';      // { '2026-09-29': anzahl }
  var OPT_KEY   = 'pt_vokabel_optionen';

  var LEITER   = [null, 1, 3, 7, 16];
  var E_START  = 2.3, E_MIN = 1.5, E_MAX = 2.8;
  var IV_MAX   = 365;
  var ZIEL     = 20;      // Aufgaben je Sitzung
  var NEU_MAX  = 15;      // neue Aufgaben je Tag, nur als Auffüllung
  // Warum 15 und nicht 3: Neues füllt immer nur auf, was von der Sitzung übrig
  // bleibt. An einem Tag ohne Fälliges wären drei Karten eine Sitzung von einer
  // halben Minute, und es hätte über vier Hundert Tage gedauert, bis er alles
  // einmal gesehen hat. Mit 15 ist der Bestand in gut drei Monaten eingeführt,
  // und weil Fälliges immer Vorrang hat, wächst die tägliche Last trotzdem nicht.
  var AUFHOLEN = 21;      // über so viele Tage wird ein Rückstand verteilt
  var TAGESBEGINN = 4;    // Stunde

  // ---------------------------------------------------------------- Kalender

  function heute(jetzt) {
    var d = new Date(jetzt || Date.now());
    if (d.getHours() < TAGESBEGINN) d.setDate(d.getDate() - 1);
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function plusTage(tag, n) {
    var t = tag.split('-');
    var d = new Date(+t[0], +t[1] - 1, +t[2]);
    d.setDate(d.getDate() + n);
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function tageZwischen(a, b) {
    var x = a.split('-'), y = b.split('-');
    var d1 = Date.UTC(+x[0], +x[1] - 1, +x[2]), d2 = Date.UTC(+y[0], +y[1] - 1, +y[2]);
    return Math.round((d2 - d1) / 86400000);
  }

  // ---------------------------------------------------------------- Speicher

  function lies(key, ersatz) {
    try { var r = localStorage.getItem(key); return r ? JSON.parse(r) : ersatz; }
    catch (e) { return ersatz; }
  }
  function schreib(key, wert) {
    try { localStorage.setItem(key, JSON.stringify(wert)); return true; }
    catch (e) {
      // Speicher voll oder privates Fenster. Die Sitzung läuft weiter, nur
      // ohne Sicherung auf diesem Gerät. Die Cloud-Warteschlange hat den Rest.
      if (window.PTTrainerWarnung) window.PTTrainerWarnung('speicher', e);
      return false;
    }
  }

  // Zustand kompakt: Array statt Objekt spart rund zwei Drittel Platz.
  function packe(s) { return [s.stufe, Math.round(s.ease * 100), s.iv, s.faellig, s.wdh, s.patzer, s.note]; }
  function entpacke(a) {
    return { stufe: a[0], ease: a[1] / 100, iv: a[2], faellig: a[3], wdh: a[4], patzer: a[5],
             note: a.length > 6 ? a[6] : null };
  }

  function alleStaende() {
    var roh = lies(STAND_KEY, {}), raus = {};
    for (var k in roh) if (Object.prototype.hasOwnProperty.call(roh, k)) raus[k] = entpacke(roh[k]);
    return raus;
  }
  function schluessel(aufgabeId, richtung) { return aufgabeId + '|' + richtung; }

  // ---------------------------------------------------------------- Formel

  function neuerStand() {
    return { stufe: 0, ease: E_START, iv: 0, faellig: null, wdh: 0, patzer: 0 };
  }

  /**
   * Der nächste Termin.
   * Der Kern ist ivWirksam: zu früh wiederholt wird nicht bestraft, aber ein
   * Glückstreffer nach dreihundert Tagen darf eine Aufgabe auch nicht gleich
   * auf zwei Jahre schieben. Überfälligkeit zählt als Beweis, aber gedeckelt.
   */
  function rechne(stand, note, tag) {
    var s = stand || neuerStand();
    var verstrichen = s.faellig && s.wdh ? Math.max(1, tageZwischen(plusTage(s.faellig, -s.iv), tag)) : 1;
    var ivAlt = Math.max(1, s.iv || 1);
    var ivWirksam = Math.min(Math.max(verstrichen, ivAlt), ivAlt * 2);

    var stufe = s.stufe, ease = s.ease, patzer = s.patzer, iv, nochmal = false;

    if (note === 0) {                       // nicht gut
      patzer += 1;
      ease = Math.max(E_MIN, ease - 0.20);
      stufe = Math.max(1, stufe - 2);
      iv = stufe <= 4 ? LEITER[stufe] : Math.max(3, Math.round(ivAlt * 0.4));
      nochmal = true;                       // kommt in dieser Sitzung noch einmal
    } else if (note === 1) {                // geht so
      ease = Math.max(E_MIN, ease - 0.05);
      stufe = Math.max(1, stufe);
      iv = Math.max(ivAlt + 1, Math.round(ivWirksam * 1.2));
      if (s.wdh === 0) { stufe = 1; iv = 1; nochmal = true; }
    } else {                                // sitzt
      ease = Math.min(E_MAX, ease + 0.08);
      stufe = stufe + 1;
      iv = stufe <= 4 ? Math.max(LEITER[stufe], Math.round(ivWirksam * 1.5))
                      : Math.round(ivWirksam * ease);
      if (s.wdh === 0) iv = 1;
    }

    // Streuung, damit nicht alles am selben Tag zurückkommt
    if (iv > 7) iv = Math.round(iv * (0.95 + Math.random() * 0.10));
    // Sicherheitsnetz: eine kaputte Rechnung darf nie eine Aufgabe verschlucken.
    if (!isFinite(iv) || isNaN(iv)) iv = 1;
    iv = Math.min(IV_MAX, Math.max(1, iv));

    return {
      stufe: stufe, ease: Math.round(ease * 1000) / 1000, iv: iv,
      faellig: plusTage(tag, iv), wdh: s.wdh + 1, patzer: patzer, note: note, nochmal: nochmal
    };
  }

  /**
   * Erinnerungswahrscheinlichkeit, grobe Schätzung nach der Vergessenskurve.
   * Wird nur gebraucht, um zu sortieren, welche fällige Aufgabe zuerst kommt.
   * Sie fließt NICHT in die Abstände ein.
   */
  function erinnerung(stand, tag) {
    if (!stand || !stand.faellig) return 0;
    var alter = stand.iv - tageZwischen(tag, stand.faellig);
    if (alter <= 0) return 1;
    return Math.exp(-alter / Math.max(1, stand.iv));
  }

  /**
   * Die drei Fächer, die Moritz sehen will.
   *
   * Seine eigene Bewertung entscheidet zuerst, der Abstand korrigiert nur nach
   * oben. Sonst landet am ersten Tag alles in "noch nicht", obwohl er zwanzigmal
   * "sitzt" gedrückt hat, und das liest sich wie eine Ohrfeige.
   * "Sitzt" wird erst vergeben, wenn er es auch über drei Wochen behalten hat.
   */
  function fach(stand) {
    if (!stand || !stand.wdh) return 'neu';
    if (stand.note === 0) return 'nicht gut';
    if (stand.note === 2 && stand.iv >= 21) return 'sitzt';
    if (stand.note == null) return stand.iv >= 21 ? 'sitzt' : stand.iv < 7 ? 'nicht gut' : 'geht so';
    return 'geht so';
  }

  // ---------------------------------------------------------------- Sitzung

  /**
   * Stellt die Aufgaben für eine Sitzung zusammen.
   *
   * Reihenfolge der Auswahl:
   *   1. überfällige und heute fällige Aufgaben, die dringendsten zuerst
   *      (dringend = wichtig mal wahrscheinlich vergessen)
   *   2. wenn noch Platz ist: neue Aufgaben in der Reihenfolge ihres Gewichts
   *
   * Bei einem Rückstand wird nicht alles auf einmal gezeigt. Der Rückstand
   * wird gedanklich auf bis zu 21 Tage verteilt, damit eine Pause nicht mit
   * einer Strafsitzung endet.
   */
  function sitzung(aufgaben, opt) {
    opt = opt || {};
    var tag = opt.tag || heute();
    var ziel = opt.ziel || optionen().ziel || ZIEL;
    var staende = alleStaende();
    var nurPaket = opt.paket && opt.paket !== 'alle' ? opt.paket : null;

    var faellig = [], neu = [];
    for (var i = 0; i < aufgaben.length; i++) {
      var a = aufgaben[i];
      if (nurPaket && a.paket !== nurPaket) continue;
      var richtungen = a.richtungen || ['pt_de'];
      for (var r = 0; r < richtungen.length; r++) {
        var ri = richtungen[r];
        var st = staende[schluessel(a.id, ri)];
        var eintrag = { aufgabe: a, richtung: ri, stand: st || null };
        if (!st || !st.wdh) {
          // Zweite Richtung erst freischalten, wenn die erste sitzt.
          if (r > 0) {
            var erste = staende[schluessel(a.id, richtungen[0])];
            if (!erste || erste.iv < 7) continue;
          }
          neu.push(eintrag);
        } else if (st.faellig <= tag) {
          eintrag.ueberfaellig = tageZwischen(st.faellig, tag);
          faellig.push(eintrag);
        }
      }
    }

    // Rückstand entzerren: alles, was älter als heute ist, wird über bis zu
    // 21 Tage gedacht. Pro Tag kommt also nur ein Bruchteil dran.
    var rueckstand = faellig.filter(function (e) { return e.ueberfaellig > 0; }).length;
    var anteil = rueckstand > ziel ? Math.max(ziel, Math.ceil(rueckstand / AUFHOLEN) + ziel) : ziel;

    faellig.sort(function (x, y) { return dringlichkeit(y, tag) - dringlichkeit(x, tag); });
    var liste = faellig.slice(0, Math.min(anteil, ziel));

    var heuteNeu = (lies(TAG_KEY, {})[tag] || 0);
    var platz = Math.max(0, ziel - liste.length);
    var neuMax = Math.min(platz, Math.max(0, NEU_MAX - heuteNeu));
    if (opt.nurNeu) neuMax = Math.min(platz, ziel);
    neu.sort(function (x, y) { return (x.aufgabe.platz || 0) - (y.aufgabe.platz || 0); });
    liste = liste.concat(neu.slice(0, neuMax));

    mische(liste);
    return liste;
  }

  function dringlichkeit(e, tag) {
    var w = e.aufgabe.W != null ? e.aufgabe.W : 0.5;
    return w * (1 - erinnerung(e.stand, tag));
  }

  function mische(l) {
    for (var i = l.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = l[i]; l[i] = l[j]; l[j] = t;
    }
  }

  // ---------------------------------------------------------------- Antworten

  /**
   * Eine Antwort verbuchen. Schreibt SOFORT, nicht erst am Ende der Sitzung:
   * lokal und in die Warteschlange für die Cloud. Wer die App mitten in der
   * Sitzung zumacht, verliert nichts.
   */
  function antwort(aufgabe, richtung, note, extra) {
    var tag = heute();
    var roh = lies(STAND_KEY, {});
    var k = schluessel(aufgabe.id, richtung);
    var alt = roh[k] ? entpacke(roh[k]) : null;
    var neuStand = rechne(alt, note, tag);

    roh[k] = packe(neuStand);
    schreib(STAND_KEY, roh);

    if (!alt || !alt.wdh) {
      var tage = lies(TAG_KEY, {});
      tage[tag] = (tage[tag] || 0) + 1;
      // Nur die letzten 120 Tage behalten, sonst wächst der Eintrag ewig.
      var schluessel2 = Object.keys(tage).sort();
      while (schluessel2.length > 120) delete tage[schluessel2.shift()];
      schreib(TAG_KEY, tage);
    }

    // Für den Leistungstest mitzählen, aber nur Antworten aus der normalen Übung.
    if (window.PTTest && !(extra && extra.quelle === 'test')) {
      try { PTTest.zaehle(tag); } catch (e) {}
    }

    if (window.PTVokabelSync) {
      window.PTVokabelSync.merke({
        aufgabe_id: aufgabe.id, pt: aufgabe.pt, de: aufgabe.de, paket: aufgabe.paket,
        richtung: richtung, note: note,
        antwort: extra && extra.antwort != null ? String(extra.antwort) : null,
        richtig: extra && extra.richtig != null ? !!extra.richtig : null,
        ms: extra && extra.ms ? Math.round(extra.ms) : null,
        wdh: neuStand.wdh, intervall: neuStand.iv, faktor: neuStand.ease,
        faellig: neuStand.faellig
      });
    }
    return neuStand;
  }

  // ---------------------------------------------------------------- Überblick

  function uebersicht(aufgaben) {
    var tag = heute(), staende = alleStaende();
    var z = { neu: 0, 'nicht gut': 0, 'geht so': 0, 'sitzt': 0, gesehen: 0, faellig: 0, gesamt: 0 };
    var jePaket = {};
    for (var i = 0; i < aufgaben.length; i++) {
      var a = aufgaben[i], rs = a.richtungen || ['pt_de'];
      for (var r = 0; r < rs.length; r++) {
        var st = staende[schluessel(a.id, rs[r])];
        var f = fach(st);
        z.gesamt++; z[f]++;
        if (st && st.wdh) { z.gesehen++; if (st.faellig <= tag) z.faellig++; }
        var p = jePaket[a.paket] || (jePaket[a.paket] = { gesamt: 0, gesehen: 0, sitzt: 0 });
        p.gesamt++;
        if (st && st.wdh) { p.gesehen++; if (f === 'sitzt') p.sitzt++; }
      }
    }
    var tage = lies(TAG_KEY, {});
    return { zahlen: z, jePaket: jePaket, heuteNeu: tage[tag] || 0, serie: serie(tage, tag), tag: tag };
  }

  function serie(tage, tag) {
    var n = 0, t = tag;
    if (!tage[t]) t = plusTage(t, -1);          // heute noch nichts gemacht: gestern zählt
    while (tage[t]) { n++; t = plusTage(t, -1); }
    return n;
  }

  function optionen(patch) {
    var o = lies(OPT_KEY, { ziel: ZIEL, paket: 'alle', tippen: true });
    if (patch) { for (var k in patch) o[k] = patch[k]; schreib(OPT_KEY, o); }
    return o;
  }

  /** Stand aus der Cloud übernehmen, wenn dort ein neuerer steht (zweites Gerät). */
  function uebernehme(zeilen) {
    var roh = lies(STAND_KEY, {}), geaendert = 0;
    for (var i = 0; i < zeilen.length; i++) {
      var z = zeilen[i];
      if (!z.aufgabe_id || z.intervall == null || !z.faellig) continue;
      var k = schluessel(z.aufgabe_id, z.richtung || 'pt_de');
      var fern = { stufe: 0, ease: z.faktor || E_START, iv: z.intervall,
                   faellig: String(z.faellig).slice(0, 10), wdh: z.wdh || 1, patzer: 0,
                   note: z.note != null ? z.note : null };
      var hier = roh[k] ? entpacke(roh[k]) : null;
      if (!hier || (fern.wdh > hier.wdh)) { roh[k] = packe(fern); geaendert++; }
    }
    if (geaendert) schreib(STAND_KEY, roh);
    return geaendert;
  }

  function zuruecksetzen() {
    try { localStorage.removeItem(STAND_KEY); localStorage.removeItem(TAG_KEY); } catch (e) {}
  }

  window.PTSrs = {
    sitzung: sitzung, antwort: antwort, uebersicht: uebersicht, optionen: optionen,
    fach: fach, rechne: rechne, heute: heute, plusTage: plusTage, tageZwischen: tageZwischen,
    staende: alleStaende, uebernehme: uebernehme, zuruecksetzen: zuruecksetzen,
    KONSTANTEN: { LEITER: LEITER, ZIEL: ZIEL, NEU_MAX: NEU_MAX, AUFHOLEN: AUFHOLEN }
  };
})();
