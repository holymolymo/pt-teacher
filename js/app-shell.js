/**
 * App-Shell für alle Seiten. Einbinden am Ende von <body>, NACH js/progress.js:
 *   <script src="js/progress.js"></script>
 *   <script src="js/app-shell.js"></script>
 *
 * Macht auf jeder Seite:
 *   - Service Worker (nur https, damit die lokale Vorschau nie veraltete Dateien cached)
 *   - Bottom-Nav (Home / Lernen / Vokabeln / Fortschritt), aktive Seite automatisch
 *   - Nav ausblenden, solange die Tastatur offen ist
 *   - Auf Übungsseiten (#results vorhanden): Ergebnis in PTProgress speichern +
 *     einheitlicher Abschluss-Block "Weiter / Nochmal / Home"
 *
 * Stellt window.PTApp bereit: Katalog aller Übungen + Smart-Pick + Streak.
 */
(function () {
  'use strict';

  // ======================= KATALOG (einzige Wahrheit über alle Übungen) =======================
  function pad(n) { return String(n).padStart(2, '0'); }
  function lesson(num, file, title, meta, topic) {
    return { id: 'lektion-' + pad(num), group: 'lektion', num: num, file: file,
      label: 'L' + num, title: title, meta: meta, topic: topic, doneKey: 'pt-lektion-' + pad(num) };
  }
  function tiefen(num, file, title, meta, topic) {
    return { id: 'tiefen-' + pad(num), group: 'tiefen', num: num, file: file,
      label: 'T' + num, title: title, meta: meta, topic: topic, doneKey: 'pt-tiefen-' + pad(num) };
  }
  function wdh(num, file, title, meta) {
    return { id: 'wiederholung-' + pad(num), group: 'wiederholung', num: num, file: file,
      label: 'W' + num, title: title, meta: meta, topic: 'wiederholung', doneKey: 'pt-wiederholung-' + pad(num) };
  }

  const LESSONS = [
    lesson(1,  'lektion-01-chamar-se.html',                'Chamar-se – sich vorstellen',        '8 Aufgaben',  'reflexive'),
    lesson(2,  'lektion-02-ser-artigos.html',              'Ser + Artigos',                      '13 Aufgaben', 'ser-artigos'),
    lesson(3,  'lektion-03-nacionalidades-profissoes.html','Nacionalidades + Profissões',        '18 Aufgaben', 'nacionalidades'),
    lesson(4,  'lektion-04-ter-numeros.html',              'Ter + Zahlen',                       '15 Aufgaben', 'ter-zahlen'),
    lesson(5,  'lektion-05-ar-verben.html',                'Regelmäßige -ar Verben',             '15 Aufgaben', 'presente'),
    lesson(6,  'lektion-06-kontraktionen.html',            'Kontraktionen (no, na, do, da)',     '18 Aufgaben', 'praepositionen'),
    lesson(7,  'lektion-07-fragewoerter.html',             'Fragewörter',                        '16 Aufgaben', 'fragew'),
    lesson(8,  'lektion-08-estar-vs-ser.html',             'Ser vs. Estar',                      '16 Aufgaben', 'ser-estar'),
    lesson(9,  'lektion-09-preterito-perfeito.html',       'Vergangenheit (Pretérito Perfeito) – Grundlagen', '18 Aufgaben', 'perfeito'),
    lesson(10, 'lektion-10-mega-session.html',             'Große Mischübung',                   '45 Aufgaben aus allen Themen', 'presente-unregel'),
    lesson(11, 'lektion-11-preterito-imperfeito.html',     'Erzählvergangenheit (Imperfeito)',   '23 Aufgaben', 'imperfeito'),
    lesson(12, 'lektion-12-possessivpronomen.html',        'Mein, dein, sein: Possessivpronomen','20 Aufgaben', 'possessiv'),
    lesson(13, 'lektion-13-ir-infinitiv.html',             'Zukunft mit ir + Verb (vou comer)',  '16 Aufgaben', 'ir-inf'),
    lesson(14, 'lektion-14-estar-a-uhrzeit.html',          'Gerade dabei sein (estar a) & Uhrzeit', '18 Aufgaben', 'estar-a'),
    lesson(15, 'lektion-15-ir-verben.html',                'Verben auf -ir',                     '28 Aufgaben', 'presente'),
    lesson(16, 'lektion-16-objektpronomen.html',           'Mich, dich, ihn: Objektpronomen',    '16 Aufgaben', 'objektpronomen'),
    lesson(17, 'lektion-17-demonstrativ.html',             'Dieser, jener: Demonstrativpronomen','19 Aufgaben', 'demonstrativ'),
    lesson(18, 'lektion-18-komparativ-zeit.html',          'Vergleichen & Zeitangaben',          '19 Aufgaben', 'komparativ'),
    lesson(19, 'lektion-19-reflexive-stellung.html',       'Reflexive Verben: wohin gehört me, te, se?', '18 Aufgaben', 'reflexive'),
    lesson(20, 'lektion-20-konditional.html',              'Würde-Form (Konditional)',           '16 Aufgaben', 'konditional'),
    lesson(21, 'lektion-21-por-vs-para.html',              'Por oder para?',                     '22 Aufgaben', 'praepositionen')
  ];
  const TIEFEN = [
    tiefen(1, 'tiefenuebung-01-unregelmaessige.html',    'Unregelmäßige Verben in der Ich-Form',      '45 kurze Aufgaben · faço, sei, digo', 'presente-unregel'),
    tiefen(2, 'tiefenuebung-02-preterito-perfeito.html', 'Vergangenheit vertiefen (Pretérito Perfeito)', '48 kurze Aufgaben · fui, fiz, tive', 'perfeito'),
    tiefen(3, 'tiefenuebung-03-imperfeito.html',         'Erzählvergangenheit vertiefen (Imperfeito)',  '30 kurze Aufgaben · era, tinha, vinha', 'imperfeito')
  ];
  const WIEDERHOLUNGEN = [
    wdh(1, 'wiederholung-01.html', 'Wiederholung 1', 'Lektion 1–3 · 20 Aufgaben'),
    wdh(2, 'wiederholung-02.html', 'Wiederholung 2', 'Lektion 1–5 · 22 Aufgaben'),
    wdh(3, 'wiederholung-03.html', 'Wiederholung 3', 'Lektion 1–6 · 20 Aufgaben'),
    wdh(4, 'wiederholung-04.html', 'Wiederholung 4', 'Lektion 1–7 · 20 Aufgaben'),
    wdh(5, 'wiederholung-05.html', 'Wiederholung 5', 'Lektion 1–15 · 25 Aufgaben'),
    { id: 'wiederholung-komplett', group: 'wiederholung', num: 6, file: 'wiederholung-komplett.html',
      label: 'W★', title: 'Komplett-Wiederholung', meta: '17 Themen · 67 Aufgaben · ca. 60 Min', topic: 'wiederholung', doneKey: 'pt-wiederholung-komplett' }
  ];
  const TRAINING = [
    // Speichert sich selbst über PTProgress.save (eigene Sektionen) → selfTracking
    { id: 'perfeito-tempus-v1', group: 'training', num: 1, file: 'uebung-perfeito-tempus.html',
      label: 'Ü1', title: 'Die Vergangenheit: Pretérito Perfeito', meta: '30 Aufgaben · etwa 15 Minuten',
      desc: 'Zuerst entscheidest du, ob ein Satz in der Gegenwart oder in der Vergangenheit steht. Dann übst du die Formen, die nicht der Regel folgen (fui, fiz, tive). Zum Schluss baust du ganze Sätze.',
      topic: 'perfeito', selfTracking: true }
  ];
  const DIAGNOSE = { id: 'diagnose', group: 'diagnose', num: 1, file: 'diagnose-test.html',
    label: 'D', title: 'Einstufungstest', meta: '80 Aufgaben · zeigt dir pro Thema, was sitzt', topic: 'diagnose',
    nextHref: 'fortschritt.html', nextTitle: 'Ergebnis an Claude schicken' };

  const CATALOG = [].concat(TRAINING, TIEFEN, LESSONS, WIEDERHOLUNGEN, [DIAGNOSE]);
  const byId = {}, byFile = {};
  CATALOG.forEach(function (e) { byId[e.id] = e; byFile[e.file] = e; });

  // Lernplan: Reihenfolge nach dem Einstufungstest vom 01.07.2026
  // (Vergangenheit 20 % → unregelmäßige Ich-Formen 60 % → Reflexive 25 % → Präpositionen 70 %)
  const PATH_IDS = ['perfeito-tempus-v1', 'tiefen-01', 'lektion-19', 'lektion-21'];
  // Warum dieser Schritt? Ganze Sätze, verständlich ohne Grammatik-Vorwissen.
  const PATH_WHY = {
    'perfeito-tempus-v1': 'Im Einstufungstest hast du bei Sätzen über gestern oder letzte Woche fast immer die Gegenwart benutzt, zum Beispiel „vou“ statt „fui“.',
    'tiefen-01':          'Im Einstufungstest fehlten dir 4 von 10 unregelmäßigen Ich-Formen, zum Beispiel faço, sei oder trago.',
    'lektion-19':         'Im Einstufungstest saß hier nur jede vierte Antwort. Unklar ist vor allem, wann das Pronomen vor das Verb rückt (chamo-me, aber: não me chamo).',
    'lektion-21':         'Im Einstufungstest waren 3 von 10 Präpositionen falsch, vor allem por gegenüber para und Kurzformen wie pelo.'
  };
  // Ein Thema gilt als sicher, wenn es MASTER_RUNS-mal mit mindestens MASTER_PCT % geschafft wurde.
  const MASTER_PCT = 80, MASTER_RUNS = 2;
  // Für Buttons: "Lektion 19: …" statt "L19 · …"
  function longName(e) {
    if (!e) return '';
    if (e.group === 'lektion') return 'Lektion ' + e.num + ': ' + e.title;
    if (e.group === 'tiefen') return 'Vertiefung ' + e.num + ': ' + e.title;
    return e.title;
  }

  // ======================= PROGRESS-HELFER =======================
  function history() {
    try { return (window.PTProgress && PTProgress.getAll()) || []; } catch (e) { return []; }
  }
  function localDay(d) {
    d = d instanceof Date ? d : new Date(d);
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function runsFor(id) { return history().filter(function (h) { return h.exerciseId === id; }); }
  function bestPct(id) { return runsFor(id).reduce(function (m, h) { return Math.max(m, h.pct); }, -1); }
  function lastRun(id) { const r = runsFor(id); return r.length ? r[r.length - 1] : null; }
  function isMastered(id) {
    return runsFor(id).filter(function (h) { return h.pct >= MASTER_PCT; }).length >= MASTER_RUNS;
  }
  function todayRuns(id) {
    const t = localDay(new Date());
    return runsFor(id).filter(function (h) { return localDay(h.timestamp) === t; });
  }
  function isDone(entry) {
    if (!entry) return false;
    if (runsFor(entry.id).length) return true;
    try { return !!(entry.doneKey && localStorage.getItem(entry.doneKey)); } catch (e) { return false; }
  }
  function streak() {
    const days = {};
    history().forEach(function (h) { days[localDay(h.timestamp)] = true; });
    let n = 0;
    const d = new Date();
    if (!days[localDay(d)]) d.setDate(d.getDate() - 1); // heute noch nichts gemacht ist ok
    while (days[localDay(d)] && n < 3650) { n++; d.setDate(d.getDate() - 1); }
    return n;
  }
  function pathStatus() {
    let currentFound = false;
    return PATH_IDS.map(function (id, i) {
      const e = byId[id];
      const mastered = isMastered(id);
      let state = 'done';
      if (!mastered) { state = currentFound ? 'todo' : 'current'; currentFound = true; }
      return { entry: e, step: i + 1, state: state, best: bestPct(id), runs: runsFor(id).length,
        why: PATH_WHY[id], goodRuns: runsFor(id).filter(function (h) { return h.pct >= MASTER_PCT; }).length };
    });
  }
  function pickToday() {
    const st = pathStatus();
    const cur = st.filter(function (s) { return s.state === 'current'; })[0];
    if (cur) return { entry: cur.entry, step: cur.step, total: PATH_IDS.length, pathComplete: false, status: cur };
    return { entry: DIAGNOSE, step: PATH_IDS.length, total: PATH_IDS.length, pathComplete: true, status: null };
  }
  function nextInPath(id) {
    const i = PATH_IDS.indexOf(id);
    return i >= 0 && i < PATH_IDS.length - 1 ? byId[PATH_IDS[i + 1]] : null;
  }
  function nextSequential(entry) {
    if (!entry) return null;
    const list = CATALOG.filter(function (e) { return e.group === entry.group; });
    return list.filter(function (e) { return e.num === entry.num + 1; })[0] || null;
  }

  // ======================= NAV =======================
  const page = (location.pathname.split('/').pop() || 'index.html').split('?')[0];
  const ICONS = {
    home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 10.5 12 3.5l8.5 7"/><path d="M5.5 9.5V20a1 1 0 0 0 1 1H10v-6h4v6h3.5a1 1 0 0 0 1-1V9.5"/></svg>',
    learn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1" fill="currentColor"/></svg>',
    vocab: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="14" height="13" rx="2.5"/><path d="M7 4h11.5A2.5 2.5 0 0 1 21 6.5V16"/><path d="M7 12h6M7 15.5h4"/></svg>',
    progress: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V11"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M2.5 20h19"/></svg>'
  };
  const NAV = [
    { id: 'home',        icon: ICONS.home,     label: 'Home',        href: 'index.html' },
    { id: 'learn',       icon: ICONS.learn,    label: 'Lernen',      href: 'lernen.html' },
    { id: 'vokabeln',    icon: ICONS.vocab,    label: 'Vokabeln',    href: 'vokabeln.html' },
    { id: 'fortschritt', icon: ICONS.progress, label: 'Fortschritt', href: 'fortschritt.html' }
  ];
  function activeNavId() {
    if (page === 'index.html' || page === '') return 'home';
    if (page === 'lernen.html' || byFile[page]) return 'learn';
    if (page === 'vokabeln.html') return 'vokabeln';
    if (page === 'fortschritt.html') return 'fortschritt';
    return null; // Grammatik, Cheat Sheet, Druck-Sheets: kein Tab aktiv
  }
  function buildNav() {
    if (document.querySelector('.bottom-nav')) return;
    const active = activeNavId();
    const nav = document.createElement('nav');
    nav.className = 'bottom-nav';
    nav.setAttribute('aria-label', 'Hauptnavigation');
    nav.innerHTML = NAV.map(function (item) {
      return '<a href="' + item.href + '" class="bnav-item' + (item.id === active ? ' active' : '') + '"' +
        (item.id === active ? ' aria-current="page"' : '') + '>' + item.icon +
        '<span class="bnav-label">' + item.label + '</span></a>';
    }).join('');
    document.body.appendChild(nav);
  }

  // Tastatur offen → Nav weg (iOS lässt fixed Elemente sonst über der Tastatur springen)
  function watchKeyboard() {
    let t = null;
    function isField(el) { return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT'); }
    document.addEventListener('focusin', function (e) {
      if (!isField(e.target)) return;
      clearTimeout(t);
      document.body.classList.add('pt-kb-open');
    });
    document.addEventListener('focusout', function (e) {
      if (!isField(e.target)) return;
      clearTimeout(t);
      t = setTimeout(function () {
        if (!isField(document.activeElement)) document.body.classList.remove('pt-kb-open');
      }, 120);
    });
  }

  // ======================= SERVICE WORKER =======================
  function registerSW() {
    if (!('serviceWorker' in navigator) || location.protocol !== 'https:') return;
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('./sw.js').catch(function (err) {
        console.warn('SW-Registrierung fehlgeschlagen:', err);
      });
    });
  }

  // ======================= ÜBUNGS-ABSCHLUSS =======================
  function cleanTitle(el) {
    const c = el.cloneNode(true);
    c.querySelectorAll('.count, .from, .badge, .tag').forEach(function (x) { x.remove(); });
    return c.textContent.replace(/\s+/g, ' ').trim().slice(0, 70) || 'Aufgaben';
  }
  function sectionNameFor(input) {
    const sec = input.closest('.section');
    if (sec) {
      const t = sec.querySelector('.section-title');
      if (t) return cleanTitle(t);
      if (sec.dataset.topic) return sec.dataset.topic;
    }
    const card = input.closest('.exercise-card, .drill, .ex');
    if (card && card.dataset.topic) return card.dataset.topic;
    let el = card || input;
    while (el && !(el.classList && el.classList.contains('block-header'))) el = el.previousElementSibling;
    if (el) return cleanTitle(el);
    return 'Aufgaben';
  }
  function promptFor(input) {
    const card = input.closest('.exercise-card, .drill, .ex');
    if (!card) return '';
    const p = card.querySelector('.exercise-hint, .exercise-prompt, .drill-task, .ex-prompt, .translation-prompt');
    let text = p ? p.textContent : '';
    const row = input.closest('.input-row, .drill-input-row');
    if (row && row.textContent.trim()) text += ' | ' + row.textContent;
    if (!text.trim()) text = card.textContent;
    return text.replace(/\s+/g, ' ').trim().slice(0, 140);
  }
  // Liest das Ergebnis direkt aus dem DOM (jede Übung markiert ihre Inputs mit .correct/.incorrect)
  function collectSections() {
    const inputs = document.querySelectorAll('input[data-answers]');
    const order = [], map = {};
    inputs.forEach(function (inp) {
      const ok = inp.classList.contains('correct');
      const bad = inp.classList.contains('incorrect');
      if (!ok && !bad) return;
      const name = sectionNameFor(inp);
      if (!map[name]) { map[name] = { name: name, score: 0, total: 0, wrong: [] }; order.push(name); }
      map[name].total++;
      if (ok) map[name].score++;
      else map[name].wrong.push({ q: promptFor(inp), user: inp.value.trim(), correct: (inp.getAttribute('data-answers') || '').split('|')[0] });
    });
    return order.map(function (n) { return map[n]; });
  }
  function recordResult(entry) {
    if (entry.selfTracking || !window.PTProgress) return null;
    const sections = collectSections();
    const total = sections.reduce(function (s, x) { return s + x.total; }, 0);
    if (!total) return null;
    try { if (entry.doneKey) localStorage.setItem(entry.doneKey, 'done'); } catch (e) {}
    return PTProgress.save({ exerciseId: entry.id, exerciseName: entry.label + ' · ' + entry.title, topic: entry.topic, sections: sections });
  }
  function el(html) { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; }
  function btnLink(cls, href, sub, main) {
    return el('<a class="pt-btn ' + cls + '" href="' + href + '">' + (sub ? '<span class="pt-btn-sub">' + sub + '</span>' : '') + '<span>' + main + '</span></a>');
  }
  function btnRepeat(cls, main) {
    const b = el('<button type="button" class="pt-btn ' + cls + '"><span>' + main + '</span></button>');
    b.addEventListener('click', function () {
      if (typeof window.resetAll === 'function') window.resetAll(); else location.reload();
    });
    return b;
  }
  function renderEndFlow(panel, entry, record) {
    panel.innerHTML = '';
    // Dieser Durchgang in Prozent: bei selbst speichernden Übungen aus der Historie lesen
    const thisRun = record || lastRun(entry.id);
    const thisPct = thisRun ? thisRun.pct : null;

    let noteText = '';
    if (record) noteText = 'Gespeichert: ' + record.totalScore + ' von ' + record.totalCount + ' richtig (' + record.pct + ' %). Alle Ergebnisse findest du unter <a href="fortschritt.html">Fortschritt</a>.';
    else if (entry.selfTracking) noteText = 'Dein Ergebnis ist gespeichert. Alle Ergebnisse findest du unter <a href="fortschritt.html">Fortschritt</a>.';
    if (noteText) panel.appendChild(el('<div class="pt-endflow-note">' + noteText + '</div>'));

    const inPath = PATH_IDS.indexOf(entry.id) >= 0;
    if (entry.group === 'diagnose') {
      panel.appendChild(btnLink('pt-btn-primary', entry.nextHref, 'Nächster Schritt', entry.nextTitle + ' →'));
      panel.appendChild(btnRepeat('pt-btn-secondary', 'Test noch einmal machen'));
    } else if (inPath) {
      const pick = pickToday();
      if (pick.entry.id === entry.id) {
        // Dieser Schritt ist noch nicht sicher (weniger als 2 Durchgänge über 80 %): Empfehlung ist wiederholen.
        const goodRuns = pick.status ? pick.status.goodRuns : 0;
        let why;
        if (thisPct !== null && thisPct >= MASTER_PCT) {
          why = goodRuns >= 1
            ? 'Das war ein Durchgang über ' + MASTER_PCT + ' %. Schaffst du das noch ein zweites Mal, gilt das Thema als sicher und der nächste Schritt wird frei. Das kann auch morgen sein.'
            : 'Gut gemacht. Sobald du zweimal mindestens ' + MASTER_PCT + ' % erreichst, gilt das Thema als sicher.';
        } else if (thisPct !== null) {
          why = 'Dieser Durchgang lag unter ' + MASTER_PCT + ' %. Wiederhole die Übung, bis du zweimal mindestens ' + MASTER_PCT + ' % erreichst, dann gilt das Thema als sicher. Schau dir vorher ruhig die Regeln oben noch einmal an.';
        } else {
          why = 'Sobald du diese Übung zweimal mit mindestens ' + MASTER_PCT + ' % schaffst, gilt das Thema als sicher und der nächste Schritt wird frei.';
        }
        panel.appendChild(btnRepeat('pt-btn-primary', 'Noch einmal üben'));
        panel.appendChild(el('<div class="pt-endflow-note">' + why + '</div>'));
        const nxt = nextInPath(entry.id);
        if (nxt) panel.appendChild(btnLink('pt-btn-secondary', nxt.file, 'Ohne Wiederholung weiter', longName(nxt) + ' →'));
      } else {
        const sub = pick.pathComplete ? 'Alle vier Schritte geschafft' : 'Dein nächster Schritt';
        panel.appendChild(btnLink('pt-btn-primary', pick.entry.file, sub, longName(pick.entry) + ' →'));
        panel.appendChild(btnRepeat('pt-btn-secondary', 'Noch einmal üben'));
      }
    } else {
      const nxt = nextSequential(entry);
      if (nxt) {
        const sub = entry.group === 'lektion' ? 'Nächste Lektion' : 'Weiter';
        panel.appendChild(btnLink('pt-btn-primary', nxt.file, sub, longName(nxt) + ' →'));
        panel.appendChild(btnRepeat('pt-btn-secondary', 'Noch einmal üben'));
      } else {
        panel.appendChild(btnLink('pt-btn-primary', 'lernen.html', 'Fertig', 'Zurück zur Übersicht →'));
        panel.appendChild(btnRepeat('pt-btn-secondary', 'Noch einmal üben'));
      }
    }
    panel.appendChild(btnLink('pt-btn-ghost', 'index.html', '', 'Zur Startseite'));
  }
  function setupEndFlow() {
    const results = document.getElementById('results');
    const entry = byFile[page];
    if (!results || !entry) return;
    document.body.classList.add('pt-has-endflow');
    const panel = document.createElement('div');
    panel.className = 'pt-endflow';
    results.insertAdjacentElement('afterend', panel);

    let shown = false;
    function sync() {
      const visible = results.classList.contains('show');
      if (visible && !shown) {
        shown = true;
        const record = recordResult(entry);
        renderEndFlow(panel, entry, record);
        panel.classList.add('show');
      } else if (!visible && shown) {
        shown = false;
        panel.classList.remove('show');
      }
    }
    new MutationObserver(sync).observe(results, { attributes: true, attributeFilter: ['class'] });
    sync();
  }

  // ======================= API + START =======================
  window.PTApp = {
    CATALOG: CATALOG, LESSONS: LESSONS, TIEFEN: TIEFEN, WIEDERHOLUNGEN: WIEDERHOLUNGEN, TRAINING: TRAINING, DIAGNOSE: DIAGNOSE,
    PATH_IDS: PATH_IDS, MASTER_PCT: MASTER_PCT, MASTER_RUNS: MASTER_RUNS,
    byId: byId, byFile: byFile, page: page,
    history: history, runsFor: runsFor, bestPct: bestPct, lastRun: lastRun, isMastered: isMastered,
    todayRuns: todayRuns, isDone: isDone, streak: streak, localDay: localDay,
    pathStatus: pathStatus, pickToday: pickToday, nextInPath: nextInPath, nextSequential: nextSequential,
    longName: longName
  };

  function start() {
    buildNav();
    watchKeyboard();
    setupEndFlow();
    registerSW();
    document.dispatchEvent(new CustomEvent('ptapp:ready'));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
