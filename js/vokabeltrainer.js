/* =============================================================================
   vokabeltrainer.js — der Ablauf einer Übungsrunde
   ============================================================================= */

(function () {
  'use strict';

  var DATEN = 'daten/trainer.json?v=20261002d';
  var CACHE = 'pt_trainer_daten';        // damit die Übung auch ohne Netz startet

  var el = {}, daten = null, liste = [], pos = 0, aktuell = null, gezeigt = false;
  var begonnen = 0, bilanz = { 0: 0, 1: 0, 2: 0 }, nachzuegler = [];
  var beantwortet = 0, obergrenze = 20, tonKnopf = null;

  function $(id) { return document.getElementById(id); }
  function zeig(e, ja) { if (e) e.classList.toggle('versteckt', !ja); }
  function text(e, t) { if (e) e.textContent = t == null ? '' : t; }

  document.addEventListener('DOMContentLoaded', start);

  function start() {
    ['start','uebung','schluss','startTitel','startText','kacheln','losKnopf','nurNeuKnopf',
     'paketWahl','zielWahl','startHinweis','karte','marke','frage','hilf','antwort','notiz',
     'eingabe','zeigenKnopf','tippfehlerKnopf','noten','tipp','zaehler','balken','titel',
     'schlussZahl','schlussTitel','schlussText','weiterKnopf','genugKnopf'].forEach(function (id) { el[id] = $(id); });

    el.losKnopf.addEventListener('click', function () {
      if (el.losKnopf.dataset.fortsetzen) {
        var r = offeneRunde();
        delete el.losKnopf.dataset.fortsetzen;
        if (r && rundeFortsetzen(r)) return;
      }
      starteRunde({});
    });
    el.nurNeuKnopf.addEventListener('click', function () { starteRunde({ nurNeu: true }); });
    el.zeigenKnopf.addEventListener('click', aufdecken);
    el.tippfehlerKnopf.addEventListener('click', tippfehler);
    el.weiterKnopf.addEventListener('click', function () { zurueckZumStart(); starteRunde({}); });
    el.genugKnopf.addEventListener('click', schliesse);
    el.zielWahl.addEventListener('change', function () {
      PTSrs.optionen({ ziel: parseInt(el.zielWahl.value, 10) });
    });
    el.paketWahl.addEventListener('change', function () {
      PTSrs.optionen({ paket: el.paketWahl.value }); zeigeStart();
    });
    Array.prototype.forEach.call(el.noten.querySelectorAll('.note'), function (b) {
      b.addEventListener('click', function () { bewerte(parseInt(b.dataset.note, 10)); });
    });
    el.eingabe.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); if (!gezeigt) aufdecken(); }
    });
    document.addEventListener('keydown', function (e) {
      if (el.uebung.classList.contains('versteckt')) return;
      if (document.activeElement === el.eingabe) return;
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); if (!gezeigt) aufdecken(); }
      if (gezeigt && e.key >= '1' && e.key <= '3') bewerte(parseInt(e.key, 10) - 1);
    });

    if (window.PTVorlesen) {
      tonKnopf = PTVorlesen.knopf(function () { return tonText(); }, 'Hören');
      tonKnopf.id = 'tonKnopf';
      el.karte.insertAdjacentElement('afterend', tonKnopf);
      zeig(tonKnopf, false);
    }

    window.PTTrainerWarnung = function (art) {
      if (art === 'speicher') hinweis('Dieses Gerät lässt gerade nichts speichern, etwa weil du im ' +
        'privaten Fenster bist. Du kannst üben, aber der Fortschritt wird nicht gemerkt.');
    };

    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') rundeSichern();
    });
    window.addEventListener('pagehide', rundeSichern);

    lade();
  }

  // ------------------------------------------------------------------ Laden

  function lade() {
    var ausCache = null;
    try { ausCache = JSON.parse(localStorage.getItem(CACHE) || 'null'); } catch (e) {}
    if (ausCache && ausCache.aufgaben) { daten = ausCache; zeigeStart(); }

    fetch(DATEN).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (d) {
      daten = d;
      try { localStorage.setItem(CACHE, JSON.stringify(d)); } catch (e) {}
      zeigeStart();
      if (window.PTVokabelSync) PTVokabelSync.hole().then(function (r) { if (r && r.uebernommen) zeigeStart(); });
    }).catch(function () {
      if (!daten) {
        text(el.startTitel, 'Die Aufgaben fehlen');
        text(el.startText, 'Die Datei mit den Aufgaben ließ sich nicht laden. Bist du online? ' +
          'Wenn du die Seite schon einmal offen hattest, versuch es gleich noch einmal.');
        zeig(el.losKnopf, false);
      }
    });
  }

  // ------------------------------------------------------------------ Start

  function zeigeStart() {
    if (!daten) return;
    var o = PTSrs.optionen();
    el.zielWahl.value = String(o.ziel || 20);

    if (!el.paketWahl.options.length) {
      var namen = { scharniere: 'Scharniere', konjugation: 'Konjugation und Zeiten', verben: 'Verben',
                    nomen: 'Substantive', adjektive: 'Adjektive', redewendungen: 'Redewendungen',
                    grammatik: 'Grammatik', fragen: 'Fragen', umgangssprache: 'Umgangssprache' };
      var opts = ['<option value="alle">Alles gemischt</option>'];
      (daten.pakete || []).forEach(function (p) {
        opts.push('<option value="' + p + '">' + (namen[p] || p) + '</option>');
      });
      el.paketWahl.innerHTML = opts.join('');
      el.paketWahl.value = o.paket || 'alle';
    }

    var u = PTSrs.uebersicht(daten.aufgaben);
    var z = u.zahlen;

    // Die Zahl der fälligen Aufgaben wird bewusst NICHT angezeigt. Wer nach
    // zwei Wochen Pause "je 240 fällig" liest, macht die App nie wieder auf.
    el.kacheln.innerHTML =
      kachel('gut', z['sitzt'], 'sitzt fest') +
      kachel('mittel', z['geht so'], 'auf dem Weg') +
      kachel('schwach', z['nicht gut'], 'hakt noch');

    if (z.gesehen === 0) {
      text(el.startTitel, 'Fang einfach an');
      text(el.startText, 'Es sind ' + daten.aufgaben.length + ' Aufgaben da, aber die siehst du nie alle auf einmal. ' +
        'Du bekommst zwanzig Stück, sortiert danach, was im Alltag am häufigsten vorkommt und wo es ' +
        'bei dir bisher hakt. Das dauert ungefähr fünf Minuten.');
      el.losKnopf.textContent = 'Die ersten zwanzig';
    } else {
      var s = u.serie;
      text(el.startTitel, s >= 2 ? s + ' Tage am Stück' : 'Weiter geht\'s');
      text(el.startText, z.gesehen + ' Karten hast du schon gesehen. ' +
        (z.faellig > 0 ? 'Ein paar davon sind heute wieder dran.' : 'Heute ist nichts Altes fällig, du bekommst Neues.'));
      el.losKnopf.textContent = 'Üben';
    }
    zeig(el.nurNeuKnopf, z.gesehen > 0);
    zeig(el.losKnopf, true);

    // Eine angefangene Runde wartet: der Knopf führt dorthin zurück, nicht in eine neue.
    var offen = offeneRunde();
    if (offen) {
      el.losKnopf.textContent = 'Weiter, wo du warst';
      el.losKnopf.dataset.fortsetzen = '1';
      text(el.startTitel, 'Du warst mittendrin');
      text(el.startText, 'Deine angefangene Runde ist noch da, ' + (offen.beantwortet || 0) +
        ' Karten hast du schon gemacht. Alles ist gespeichert, du kannst einfach weitermachen.');
    } else {
      delete el.losKnopf.dataset.fortsetzen;
    }

    var st = window.PTVokabelSync ? PTVokabelSync.status() : null;
    if (st && st.offen > 20 && st.fehler) {
      hinweis('Auf diesem Gerät warten ' + st.offen + ' Antworten darauf, in die Cloud zu kommen. ' +
        'Das liegt an der Datenbank, nicht an dir. Nichts geht verloren, es wird später nachgeholt.');
    } else { zeig(el.startHinweis, false); }
  }

  function kachel(art, n, label) {
    return '<div class="kachel ' + art + '"><b>' + n + '</b><span>' + label + '</span></div>';
  }
  function hinweis(t) { text(el.startHinweis, t); zeig(el.startHinweis, true); }

  // ------------------------------------------------------------------ Laufende Runde sichern

  /*
     Jede ANTWORT ist schon vorher sofort gespeichert. Hier geht es um die Runde
     selbst: welche Aufgaben, an welcher Stelle, wie viele schon beantwortet.
     Ohne das landet er nach einem kurzen App-Wechsel wieder auf dem Startbild
     und muss von vorne anfangen, obwohl nichts verloren war.

     Gespeichert wird bei jedem Weiterblättern und beim Verschwinden der Seite.
     Nach sechs Stunden verfällt der Stand, dann ist die Runde kalt.
  */
  var RUNDE_KEY = 'pt_vokabel_runde';
  var RUNDE_FRIST = 6 * 3600 * 1000;

  function rundeSichern() {
    if (!liste.length || !el.uebung || el.uebung.classList.contains('versteckt')) return;
    try {
      localStorage.setItem(RUNDE_KEY, JSON.stringify({
        zeit: Date.now(), pos: pos, beantwortet: beantwortet, obergrenze: obergrenze,
        bilanz: bilanz, paket: el.paketWahl.value,
        aufgaben: liste.map(function (e) { return [e.aufgabe.id, e.richtung]; }),
        nach: nachzuegler.map(function (e) { return [e.aufgabe.id, e.richtung]; })
      }));
    } catch (e) {}
  }

  function rundeVergessen() { try { localStorage.removeItem(RUNDE_KEY); } catch (e) {} }

  function offeneRunde() {
    var r;
    try { r = JSON.parse(localStorage.getItem(RUNDE_KEY) || 'null'); } catch (e) { return null; }
    if (!r || !r.aufgaben || !r.aufgaben.length) return null;
    if (Date.now() - r.zeit > RUNDE_FRIST) { rundeVergessen(); return null; }
    if (r.pos >= r.aufgaben.length && !(r.nach || []).length) { rundeVergessen(); return null; }
    return r;
  }

  function rundeFortsetzen(r) {
    var nachId = {};
    daten.aufgaben.forEach(function (a) { nachId[a.id] = a; });
    var staende = PTSrs.staende();
    function bauen(paar) {
      var a = nachId[paar[0]];
      if (!a) return null;
      return { aufgabe: a, richtung: paar[1], stand: staende[paar[0] + '|' + paar[1]] || null };
    }
    liste = r.aufgaben.map(bauen).filter(Boolean);
    nachzuegler = (r.nach || []).map(bauen).filter(Boolean);
    if (!liste.length) { rundeVergessen(); return false; }
    pos = Math.min(r.pos, liste.length);
    beantwortet = r.beantwortet || 0;
    obergrenze = r.obergrenze || 20;
    bilanz = r.bilanz || { 0: 0, 1: 0, 2: 0 };
    zeig(el.start, false); zeig(el.schluss, false); zeig(el.uebung, true);
    zeig(el.zaehler, true); zeig(el.balken, true);
    naechste();
    return true;
  }

  // ------------------------------------------------------------------ Runde

  function starteRunde(opt) {
    var o = PTSrs.optionen();
    liste = PTSrs.sitzung(daten.aufgaben, {
      ziel: parseInt(el.zielWahl.value, 10) || o.ziel,
      paket: el.paketWahl.value,
      nurNeu: !!opt.nurNeu
    });
    if (!liste.length) {
      text(el.startTitel, 'Für heute durch');
      text(el.startText, 'Hier ist gerade nichts fällig. Du kannst dir trotzdem Neues ansehen, ' +
        'oder ein anderes Paket wählen.');
      return;
    }
    rundeVergessen();
    pos = 0; bilanz = { 0: 0, 1: 0, 2: 0 }; nachzuegler = [];
    beantwortet = 0;
    obergrenze = Math.max(liste.length, parseInt(el.zielWahl.value, 10) || 20);
    zeig(el.start, false); zeig(el.schluss, false); zeig(el.uebung, true);
    zeig(el.zaehler, true); zeig(el.balken, true);
    text(el.titel, 'Vokabeln üben');
    naechste();
  }

  function zurueckZumStart() {
    zeig(el.uebung, false); zeig(el.schluss, false); zeig(el.start, true);
    zeig(el.zaehler, false); zeig(el.balken, false);
    zeigeStart();
  }

  function naechste() {
    // Wiedervorlagen zählen mit. Eine Runde endet hart bei der gewählten Zahl,
    // sonst wird aus zwanzig Aufgaben unbemerkt eine halbe Stunde.
    if (beantwortet >= obergrenze) return schliesse();
    if (pos >= liste.length) {
      if (nachzuegler.length) { liste = liste.concat(nachzuegler); nachzuegler = []; }
      else return schliesse();
    }
    aktuell = liste[pos];
    gezeigt = false;
    begonnen = Date.now();
    zeichne();
    rundeSichern();
  }

  function zeichne() {
    var a = aktuell.aufgabe, ri = aktuell.richtung;
    var neu = !aktuell.stand || !aktuell.stand.wdh;

    text(el.zaehler, beantwortet === 0 ? '' : beantwortet + (beantwortet === 1 ? ' Karte' : ' Karten'));
    el.balken.firstElementChild.style.width = Math.min(100, Math.round(beantwortet / 5 * 100)) + '%';

    zeig(el.antwort, false); zeig(el.notiz, false); zeig(el.noten, false);
    zeig(el.zeigenKnopf, true); zeig(el.tippfehlerKnopf, false);
    el.antwort.classList.remove('falsch');
    text(el.tipp, '');

    var marke = neu ? 'neu' : PTSrs.fach(aktuell.stand);
    if (a.paket === 'konjugation' && ri === 'tippen') marke = neu ? 'neue Form' : 'Form';

    if (ri === 'luecke') {
      // Grammatikübung: ein Satz mit einer Lücke. Hier ist ein Lückentext
      // erlaubt, weil getippt wird und es keine Rückrichtung gibt.
      text(el.marke, marke + ' · Lücke füllen');
      el.frage.className = 'frage klein';
      text(el.frage, a.satz.replace('___', '＿＿＿'));
      text(el.hilf, a.de); zeig(el.hilf, true);
      zeig(el.eingabe, true); el.eingabe.value = ''; el.eingabe.disabled = false;
      el.eingabe.placeholder = a.platzhalter || 'fehlendes Wort';
      setTimeout(function () { try { el.eingabe.focus(); } catch (e) {} }, 60);
      el.zeigenKnopf.textContent = 'Prüfen';
    } else if (ri === 'tippen') {
      text(el.marke, marke + ' · tippen');
      el.frage.className = 'frage klein';
      text(el.frage, a.verb + ' — ' + a.zeit_de);
      text(el.hilf, a.person_de + ' (' + a.person + ')'); zeig(el.hilf, true);
      zeig(el.eingabe, true); el.eingabe.value = ''; el.eingabe.disabled = false;
      el.eingabe.placeholder = 'Form eintippen';
      setTimeout(function () { try { el.eingabe.focus(); } catch (e) {} }, 60);
      el.zeigenKnopf.textContent = 'Prüfen';
    } else if (ri === 'reihe') {
      text(el.marke, marke + ' · alle fünf Formen');
      el.frage.className = 'frage klein';
      text(el.frage, a.verb + ' — ' + a.zeit_de);
      text(el.hilf, 'eu, tu, ele, nós, eles'); zeig(el.hilf, true);
      zeig(el.eingabe, false);
      el.zeigenKnopf.textContent = 'Formen zeigen';
    } else {
      var vorne = ri === 'pt_de' ? a.pt : a.de;
      text(el.marke, marke + ' · ' + (ri === 'pt_de' ? 'Portugiesisch → Deutsch' : 'Deutsch → Portugiesisch'));
      el.frage.className = 'frage' + (vorne.length > 34 ? ' klein' : '');
      text(el.frage, vorne);
      zeig(el.hilf, false);
      zeig(el.eingabe, false);
      el.zeigenKnopf.textContent = 'Antwort zeigen';
    }
    tonAktualisieren();
  }

  /**
   * Was vorgelesen wird. Immer die PORTUGIESISCHE Seite, nie die deutsche.
   * Vor dem Aufdecken wird nur gelesen, was die Lösung nicht verrät: bei einer
   * Karte Portugiesisch nach Deutsch ist die Vorderseite schon portugiesisch
   * und darf laut, bei getippten Formen und Lücken wäre es die Antwort.
   */
  function tonText() {
    if (!aktuell) return '';
    var a = aktuell.aufgabe, ri = aktuell.richtung;
    if (ri === 'luecke') return gezeigt ? a.satz.replace('___', a.pt) : '';
    if (ri === 'tippen') return gezeigt ? a.pt : '';
    if (ri === 'reihe') return gezeigt ? a.formen.join(', ') : '';
    if (ri === 'pt_de') return a.pt;                 // Vorderseite ist portugiesisch
    return gezeigt ? a.pt : '';                      // de_pt: erst nach dem Aufdecken
  }

  function tonAktualisieren() {
    if (!tonKnopf) return;
    zeig(tonKnopf, !!tonText());
  }

  // ------------------------------------------------------------------ Aufdecken

  function aufdecken() {
    if (gezeigt) return;
    gezeigt = true;
    var a = aktuell.aufgabe, ri = aktuell.richtung;

    if (ri === 'luecke') {
      var richtig = pruefeLuecke(el.eingabe.value, a);
      aktuell.urteil = { richtig: richtig, art: richtig ? 'exakt' : 'falsch' };
      el.eingabe.disabled = true;
      text(el.antwort, a.satz.replace('___', a.pt));
      el.antwort.classList.toggle('falsch', !richtig);
      zeig(el.antwort, true); zeig(el.noten, true);
      markiereVorschlag(richtig ? 2 : 0);
      if (!richtig && el.eingabe.value.trim()) text(el.tipp, 'Du hattest ' + el.eingabe.value.trim() + ' getippt, richtig ist ' + a.pt + '.');
    } else if (ri === 'tippen') {
      var urteil = pruefeForm(el.eingabe.value, a);
      aktuell.urteil = urteil;
      el.eingabe.disabled = true;
      text(el.antwort, a.pt);
      el.antwort.classList.toggle('falsch', !urteil.richtig);
      zeig(el.antwort, true);
      if (urteil.art === 'akzent') text(el.tipp, 'Richtig. Mit Akzent geschrieben heißt es ' + a.pt + '.');
      else if (urteil.art === 'nachbar') text(el.tipp, 'Das ist eine echte Form von ' + a.verb + ', aber ' + urteil.was + '.');
      else if (urteil.art === 'tippfehler') zeig(el.tippfehlerKnopf, true);
      else if (!urteil.richtig && el.eingabe.value.trim()) text(el.tipp, 'Du hattest ' + el.eingabe.value.trim() + ' getippt.');
      // Bei getippten Formen entscheidet die Eingabe, nicht das Gefühl.
      if (urteil.richtig) { zeig(el.noten, true); markiereVorschlag(2); }
      else { zeig(el.noten, true); markiereVorschlag(0); }
    } else if (ri === 'reihe') {
      text(el.antwort, a.formen.join(', '));
      zeig(el.antwort, true); zeig(el.noten, true);
    } else {
      text(el.antwort, ri === 'pt_de' ? a.de : a.pt);
      zeig(el.antwort, true); zeig(el.noten, true);
    }

    if (a.notiz) { text(el.notiz, a.notiz); zeig(el.notiz, true); }
    zeig(el.zeigenKnopf, false);
    tonAktualisieren();
    // Nach dem Aufdecken von selbst vorlesen, aber nur wenn er das eingestellt
    // hat und schon einmal auf den Knopf gedrückt hat (iOS verlangt das).
    if (window.PTVorlesen && PTVorlesen.optionen().automatisch) {
      PTVorlesen.sprich(tonText(), { nurNachGeste: true });
    }
  }

  function markiereVorschlag(note) {
    Array.prototype.forEach.call(el.noten.querySelectorAll('.note'), function (b) {
      b.style.opacity = (parseInt(b.dataset.note, 10) === note) ? '1' : '0.55';
    });
  }

  function tippfehler() {
    // Zählt nicht als Fehler, kommt aber heute noch einmal.
    zeig(el.tippfehlerKnopf, false);
    text(el.tipp, 'Gut, das kommt gleich noch einmal.');
    nachzuegler.push({ aufgabe: aktuell.aufgabe, richtung: aktuell.richtung, stand: aktuell.stand });
    pos++;
    naechste();
  }

  // ------------------------------------------------------------------ Bewerten

  function bewerte(note) {
    if (!gezeigt) return;
    var a = aktuell.aufgabe;
    var extra = { ms: Date.now() - begonnen };
    if (aktuell.richtung === 'tippen' || aktuell.richtung === 'luecke') {
      extra.antwort = el.eingabe.value.trim();
      extra.richtig = !!(aktuell.urteil && aktuell.urteil.richtig);
    }
    var neuStand = PTSrs.antwort(a, aktuell.richtung, note, extra);
    bilanz[note]++;
    beantwortet++;

    if (neuStand.nochmal) {
      nachzuegler.push({ aufgabe: a, richtung: aktuell.richtung, stand: neuStand });
    }
    pos++;
    naechste();
  }

  // ------------------------------------------------------------------ Bewertung getippter Formen

  /**
   * Streng, aber nicht kleinlich.
   *
   * Groß- und Kleinschreibung und Satzzeichen am Rand zählen nie.
   * Ein fehlender Akzent wird NUR dann verziehen, wenn keine andere Form
   * desselben Verbs genauso aussieht. Damit geht "estavamos" für "estávamos"
   * durch, aber "falamos" für "falámos" nicht, denn falamos ist die Gegenwart.
   *
   * Was eine echte Nachbarform ist, gilt als falsch und wird benannt. Genau
   * hier lag der alte Fehler: eine Ähnlichkeitstoleranz hatte "comem" als
   * "comeram" durchgewinkt und das Ergebnis geschönt. Das passiert nicht mehr.
   */
  function pruefeForm(eingabe, a) {
    var u = norm(eingabe), z = norm(a.pt);
    if (!u) return { richtig: false, art: 'leer' };
    if (u === z) return { richtig: true, art: 'exakt' };

    var tabelle = (daten.formtabellen && daten.formtabellen[a.verb]) || a.geschwister || [];
    var ohneAkzent = z ? entakzent(z) : '';

    if (entakzent(u) === ohneAkzent) {
      var gleiche = tabelle.filter(function (f) { return entakzent(norm(f)) === ohneAkzent; });
      if (gleiche.length <= 1) return { richtig: true, art: 'akzent' };
      return { richtig: false, art: 'nachbar', was: 'hier fehlt der Akzent, und ohne ihn ist es eine andere Form' };
    }

    for (var i = 0; i < tabelle.length; i++) {
      if (norm(tabelle[i]) === u) {
        return { richtig: false, art: 'nachbar', was: 'nicht die gefragte' };
      }
    }
    // Nur wenn die Eingabe in KEINER Formtabelle vorkommt, darf sie als
    // Tippfehler gelten. "comem" bekommt diesen Knopf deshalb nie.
    if (abstand(entakzent(u), ohneAkzent) === 1 && !irgendeineForm(u)) {
      return { richtig: false, art: 'tippfehler' };
    }
    return { richtig: false, art: 'falsch' };
  }

  /**
   * Lückenaufgabe prüfen. Mehrere richtige Lösungen sind erlaubt, sie stehen
   * in a.auch. Akzente müssen stimmen, Groß- und Kleinschreibung nicht,
   * außer die Lücke steht am Satzanfang und es geht gerade um den Artikel.
   */
  function pruefeLuecke(eingabe, a) {
    var u = norm(eingabe);
    if (!u) return false;
    var richtig = [a.pt].concat(a.auch || []);
    for (var i = 0; i < richtig.length; i++) if (norm(richtig[i]) === u) return true;
    return false;
  }

  function irgendeineForm(u) {
    var t = daten.formtabellen || {};
    for (var v in t) {
      for (var i = 0; i < t[v].length; i++) if (norm(t[v][i]) === u) return true;
    }
    return false;
  }

  function norm(s) {
    return String(s == null ? '' : s).normalize('NFC').trim().toLowerCase()
      .replace(/\s+/g, ' ').replace(/^[.,!?;:"'¿¡]+|[.,!?;:"']+$/g, '');
  }
  function entakzent(s) {
    return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  function abstand(a, b) {
    if (Math.abs(a.length - b.length) > 1) return 2;
    var v = [], i, j;
    for (i = 0; i <= b.length; i++) v[i] = i;
    for (i = 1; i <= a.length; i++) {
      var vor = v[0]; v[0] = i;
      for (j = 1; j <= b.length; j++) {
        var t = v[j];
        v[j] = Math.min(v[j] + 1, v[j - 1] + 1, vor + (a[i - 1] === b[j - 1] ? 0 : 1));
        vor = t;
      }
    }
    return v[b.length];
  }

  // ------------------------------------------------------------------ Schluss

  function schliesse() {
    rundeVergessen();
    zeig(el.uebung, false); zeig(el.schluss, true);
    zeig(el.zaehler, false); zeig(el.balken, false);
    var gesamt = bilanz[0] + bilanz[1] + bilanz[2];
    text(el.schlussZahl, gesamt);
    text(el.schlussTitel, gesamt === 1 ? 'Eine Karte gemacht' : gesamt + ' Karten gemacht');

    var satz;
    if (gesamt < 5) satz = 'Auch das zählt. Jede einzelne Karte ist gespeichert, und die App weiß jetzt mehr über dich als vorher.';
    else if (bilanz[2] >= gesamt * 0.7) satz = 'Das meiste saß auf Anhieb. Was du sicher konntest, siehst du jetzt länger nicht wieder.';
    else if (bilanz[0] >= gesamt * 0.5) satz = 'Vieles hakte noch. Das ist beim ersten Mal normal, und genau das kommt bald wieder.';
    else satz = 'Solide Runde. Was wackelte, legt die App in ein paar Tagen noch einmal vor.';
    text(el.schlussText, satz);

    if (window.PTVokabelSync) PTVokabelSync.sende();
    if (window.PTProgress && gesamt >= 5) {
      // Damit die Fortschritt-Seite und ich es sehen, ohne die Vokabel-Tabelle zu kennen.
      try {
        PTProgress.save({
          exerciseId: 'vokabeltrainer', exerciseName: 'Vokabeltrainer', topic: 'vokabeln',
          sections: [{ name: 'Runde', score: bilanz[2] + bilanz[1], total: gesamt, wrong: [] }]
        });
      } catch (e) {}
    }
  }
})();
