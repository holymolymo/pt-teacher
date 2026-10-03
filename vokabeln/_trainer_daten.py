#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baut die Datendatei für den Vokabeltrainer in der App: ../daten/trainer.json

Quellen
  1. die neun Karten-Pakete (vokabeln-*.csv)
  2. die Verb-Datenbank (_verben.py) für die Konjugations-Aufgaben
  3. _haeufigkeit.txt — 50.000 Wortformen aus Untertiteln, EUROPÄISCHES Portugiesisch
     (OpenSubtitles 2018, Liste "pt"; nachgeprüft: telemóvel Rang 873, celular 8162)

Wie die Reihenfolge zustande kommt
----------------------------------
Nicht über Ränge, sondern über den Zipf-Wert, weil Ränge nicht linear sind:
zwischen Rang 100 und 200 liegen Welten, zwischen 5000 und 5100 nichts.

    zipf(w) = log10(Vorkommen) + 0,6735          (Korpus: 212.103.058 Token)
    F       = clamp((zipf − 3,0) / 3,5, 0, 1)    Häufigkeitspunkte

Der Deckel bei zipf 6,5 ist Absicht: darüber stehen nur noch Funktionswörter,
die Moritz längst kann, dort lohnt keine weitere Unterscheidung.

Wie aggregiert wird, hängt vom Kartentyp ab:
    LEXEM  ein Wort              → sein eigener Wert
    CHUNK  zwei bis drei Wörter  → das seltenste Inhaltswort entscheidet
    SATZ   vier und mehr         → max(Median der Inhaltswörter, Anker)
           Das max ist wichtig: ein einziges seltenes Wort darf einen Satz,
           der eine häufige Regel zeigt, nicht nach hinten versenken.
    REGEL  "embora + Konjunktiv" → aus der Häufigkeit des Phänomens, nie aus
           den Wörtern des Beispiels

Der Endwert einer Aufgabe ist nicht die Häufigkeit allein:

    W = 0,50 × F  +  0,35 × G  +  0,15 × A

    G  Diagnosebindung: übt die Aufgabe einen seiner belegten Dauerfehler
    A  Aktualität: war das Thema gerade im Unterricht

W steuert NUR, in welcher Reihenfolge neue Aufgaben eingeführt werden.
Die Wiederholungsabstände kommen allein aus seinen Antworten (js/srs.js),
dort greift die Häufigkeit nie ein.

Aufruf:  python3 _trainer_daten.py
"""

import csv, json, math, os, re, statistics, sys

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, '..', 'daten', 'trainer.json')
FREQ = os.path.join(HIER, '_haeufigkeit.txt')

PAKETE = ['scharniere', 'konjugation', 'verben', 'nomen', 'adjektive',
          'redewendungen', 'grammatik', 'fragen', 'umgangssprache']

ZIPF_MIN, ZIPF_SPANNE, ZIPF_UNBEKANNT = 3.0, 3.5, 2.50

# Wörter, die bei der Aggregation nicht zählen. Sie sind überall häufig und
# würden jeden Mehrwort-Eintrag gleich aussehen lassen.
FUNKTIONSWOERTER = set("""o a os as um uma uns umas de do da dos das em no na nos nas
e que se para por com à ao aos às não é eu tu ele ela nós eles elas me te lhe lhes
mais muito já ser estar ter o's""".split())

# Deutsche Metasprache auf der portugiesischen Seite. Ein Treffer heißt: Regelkarte.
META = set("""vergangenheit gegenwart erzählvergangenheit grundform infinitiv konjunktiv
partizip würde-form standardstellung endung person plural singular artikel inf statt
nach vor wann wie formen alle fünf""".split())

# Anker: das unveränderliche Wort einer Konstruktion. Daraus kommt der Wert der
# Regel- und Satzkarten, statt aus den zufälligen Wörtern des Beispiels.
ANKER = ['embora', 'mesmo que', 'talvez', 'espero que', 'antes de', 'depois de',
         'assim que', 'logo que', 'se calhar', 'pelo menos', 'ter de', 'ter que',
         'estar a', 'acabar de', 'deixar de', 'começar a', 'continuar a', 'andar a',
         'costumava', 'ontem', 'anteontem', 'antigamente', 'normalmente', 'sempre',
         'nunca', 'já', 'ainda', 'por', 'para', 'desde', 'há', 'enquanto', 'quando',
         'porque', 'apesar de', 'em vez de', 'a não ser que', 'até que']

# Phänomene, die einen seiner belegten Dauerfehler treffen. G = 1,0.
# Belege stehen in app_state.md, Abschnitt "wiederkehrende Fehler".
DIAGNOSE = [
    (re.compile(r'\b(o|a|os|as)\s+(meu|minha|meus|minhas|teu|tua|teus|tuas|seu|sua|seus|suas|nosso|nossa|nossos|nossas)\b', re.I),
     'artikel-possessiv'),
    (re.compile(r'\w+-(me|te|lhe|se|nos|lhes|o|a|os|as)\b'), 'pronomen-hinten'),
    (re.compile(r'\b(ontem|anteontem|antigamente|no ano passado|na semana passada|no mês passado|há \w+ (dias|meses|anos))\b', re.I),
     'zeitenwahl'),
    (re.compile(r'\b(embora|mesmo que|talvez|espero que|antes de \w+em|assim que|logo que)\b', re.I),
     'konjunktiv'),
]
# Phänomen kommt vor, wird aber nicht geübt. G = 0,7.
NEBENBEI = re.compile(r'\b(meu|minha|meus|minhas|lhe|me|te|se)\b', re.I)

ZEIT_FRAGE = {'pres': 'Gegenwart', 'perf': 'Vergangenheit (Pretérito Perfeito)',
              'imp': 'Erzählvergangenheit (Imperfeito)', 'cond': 'würde-Form (Condicional)'}
PERSON_DE = {'eu': 'ich', 'tu': 'du', 'ele/ela': 'er/sie', 'nós': 'wir', 'eles/elas': 'sie (mehrere)'}

# Welche der 560 Zellen überhaupt in die Rotation kommen.
# Bei den regelmäßigen Mustern ist die Form ableitbar, dort lohnt nur die Zelle,
# die man NICHT ableiten kann: die Ich-Form im Presente, die Wir-Form im Perfeito
# mit ihrem Akzent (falámos).
ZELLEN = {
    'top':    None,                                    # alle zwanzig
    'unreg':  None,                                    # alle zwanzig
    'eu':     [('pres', 0), ('pres', 2), ('perf', 0)],
    'muster': [('perf', 0), ('perf', 2), ('perf', 3), ('imp', 3)],
}


# ------------------------------------------------------------------ Häufigkeit

def lies_haeufigkeit():
    if not os.path.exists(FREQ):
        print(f'  ! {os.path.basename(FREQ)} fehlt. Es wird ohne Häufigkeit gebaut,')
        print('    die Reihenfolge ist dann nur nach Diagnose gewichtet.')
        return {}, 0
    zahl, gesamt = {}, 0
    with open(FREQ, encoding='utf-8') as fh:
        for zeile in fh:
            t = zeile.split()
            if len(t) == 2:
                zahl[t[0]] = int(t[1]); gesamt += int(t[1])
    return zahl, gesamt


WORT = re.compile(r"[a-zà-öø-ÿ]+(?:-[a-zà-öø-ÿ]+)*", re.I)


class Haeufigkeit:
    def __init__(self, zahl, korpus):
        self.zahl = zahl
        self.konstante = (9 - math.log10(korpus)) if korpus else 0.0

    def zipf(self, wort):
        c = self.zahl.get(wort.lower())
        return math.log10(c) + self.konstante if c else ZIPF_UNBEKANNT

    def punkte(self, zipf):
        return round(max(0.0, min(1.0, (zipf - ZIPF_MIN) / ZIPF_SPANNE)), 4)

    def tokens(self, text):
        """Bindestrich-Formen bleiben ganz, sonst wird die Pronomenstellung unsichtbar."""
        return [t.lower() for t in WORT.findall(text)]

    def inhaltswoerter(self, text):
        return [t for t in self.tokens(text) if t not in FUNKTIONSWOERTER and t not in META]

    def anker_zipf(self, text):
        t = text.lower()
        treffer = [a for a in ANKER if a in t]
        if not treffer:
            return None
        # Der häufigste vorkommende Anker trägt die Karte.
        return max(self.zipf(a.split()[0]) for a in treffer)


# ------------------------------------------------------------------ Kartentyp

def typ_der_karte(pt, h):
    t = pt.lower()
    if '+' in pt or any(m in t.split() for m in META):
        return 'REGEL'
    n = len(h.tokens(pt))
    if n >= 4 or pt.strip()[-1:] in '.?!':
        return 'SATZ'
    if n >= 2:
        return 'CHUNK'
    return 'LEXEM'


def punkte_der_karte(pt, typ, h):
    inhalt = h.inhaltswoerter(pt)
    anker = h.anker_zipf(pt)

    if typ == 'REGEL':
        return h.punkte(anker if anker is not None else 4.0), 'anker' if anker else 'geschätzt'
    if typ == 'LEXEM':
        w = h.tokens(pt)
        return h.punkte(max(h.zipf(x) for x in w) if w else ZIPF_UNBEKANNT), 'wort'
    if typ == 'CHUNK':
        if not inhalt:
            inhalt = h.tokens(pt)
        return h.punkte(min(h.zipf(x) for x in inhalt)), 'seltenstes'
    # SATZ: Median der Inhaltswörter, aber der Anker kann ihn heben
    med = statistics.median([h.zipf(x) for x in inhalt]) if inhalt else ZIPF_UNBEKANNT
    if anker is not None and anker > med:
        return h.punkte(anker), 'anker'
    return h.punkte(med), 'median'


def diagnose_bindung(pt, notiz):
    text = pt + ' ' + notiz
    treffer = [name for muster, name in DIAGNOSE if muster.search(pt)]
    if treffer:
        return 1.0, treffer
    if NEBENBEI.search(pt):
        return 0.7, []
    if any(muster.search(text) for muster, _ in DIAGNOSE):
        return 0.4, []
    return 0.0, []


# ------------------------------------------------------------------ Karten lesen

def lies_pakete(h):
    raus = []
    for paket in PAKETE:
        pfad = os.path.join(HIER, f'vokabeln-{paket}.csv')
        if not os.path.exists(pfad):
            continue
        with open(pfad, encoding='utf-8-sig', newline='') as fh:
            for zeile in list(csv.reader(fh, delimiter=';'))[1:]:
                pt, de, notiz = (zeile + ['', ''])[:3]
                pt, de, notiz = pt.strip(), de.strip(), notiz.strip()
                if not pt or not de:
                    continue
                typ = typ_der_karte(pt, h)
                F, quelle = punkte_der_karte(pt, typ, h)
                G, fehler = diagnose_bindung(pt, notiz)
                # Aktualität: was erkennbar aus einer Live-Klasse stammt, steht vorne.
                A = 1.0 if re.search(r'(deiner Klasse|in der Klasse|dein Lehrer|Hat dein Lehrer)', notiz) else 0.0
                raus.append({
                    'typ': typ.lower(), 'pt': pt, 'de': de, 'notiz': notiz, 'paket': paket,
                    'F': F, 'G': G, 'A': A, 'fehler': fehler, 'fquelle': quelle,
                    'richtungen': ['pt_de', 'de_pt'],
                })
    return raus


# ------------------------------------------------------------------ Konjugation

def alle_verben():
    """
    Die von Hand geprüften aus _verben.py plus die gerechneten aus _verben_neu.py.
    Beide zusammen, damit jedes Verb aus den Klassen seine Formen hat, so wie
    Moritz es wollte: nicht nur das Wort, sondern auch seine Konjugation.
    """
    sys.path.insert(0, HIER)
    import _verben as V
    V.selbsttest()          # bricht ab, wenn eine Form von Hand falsch eingetippt wurde
    verben = dict(V.VERBEN)
    reflexive = dict(V.REFLEXIVE)
    try:
        import _verben_neu as N
        verben.update(N.VERBEN_NEU)
        reflexive.update(N.REFLEXIVE_NEU)
    except ImportError:
        pass
    return V, verben, reflexive


def baue_konjugation(h):
    V, VERBEN, REFLEXIVE = alle_verben()

    raus = []
    for inf, v in VERBEN.items():
        gruppe = v.get('gruppe', 'muster')
        erlaubt = ZELLEN.get(gruppe, None)
        for zeit in ('pres', 'perf', 'imp', 'cond'):
            if zeit not in v:
                continue
            for i, person in enumerate(V.PERSONEN):
                if erlaubt is not None and (zeit, i) not in erlaubt:
                    continue
                form = v[zeit][i]
                z = h.zipf(form)
                raus.append({
                    'typ': 'form', 'verb': inf, 'verb_de': v['de'], 'zeit': zeit,
                    'zeit_de': ZEIT_FRAGE[zeit], 'person': person, 'person_de': PERSON_DE[person],
                    'pt': form, 'de': f'{inf} · {ZEIT_FRAGE[zeit]} · {PERSON_DE[person]}',
                    'notiz': v.get('hinweis', ''), 'paket': 'konjugation', 'gruppe': gruppe,
                    'F': h.punkte(z), 'zipf': round(z, 2),
                    'G': 1.0 if zeit in ('perf', 'imp') else 0.4, 'A': 0.0,
                    'fehler': ['zeitenwahl'] if zeit in ('perf', 'imp') else [],
                    'geschwister': [f for f in v[zeit]],
                    'richtungen': ['tippen'],
                })

    # Reflexive: beide Stellungen. Genau hier macht er seinen zweithäufigsten Fehler.
    for inf, v in REFLEXIVE.items():
        for i, person in enumerate(V.PERSONEN):
            form, vorne = v['nach'][i], v['vor'][i]
            z = h.zipf(form)
            raus.append({
                'typ': 'form', 'verb': inf, 'verb_de': v['de'], 'zeit': 'pres',
                'zeit_de': 'Gegenwart', 'person': person, 'person_de': PERSON_DE[person],
                'pt': form, 'de': f'{inf} · Gegenwart · {PERSON_DE[person]}',
                'notiz': (v.get('hinweis', '') + ' Ohne Auslöserwort davor hängt das Pronomen hinten an. '
                          f'Steht não, já, que oder ein Fragewort davor, rutscht es nach vorne: {vorne}.').strip(),
                'paket': 'konjugation', 'gruppe': 'reflexiv',
                'F': h.punkte(z), 'zipf': round(z, 2), 'G': 1.0, 'A': 0.0,
                'fehler': ['pronomen-hinten'], 'geschwister': v['nach'],
                'richtungen': ['tippen'],
            })

    # Ganze Reihe als Merkhilfe, eine je Verb und Zeit. Die Reihe hält die Form
    # zusammen, die Einzelzellen trainieren den Abruf.
    for inf, v in VERBEN.items():
        if v.get('gruppe') not in ('top', 'unreg'):
            continue
        for zeit in ('pres', 'perf', 'imp', 'cond'):
            if zeit not in v:
                continue
            z = max(h.zipf(f) for f in v[zeit])      # die häufigste Form trägt die Reihe
            raus.append({
                'typ': 'reihe', 'verb': inf, 'verb_de': v['de'], 'zeit': zeit,
                'zeit_de': ZEIT_FRAGE[zeit], 'formen': v[zeit],
                'pt': ', '.join(v[zeit]), 'de': f'{inf} · {ZEIT_FRAGE[zeit]} · alle fünf Formen',
                'notiz': v.get('hinweis', ''), 'paket': 'konjugation', 'gruppe': v.get('gruppe', ''),
                'F': h.punkte(z), 'zipf': round(z, 2),
                'G': 1.0 if zeit in ('perf', 'imp') else 0.4, 'A': 0.0,
                'fehler': [], 'richtungen': ['reihe'],
            })
    return raus


def sammle_formtabellen():
    """
    Alle Formen je Verb, damit die App eine getippte Antwort gegen die
    NACHBARFORMEN prüfen kann. Nur so lässt sich "comem" statt "comeram" als
    falsche Person melden, statt es als Tippfehler durchzuwinken.
    """
    V, VERBEN, REFLEXIVE = alle_verben()
    t = {}
    for inf, v in VERBEN.items():
        formen = []
        for zeit in ('pres', 'perf', 'imp', 'cond'):
            formen += v.get(zeit, [])
        t[inf] = sorted(set(formen))
    for inf, v in REFLEXIVE.items():
        t[inf] = sorted(set(v['nach'] + v['vor']))
    return t


# ------------------------------------------------------------------ Grammatikübungen

# Die Lückenaufgaben greifen genau die Fehler an, die in zehn Klassen hintereinander
# belegt sind. Sie werden aus den vorhandenen Sätzen erzeugt, nicht von Hand geschrieben,
# damit jede neue Klasse automatisch neue Übungen mitbringt.
L_POSSESSIV = re.compile(r'\b(o|a|os|as)\s+(meu|minha|meus|minhas|teu|tua|teus|tuas|seu|sua|seus|suas|nosso|nossa|nossos|nossas)\b', re.I)
L_ENKLISE   = re.compile(r'\b(\w+)-(me|te|lhe|se|nos|lhes)\b')
L_PROKLISE  = re.compile(r'\b(não|nunca|já|também|que|quando|porque|onde|quem|só|sempre)\s+(me|te|lhe|se|nos|lhes)\s+(\w+)', re.I)


def baue_luecken(karten, h):
    """
    Erzeugt Grammatikübungen mit Eingabefeld aus den vorhandenen Sätzen.

    Anders als bei Karteikarten ist eine Lücke hier erlaubt, weil getippt wird
    und es keine Rückrichtung gibt, die daran zerbrechen könnte.
    """
    raus = []

    for k in karten:
        pt, de = k['pt'], k['de']
        if len(pt.split()) < 3:
            continue

        # 1. Der Artikel vor dem Possessiv. Sein häufigster Fehler überhaupt,
        #    belegt in zehn Klassen hintereinander.
        m = L_POSSESSIV.search(pt)
        if m:
            satz = pt[:m.start(1)] + '___' + pt[m.end(1):]
            raus.append({
                'typ': 'luecke', 'thema': 'artikel-possessiv',
                'satz': satz, 'pt': m.group(1), 'de': de,
                'platzhalter': 'ein kleines Wort',
                'notiz': 'In Portugal steht vor meu, minha, teu und seu immer der Artikel. '
                         'Ohne ihn klingt der Satz brasilianisch. Das ist dein häufigster Fehler, '
                         'er kam in zehn Klassen hintereinander vor.',
                'paket': 'grammatik', 'F': h.punkte(6.0), 'G': 1.0, 'A': 0.0,
                'fehler': ['artikel-possessiv'], 'richtungen': ['luecke'],
            })
            continue

        # 2. Pronomen hinten am Verb, solange kein Auslöserwort davorsteht.
        m = L_ENKLISE.search(pt)
        if m and not L_PROKLISE.search(pt):
            satz = pt[:m.start(2)] + '___' + pt[m.end(2):]
            raus.append({
                'typ': 'luecke', 'thema': 'pronomen-hinten',
                'satz': satz, 'pt': m.group(2), 'de': de,
                'platzhalter': 'me, te, lhe, se, nos',
                'notiz': 'Steht kein Auslöserwort davor, hängt das Pronomen mit Bindestrich '
                         'hinten am Verb. Vorangestellt wäre es brasilianisch.',
                'paket': 'grammatik', 'F': h.punkte(6.0), 'G': 1.0, 'A': 0.0,
                'fehler': ['pronomen-hinten'], 'richtungen': ['luecke'],
            })
            continue

        # 3. Pronomen nach vorn, sobald ein Auslöserwort davorsteht. Genau das
        #    hat er am 02.10. falsch gemacht: "Quando mudei-me" statt "Quando me mudei".
        m = L_PROKLISE.search(pt)
        if m:
            satz = pt[:m.start(2)] + '___' + pt[m.end(2):]
            raus.append({
                'typ': 'luecke', 'thema': 'pronomen-vorn',
                'satz': satz, 'pt': m.group(2), 'de': de,
                'platzhalter': 'me, te, lhe, se, nos',
                'notiz': f'Nach einem Wort wie {m.group(1).lower()} rutscht das Pronomen vor das Verb. '
                         'Angehängt wäre hier falsch.',
                'paket': 'grammatik', 'F': h.punkte(6.0), 'G': 1.0, 'A': 0.0,
                'fehler': ['pronomen-vorn'], 'richtungen': ['luecke'],
            })

    return raus


# ------------------------------------------------------------------ Übungsart

ARTIKELWOERTER = {'o', 'a', 'os', 'as', 'um', 'uma'}


def uebungsart(a):
    """
    In welche Schublade gehört eine Aufgabe, wenn Moritz vorher auswählen soll,
    was abgefragt wird.

    Der Anlass: Beim ersten echten Versuch bekam er sechzehn ganze Sätze als
    erste Aufgaben, darunter einen mit zwölf Wörtern, und keine einzige Vokabel.
    Wer eine Vokabel-App öffnet, will Vokabeln.

    Entscheidend ist das PAKET, nicht die Wortzahl. Eine Vokabel ist ein
    Inhaltswort: ein Substantiv, ein Verb, ein Adjektiv. "Como" und "Mas" sind
    zwar einzelne Wörter und sehr häufig, aber niemand lernt sie als Vokabel.
    Sie gehören zu den Scharnieren und zur Grammatik.

        vokabeln    Substantive, Verben, Adjektive als Einzelwort
        wendungen   feste Verbindungen, Scharnierwörter, Fragen, Redewendungen
        saetze      ganze Sätze als Muster
        grammatik   Regelkarten und Lückenaufgaben mit Eingabefeld
        formen      Verbformen zum Tippen und ganze Formenreihen
    """
    if a['typ'] in ('form', 'reihe'):
        return 'formen'
    if a['typ'] in ('regel', 'luecke'):
        return 'grammatik'

    w = a['pt'].split()
    kurz = len(w) == 1 or (len(w) == 2 and w[0].lower().strip('„“"') in ARTIKELWOERTER)

    if a['paket'] in ('nomen', 'verben', 'adjektive'):
        return 'vokabeln' if kurz else 'wendungen' if len(w) <= 3 else 'saetze'
    if len(w) >= 4 or a['pt'].strip()[-1:] in '.?!':
        return 'saetze'
    return 'wendungen'


# ------------------------------------------------------------------ Gewichten

KATALOG = os.path.join(HIER, '_katalog.json')


def dauerhafte_kennung(a):
    """
    Ein Schlüssel, der sich NICHT ändert, wenn sich die Reihenfolge ändert.

    Das ist der wichtigste Punkt der ganzen Datei. Wäre die Kennung die
    Sortierposition, würde jede neue Klasse alle Nummern verschieben und
    Moritz' gespeicherter Lernstand läge anschließend auf den falschen
    Aufgaben. Deshalb hängt sie allein am Inhalt.
    """
    if a['typ'] == 'form':
        return f"form|{a['verb']}|{a['zeit']}|{a['person']}"
    if a['typ'] == 'reihe':
        return f"reihe|{a['verb']}|{a['zeit']}"
    if a['typ'] == 'luecke':
        # Der Satz MIT der Lücke identifiziert die Übung, nicht das Lückenwort.
        # Sonst heißen alle Artikel-Übungen gleich, weil dort immer nur "o" steht.
        return f"luecke|{a['thema']}|{a['satz']}"
    return f"karte|{a['paket']}|{a['pt']}"


def gewichte(aufgaben):
    for a in aufgaben:
        a['W'] = round(0.50 * a['F'] + 0.35 * a['G'] + 0.15 * a['A'], 4)
        a['art'] = uebungsart(a)

    # Kennungen aus dem Katalog holen. Einmal vergeben, bleibt eine Kennung für
    # immer bei ihrer Aufgabe. Verschwindet eine Aufgabe, wird ihre Kennung
    # trotzdem nicht neu vergeben, sonst erbt eine neue Karte einen fremden
    # Lernstand.
    katalog = {}
    if os.path.exists(KATALOG):
        with open(KATALOG, encoding='utf-8') as fh:
            katalog = json.load(fh)
    naechste = katalog.get('_naechste', 0)
    neu_vergeben = 0
    for a in sorted(aufgaben, key=lambda x: (-x['W'], x.get('verb', ''), x['pt'])):
        k = dauerhafte_kennung(a)
        if k not in katalog:
            katalog[k] = f'a{naechste:04d}'
            naechste += 1
            neu_vergeben += 1
        a['id'] = katalog[k]
        a['schluessel'] = k
    katalog['_naechste'] = naechste
    with open(KATALOG, 'w', encoding='utf-8') as fh:
        json.dump(katalog, fh, ensure_ascii=False, indent=0, sort_keys=True)

    # Die Sortierung bestimmt nur noch, was zuerst eingeführt wird.
    aufgaben.sort(key=lambda a: (-a['W'], a.get('verb', ''), a['pt']))
    for i, a in enumerate(aufgaben):
        a['platz'] = i

    # Eigene Reihenfolge je Übungsart. Bei Vokabeln und Wendungen zählt allein
    # die Häufigkeit: das alltäglichste Wort kommt zuerst, dann wird es Stück
    # für Stück seltener. Bei Grammatik und Formen bleibt das Gesamtgewicht,
    # dort ist die Bindung an seine Dauerfehler wichtiger als die Worthäufigkeit.
    for art in ('vokabeln', 'wendungen', 'saetze', 'grammatik', 'formen'):
        teil = [a for a in aufgaben if a['art'] == art]
        if art in ('vokabeln', 'wendungen'):
            # Häufigkeit entscheidet, ABER reine Funktionswörter wandern ans
            # Ende. Eu, mas, se und como sind die häufigsten Wörter überhaupt
            # und stünden sonst ganz vorn, obwohl sie niemand als Vokabel lernt.
            def schluessel(a):
                w = [x.lower().strip('„“"?!.,') for x in a['pt'].split()]
                kern = [x for x in w if x not in ARTIKELWOERTER]
                nur_funktion = bool(kern) and all(x in FUNKTIONSWOERTER for x in kern)
                return (1 if nur_funktion else 0, -a['F'], a['pt'])
            teil.sort(key=schluessel)
        else:
            teil.sort(key=lambda a: (-a['W'], a.get('verb', ''), a['pt']))
        for i, a in enumerate(teil):
            a['stufe'] = i
    if neu_vergeben:
        print(f'   {neu_vergeben} neue Kennungen vergeben, {naechste} insgesamt')
    return aufgaben


# ------------------------------------------------------------------ Hauptlauf

def main():
    zahl, korpus = lies_haeufigkeit()
    h = Haeufigkeit(zahl, korpus)
    print(f'Häufigkeitsliste: {len(zahl)} Wortformen, {korpus:,} Vorkommen'.replace(',', '.'))
    if korpus:
        print(f'Zipf-Konstante {h.konstante:.4f}  ·  Kontrolle: que {h.zipf("que"):.2f}, '
              f'ontem {h.zipf("ontem"):.2f}, congelador {h.zipf("congelador"):.2f}')

    karten = lies_pakete(h)
    alle = gewichte(karten + baue_konjugation(h) + baue_luecken(karten, h))
    formtabellen = sammle_formtabellen()

    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    with open(ZIEL, 'w', encoding='utf-8') as fh:
        json.dump({
            'version': 2,
            'quelle': 'Häufigkeit: OpenSubtitles 2018, Liste pt (europäisch), 50.000 Wortformen, '
                      f'{korpus} Token. Zipf = log10(Vorkommen) + {h.konstante:.4f}.',
            'formel': 'W = 0,50 × Häufigkeit + 0,35 × Diagnosebindung + 0,15 × Aktualität',
            'pakete': PAKETE,
            'arten': ['vokabeln', 'wendungen', 'saetze', 'grammatik', 'formen'],
            'formtabellen': formtabellen,
            'aufgaben': alle,
        }, fh, ensure_ascii=False, separators=(',', ':'))

    import collections
    print(f'\n{len(alle)} Aufgaben, {os.path.getsize(ZIEL)/1024:.0f} kB')
    for typ, n in collections.Counter(a['typ'] for a in alle).most_common():
        print(f'   {typ:8} {n:5}')
    print(f'\n{sum(1 for a in alle if a["G"] == 1.0)} Aufgaben treffen einen belegten Dauerfehler.')
    print('\nSo führt die App die ersten zwanzig Aufgaben ein:')
    for a in alle[:20]:
        print(f'   W {a["W"]:.2f}  F {a["F"]:.2f} G {a["G"]:.1f}  {a["paket"][:12]:13} '
              f'{a["pt"][:42]:44} {a["de"][:30]}')


if __name__ == '__main__':
    main()
