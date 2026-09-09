#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fügt die Karten einer neuen Klasse in die bestehenden Packs ein.

Aufruf:  python3 _klasse_einfuegen.py <karten.json>

Die JSON-Datei enthält Einträge {pt, de, notiz, kategorie}.
Vorhandene Karten werden ersetzt (die neue Fassung gewinnt, weil sie geprüft ist),
neue werden angehängt. Danach wird die Master-Datei neu gebaut.
"""
import csv, json, os, re, sys, unicodedata

DIR = os.path.dirname(os.path.abspath(__file__))
KATEGORIEN = ['verben', 'nomen', 'adjektive', 'redewendungen', 'grammatik', 'fragen', 'umgangssprache']

def norm(s):
    s = (s or '').strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[.!?,;:\'"\\/()–—-]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def lies(pfad):
    rows = list(csv.reader(open(pfad, encoding='utf-8-sig'), delimiter=';'))
    return rows[0], [r for r in rows[1:] if r and r[0].strip()]

def schreibe(pfad, kopf, daten):
    with open(pfad, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(kopf)
        for r in sorted(daten, key=lambda x: norm(x[0])):
            w.writerow(r)

def main(quelle):
    neue = json.load(open(quelle, encoding='utf-8'))

    # alle vorhandenen Karten über alle Packs indizieren, damit eine Karte
    # nicht in zwei Kategorien landet
    bestand = {}   # norm(pt) -> (kategorie, index)
    packs = {}
    for kat in KATEGORIEN:
        pfad = os.path.join(DIR, f'vokabeln-{kat}.csv')
        kopf, daten = lies(pfad)
        packs[kat] = [kopf, daten]
        for i, r in enumerate(daten):
            bestand.setdefault(norm(r[0]), (kat, i))

    ersetzt = angehaengt = verschoben = 0
    for k in neue:
        kat = k['kategorie']
        if kat not in packs:
            print(f'  unbekannte Kategorie {kat} bei {k["pt"]}'); continue
        zeile = [k['pt'], k['de'], k.get('notiz', '')]
        treffer = bestand.get(norm(k['pt']))
        if treffer:
            alt_kat, idx = treffer
            if alt_kat == kat:
                packs[kat][1][idx] = zeile
                ersetzt += 1
            else:
                # Karte wechselt die Kategorie: alt raus, neu rein
                packs[alt_kat][1][idx] = None
                packs[kat][1].append(zeile)
                verschoben += 1
        else:
            packs[kat][1].append(zeile)
            bestand[norm(k['pt'])] = (kat, len(packs[kat][1]) - 1)
            angehaengt += 1

    for kat, (kopf, daten) in packs.items():
        daten = [r for r in daten if r]
        schreibe(os.path.join(DIR, f'vokabeln-{kat}.csv'), kopf, daten)

    # Master neu bauen
    alle, seen = [], set()
    for kat in ['konjugation'] + KATEGORIEN:
        pfad = os.path.join(DIR, f'vokabeln-{kat}.csv')
        if not os.path.exists(pfad): continue
        _, daten = lies(pfad)
        for r in daten:
            pt, de, notiz = (r + ['', ''])[:3]
            key = (norm(pt), norm(de))
            if key in seen: continue
            seen.add(key); alle.append([pt, de, notiz])
    schreibe(os.path.join(DIR, 'vokabeln-master.csv'), ['Portugiesisch', 'Deutsch', 'Notiz'], alle)

    print(f'  ersetzt      {ersetzt}')
    print(f'  neu          {angehaengt}')
    print(f'  umsortiert   {verschoben}')
    print()
    gesamt = 0
    for kat in ['konjugation'] + KATEGORIEN:
        pfad = os.path.join(DIR, f'vokabeln-{kat}.csv')
        if not os.path.exists(pfad): continue
        n = len(lies(pfad)[1])
        print(f'  vokabeln-{kat:16s} {n:4d}')
        gesamt += n
    print(f'  {"":26s} ----')
    print(f'  {"gesamt":26s} {gesamt:4d}   (Master: {len(alle)})')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '_neue_karten.json')
