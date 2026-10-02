/* =============================================================================
   leistungstest.js — messen statt behaupten
   =============================================================================

   DAS PROBLEM, DAS DIESE DATEI LÖST:
   Die drei Fächer im Trainer beruhen auf Moritz' Selbsteinschätzung. Er drückt
   selbst "sitzt". Ob er es wirklich kann, misst niemand. Genau das ändert der
   Leistungstest.

   Deshalb gelten im Test andere Regeln als in der Übung:
     - Es wird nur GETIPPT. Wiedererkennen beweist zu wenig.
     - Portugiesisch nach Deutsch kommt NIE vor. Das ist Wiedererkennen.
     - Keine Selbstbewertung. Richtig oder falsch entscheidet der Abgleich.
     - Keine Lösung und keine Notiz während des Tests. Erst am Ende.

   Der Test ist keine eigene Seite, die er aufsuchen müsste, sondern eine Runde,
   die an die Stelle einer normalen tritt. Wer eine App kaum benutzt, geht nicht
   freiwillig in eine Prüfung.

   WANN ER KOMMT: nach 120 bewerteten Antworten, frühestens zehn Tage nach dem
   letzten. Stapeln sich viele unbelegte "sitzt" (über 80), reichen 60 Antworten,
   denn dann gibt es mehr zu überprüfen. Nicht am ersten Tag nach einer Pause,
   nicht ohne zwölf Aufgaben Aufwärmen, und nach einem Abbruch drei Tage Ruhe.
   ========================================================================== */

(function () {
  'use strict';

  var TEST_KEY = 'pt_leistungstest';

  var MENGE_NORMAL = 120;     // bewertete Antworten bis zum nächsten Test
  var MENGE_VIEL   = 60;      // wenn sich unbelegte Behauptungen stapeln
  var BEHAUPT_GRENZE = 80;
  var MIN_TAGE = 10;
  var AUFWAERMEN = 12;        // Aufgaben an diesem Tag, bevor der Test kommt
  var RUECKKEHR_TAGE = 5;     // nach längerer Pause erst wieder ankommen lassen
  var SCHONZEIT = 3;          // nach einem Abbruch

  var SCHICHTEN = [
    { name: 'behauptung',  n: 8, titel: 'Was du für sicher hältst' },
    { name: 'dauerfehler', n: 6, titel: 'Deine beiden Dauerfehler' },
    { name: 'formen',      n: 6, titel: 'Verbformen' },
    { name: 'wortschatz',  n: 4, titel: 'Wortschatz' }
  ];

  function lies(k, e) { try { var r = localStorage.getItem(k); return r ? JSON.parse(r) : e; } catch (x) { return e; } }
  function schreib(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (x) { return false; } }
  function stand(patch) {
    var m = lies(TEST_KEY, {});
    if (patch) { for (var k in patch) m[k] = patch[k]; schreib(TEST_KEY, m); }
    return m;
  }

  /** Zählt jede bewertete Antwort aus der normalen Übung. Wird von srs.js gerufen. */
  function zaehle(tag) {
    var m = lies(TEST_KEY, {});
    if (m.tag !== tag) { m.zuletztAktiv = m.tag || null; m.tag = tag; m.heute = 0; }
    m.heute = (m.heute || 0) + 1;
    m.seit = (m.seit || 0) + 1;
    schreib(TEST_KEY, m);
  }

  function behauptungen(aufgaben) {
    var st = PTSrs.staende(), n = 0;
    for (var k in st) if (PTSrs.fach(st[k]) === 'sitzt') n++;
    return n;
  }

  /** Ist heute ein Test dran? Gibt immer auch den Grund zurück, damit man es erklären kann. */
  function faellig(aufgaben) {
    var tag = PTSrs.heute(), m = lies(TEST_KEY, {});
    if (m.laufend) return { ja: true, grund: 'fortsetzen' };
    if (m.tag !== tag || (m.heute || 0) < AUFWAERMEN) return { ja: false, grund: 'noch nicht aufgewärmt' };
    if (m.zuletztAktiv && PTSrs.tageZwischen(m.zuletztAktiv, tag) > RUECKKEHR_TAGE)
      return { ja: false, grund: 'gerade erst zurück' };
    if (m.letzterAbbruch && PTSrs.tageZwischen(m.letzterAbbruch, tag) < SCHONZEIT)
      return { ja: false, grund: 'Schonzeit nach Abbruch' };
    var her = m.letzterTest ? PTSrs.tageZwischen(m.letzterTest, tag) : 9999;
    if (her < MIN_TAGE) return { ja: false, grund: 'zu früh' };
    var grenze = behauptungen(aufgaben) > BEHAUPT_GRENZE ? MENGE_VIEL : MENGE_NORMAL;
    if ((m.seit || 0) >= grenze) return { ja: true, grund: 'genug geübt seitdem' };
    if (her >= 35 && (m.seit || 0) >= 40) return { ja: true, grund: 'lange her' };
    return { ja: false, grund: 'noch zu wenig geübt', fehlen: grenze - (m.seit || 0) };
  }

  /**
   * Die vier Schichten. Zufall allein würde seine zwei Dauerfehler in den
   * meisten Tests gar nicht treffen, deshalb wird geschichtet gezogen.
   */
  function becken(aufgaben) {
    var st = PTSrs.staende();
    var b = { behauptung: [], dauerfehler: [], formen: [], wortschatz: [] };
    aufgaben.forEach(function (a) {
      (a.richtungen || []).forEach(function (ri) {
        // Nur was objektiv prüfbar ist. pt_de ist Wiedererkennen und fällt raus.
        if (ri !== 'tippen' && ri !== 'luecke' && ri !== 'de_pt') return;
        var s = st[a.id + '|' + ri] || null;
        var e = { aufgabe: a, richtung: ri, stand: s, iv: s ? s.iv : 0 };
        if (ri === 'luecke') { b.dauerfehler.push(e); return; }
        if (ri === 'tippen') { if (s && s.wdh) b.formen.push(e); return; }
        var gegen = st[a.id + '|pt_de'] || null;
        if (s && PTSrs.fach(s) === 'sitzt') b.behauptung.push(e);
        else if (!s && gegen && PTSrs.fach(gegen) === 'sitzt') { e.iv = gegen.iv; b.behauptung.push(e); }
        else if (s && s.wdh) b.wortschatz.push(e);
      });
    });
    return b;
  }

  function mische(l) {
    for (var i = l.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)); var t = l[i]; l[i] = l[j]; l[j] = t;
    }
    return l;
  }

  /** Stellt die 24 Aufgaben zusammen. Fehlt in einer Schicht etwas, füllen die anderen auf. */
  function zusammenstellen(aufgaben) {
    var b = becken(aufgaben), raus = [], genommen = {};
    b.behauptung.sort(function (x, y) { return y.iv - x.iv; });   // das am längsten Behauptete zuerst
    mische(b.dauerfehler); mische(b.formen); mische(b.wortschatz);

    SCHICHTEN.forEach(function (s) {
      var liste = b[s.name] || [];
      for (var i = 0, n = 0; i < liste.length && n < s.n; i++) {
        var k = liste[i].aufgabe.id + '|' + liste[i].richtung;
        if (genommen[k]) continue;
        genommen[k] = 1; liste[i].schicht = s.name; raus.push(liste[i]); n++;
      }
    });
    // Auffüllen auf 24, falls eine Schicht zu dünn war
    var ziel = SCHICHTEN.reduce(function (s, x) { return s + x.n; }, 0);
    ['dauerfehler', 'formen', 'wortschatz', 'behauptung'].forEach(function (name) {
      (b[name] || []).forEach(function (e) {
        if (raus.length >= ziel) return;
        var k = e.aufgabe.id + '|' + e.richtung;
        if (genommen[k]) return;
        genommen[k] = 1; e.schicht = name; raus.push(e);
      });
    });
    return mische(raus);
  }

  function beginnen(aufgaben) {
    var posten = zusammenstellen(aufgaben);
    if (posten.length < 10) return null;    // zu wenig Material, kein Test
    stand({ laufend: { pos: 0, begonnen: Date.now(),
                       posten: posten.map(function (e) { return [e.aufgabe.id, e.richtung, e.schicht]; }),
                       antworten: [] } });
    return posten;
  }

  function antwortMerken(index, richtig, getippt) {
    var m = lies(TEST_KEY, {});
    if (!m.laufend) return;
    m.laufend.antworten[index] = { r: !!richtig, a: String(getippt || '').slice(0, 60) };
    m.laufend.pos = index + 1;
    schreib(TEST_KEY, m);
  }

  function abbrechen() {
    var m = lies(TEST_KEY, {});
    m.letzterAbbruch = PTSrs.heute(); m.laufend = null;
    schreib(TEST_KEY, m);
  }

  /** Test abschließen. Gibt das Ergebnis je Schicht zurück. */
  function abschliessen(posten) {
    var m = lies(TEST_KEY, {});
    var antworten = (m.laufend && m.laufend.antworten) || [];
    var je = {}, gesamt = { n: 0, r: 0 };
    posten.forEach(function (e, i) {
      var a = antworten[i];
      if (!a) return;
      var s = e.schicht || 'sonstige';
      if (!je[s]) je[s] = { n: 0, r: 0 };
      je[s].n++; gesamt.n++;
      if (a.r) { je[s].r++; gesamt.r++; }
    });
    var eintrag = { tag: PTSrs.heute(), n: gesamt.n, r: gesamt.r, je: je };
    var serie = (m.serie || []).concat([eintrag]).slice(-12);
    stand({ laufend: null, letzterTest: eintrag.tag, seit: 0, serie: serie, letzterAbbruch: null });
    return eintrag;
  }

  /* ==========================================================================
     Wie gut kann er etwas wirklich?
     ==========================================================================

     Geschätzt wird: Wie wahrscheinlich löst er eine Aufgabe dieses Themas
     richtig, wenn er sie unangekündigt selbst produzieren muss.

     Ausgegeben wird NIE eine einzelne Zahl, sondern immer ein Bereich. Solange
     er wenig geübt hat, ist die Breite des Bereichs die eigentliche Aussage.
     Nach drei Antworten darf keine App behaupten, ein Thema sitze zu neunzig
     Prozent.

     Nicht jede Antwort wiegt gleich schwer:
        getippt oder in die Lücke gesetzt   1,00   er hat es produziert
        selbst bewertet (Deutsch nach PT)   0,50   seine eigene Einschätzung
        wiedererkannt (PT nach Deutsch)     0,15   beweist am wenigsten
     Antworten aus einem Leistungstest zählen doppelt, weil sie unangekündigt
     und ohne Hilfe zustande kamen.
  ========================================================================== */

  var GEWICHT = { tippen: 1.0, luecke: 1.0, de_pt: 0.5, pt_de: 0.15, reihe: 0.5 };

  function themaVon(a) {
    var raus = [];
    (a.fehler || []).forEach(function (f) {
      if (f === 'artikel-possessiv') raus.push('artikel-possessiv');
      else if (f === 'pronomen-hinten' || f === 'pronomen-vorn') raus.push('pronomen-stellung');
      else if (f === 'zeitenwahl') raus.push('zeitenwahl');
      else if (f === 'konjunktiv') raus.push('konjunktiv');
    });
    if (a.zeit === 'perf') raus.push('formen-perfeito');
    else if (a.zeit === 'imp') raus.push('formen-imperfeito');
    else if (a.zeit === 'cond') raus.push('formen-konditional');
    else if (a.zeit === 'pres') raus.push('formen-praesens');
    if (a.paket === 'scharniere') raus.push('scharniere');
    return raus;
  }

  var NAMEN = {
    'artikel-possessiv': 'Der Artikel vor mein, dein und sein',
    'pronomen-stellung': 'Wo das Pronomen hinkommt',
    'zeitenwahl': 'Gegenwart oder Vergangenheit',
    'formen-perfeito': 'Die Formen der Vergangenheit',
    'formen-imperfeito': 'Die Formen der Erzählvergangenheit',
    'formen-konditional': 'Die würde-Formen',
    'formen-praesens': 'Die Formen der Gegenwart',
    'konjunktiv': 'Die Form nach embora und mesmo que',
    'scharniere': 'Die kleinen Gesprächswörter'
  };

  /**
   * Beta-Schätzung je Thema. a und b starten bei 1, das ist die ehrliche
   * Ausgangslage: alles zwischen null und hundert Prozent ist denkbar.
   */
  function koennen(aufgaben) {
    var st = PTSrs.staende(), roh = {};
    aufgaben.forEach(function (a) {
      var themen = themaVon(a);
      if (!themen.length) return;
      (a.richtungen || []).forEach(function (ri) {
        var s = st[a.id + '|' + ri];
        if (!s || !s.wdh) return;
        var g = GEWICHT[ri] || 0.5;
        // note 2 zählt als gelungen, note 0 als misslungen, note 1 als halb
        var gut = s.note === 2 ? 1 : s.note === 1 ? 0.5 : 0;
        themen.forEach(function (t) {
          var r = roh[t] || (roh[t] = { a: 1, b: 1, gesehen: 0, hart: 0 });
          r.a += g * gut; r.b += g * (1 - gut);
          r.gesehen++;
          if (ri === 'tippen' || ri === 'luecke') r.hart++;
        });
      });
    });

    var raus = [];
    for (var t in roh) {
      var r = roh[t];
      var p = r.a / (r.a + r.b);
      // Streuung der Beta-Verteilung, daraus ein Bereich von rund 80 Prozent
      var v = Math.sqrt(p * (1 - p) / (r.a + r.b + 1));
      raus.push({
        thema: t, name: NAMEN[t] || t,
        wert: p, unten: Math.max(0, p - 1.28 * v), oben: Math.min(1, p + 1.28 * v),
        gesehen: r.gesehen, hart: r.hart,
        belegt: r.hart >= 8,         // erst ab acht produzierten Antworten reden wir von Messung
        satz: satzFuer(t, p, r)
      });
    }
    raus.sort(function (x, y) { return x.wert - y.wert; });
    return raus;
  }

  /** In ganzen Sätzen, ohne nackte Zahlen. So hat Moritz es sich ausdrücklich gewünscht. */
  function satzFuer(t, p, r) {
    var name = NAMEN[t] || t;
    if (r.hart < 8) {
      return 'Zu ' + name + ' hast du bisher zu wenig selbst getippt, als dass ich etwas sagen könnte. '
           + 'Das ändert sich von selbst, wenn du weiter übst.';
    }
    if (p >= 0.85) return name + ' sitzt. Das hast du mehrfach selbst produziert, nicht nur wiedererkannt.';
    if (p >= 0.65) return name + ' läuft meistens, aber noch nicht zuverlässig.';
    if (p >= 0.4)  return name + ' ist etwa die Hälfte der Zeit richtig. Hier lohnt sich Übung am meisten.';
    return name + ' geht noch oft daneben. Das ist gerade deine größte Baustelle.';
  }

  window.PTTest = {
    faellig: faellig, beginnen: beginnen, antwortMerken: antwortMerken,
    abbrechen: abbrechen, abschliessen: abschliessen, zaehle: zaehle,
    koennen: koennen, stand: function () { return lies(TEST_KEY, {}); },
    SCHICHTEN: SCHICHTEN, NAMEN: NAMEN
  };
})();
