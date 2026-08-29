#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baut alle Vokabel-Packs neu auf.

Quellen:
  1. die bestehenden sieben CSVs (der gewachsene Bestand)
  2. _audit_korrekturen.json  — 206 Karten, die in der falschen Kategorie lagen
  3. _neue_karten.json        — 116 Karten aus den Klassen vom 12.08., 21.08. und 27.08.
  4. vokabeln-konjugation.csv — wird separat von _konjugation.py gebaut, hier nur
                                gebraucht, um Doppelungen zu erkennen

Was dieses Skript tut:
  - wendet die Umkategorisierungen an
  - wirft konjugierte Einzelformen raus (die stehen jetzt im Konjugations-Pack)
  - entfernt Dubletten, auf der portugiesischen wie auf der deutschen Seite
  - hängt die neuen Karten an
  - schreibt acht saubere CSVs
"""
import csv
import json
import os
import re
import sys
import unicodedata

DIR = os.path.dirname(os.path.abspath(__file__))
KATEGORIEN = ['verben', 'nomen', 'adjektive', 'redewendungen', 'grammatik', 'fragen', 'umgangssprache']


def norm(s):
    """Für den Dublettenabgleich: klein, ohne Akzente, ohne Satzzeichen."""
    s = (s or '').strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[.!?,;:\'"\\/()\-–—]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def lies(kat):
    pfad = os.path.join(DIR, f'vokabeln-{kat}.csv')
    if not os.path.exists(pfad):
        return []
    with open(pfad, encoding='utf-8-sig', newline='') as f:
        r = csv.reader(f, delimiter=';')
        rows = list(r)
    return [tuple(x + [''] * (3 - len(x)))[:3] for x in rows[1:] if x and x[0].strip()]


# ---------------------------------------------------------------------------
# Erkennung: ist das eine konjugierte Einzelform statt einer Vokabel?
# Diese Karten wandern ersatzlos raus, das Konjugations-Pack deckt sie ab.
# ---------------------------------------------------------------------------
PRONOMEN_START = ('eu ', 'tu ', 'ele ', 'ela ', 'nós ', 'nos ', 'eles ', 'elas ', 'ele/ela ', 'você ')

# Endungen, an denen man eine konjugierte Form erkennt (Perfeito und Presente 1. Ps.)
PERF_ENDUNGEN = ('ei', 'aste', 'ou', 'ámos', 'aram', 'i', 'este', 'eu', 'emos', 'eram',
                 'iste', 'iu', 'imos', 'iram')
# Formen, die eindeutig konjugiert sind (unregelmäßig, stehen alle im Konjugations-Pack)
BEKANNTE_FORMEN = {
    'fui', 'foste', 'foi', 'fomos', 'foram', 'tive', 'tiveste', 'teve', 'tivemos', 'tiveram',
    'fiz', 'fizeste', 'fez', 'fizemos', 'fizeram', 'estive', 'esteve', 'estivemos', 'estiveram',
    'vim', 'veio', 'viemos', 'vieram', 'vi', 'viu', 'viram', 'dei', 'deu', 'demos', 'deram',
    'disse', 'dissemos', 'disseram', 'pude', 'pode', 'pudemos', 'puderam', 'quis', 'quisemos',
    'soube', 'soubemos', 'pus', 'pos', 'pusemos', 'trouxe', 'trouxemos',
    'sou', 'es', 'e', 'somos', 'sao', 'estou', 'estas', 'esta', 'estamos', 'estao',
    'tenho', 'tens', 'tem', 'temos', 'vou', 'vais', 'vai', 'vamos', 'vao',
    'venho', 'vens', 'vem', 'vimos', 'faco', 'digo', 'vejo', 'dou', 'posso', 'quero',
    'sei', 'ponho', 'trago', 'era', 'eras', 'eramos', 'eram', 'tinha', 'tinhas', 'tinhamos',
    'seria', 'teria', 'faria', 'diria', 'gostaria',
}


def ist_konjugiert(pt, de):
    """Erkennt Karten, die eine gebeugte Einzelform statt einer Vokabel abfragen."""
    p = norm(pt)
    # "Eu sou", "Nós temos", ...
    if p.startswith(PRONOMEN_START) and len(p.split()) <= 3:
        return True
    # nackte bekannte Form
    if p in BEKANNTE_FORMEN:
        return True
    # deutsche Seite verrät die Person: "ich war", "wir hatten"
    d = norm(de)
    if re.match(r'^(ich|du|er|sie|wir|ihr)\s+\w+$', d) and len(p.split()) <= 2:
        return True
    return False


def baue():
    korrekturen = json.load(open(os.path.join(DIR, '_audit_korrekturen.json'), encoding='utf-8'))
    neue = json.load(open(os.path.join(DIR, '_neue_karten.json'), encoding='utf-8'))

    # Nachschlagewerk: welche Karte soll wohin?
    ziel = {}
    for k in korrekturen:
        ziel[(norm(k['pt']), norm(k['de']))] = k['soll']

    packs = {kat: [] for kat in KATEGORIEN}
    stat = {'gelesen': 0, 'umsortiert': 0, 'konjugiert_raus': 0, 'dublette_raus': 0, 'neu': 0}

    # 1) Bestand einlesen, umsortieren, Konjugationen aussortieren
    roh = []
    for kat in KATEGORIEN:
        for pt, de, notiz in lies(kat):
            stat['gelesen'] += 1
            if ist_konjugiert(pt, de):
                stat['konjugiert_raus'] += 1
                continue
            neu_kat = ziel.get((norm(pt), norm(de)), kat)
            if neu_kat != kat:
                stat['umsortiert'] += 1
            if neu_kat not in packs:
                neu_kat = kat
            roh.append((neu_kat, pt, de, notiz))

    # 2) neue Karten anhängen
    for k in neue:
        kat = k.get('kategorie')
        if kat in packs:
            roh.append((kat, k['pt'], k['de'], k.get('notiz', '')))
            stat['neu'] += 1

    # 3) Dubletten entfernen: gleiche PT-Seite oder gleiche DE-Seite innerhalb eines Packs
    for kat, pt, de, notiz in roh:
        p, d = norm(pt), norm(de)
        vorhanden = packs[kat]
        doppelt = False
        for i, (epk, edk, ept, ede, enotiz) in enumerate(vorhanden):
            if epk == p or edk == d:
                # die Karte mit der informativeren Notiz gewinnt
                if len(notiz or '') > len(enotiz or ''):
                    vorhanden[i] = (epk, edk, pt, de, notiz)
                doppelt = True
                break
        if doppelt:
            stat['dublette_raus'] += 1
        else:
            vorhanden.append((p, d, pt, de, notiz))

    return packs, stat


def schreibe(packs):
    ergebnis = {}
    for kat, eintraege in packs.items():
        pfad = os.path.join(DIR, f'vokabeln-{kat}.csv')
        with open(pfad, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            w.writerow(['Portugiesisch', 'Deutsch', 'Notiz'])
            for _, _, pt, de, notiz in sorted(eintraege, key=lambda x: x[0]):
                w.writerow([pt, de, notiz])
        ergebnis[kat] = len(eintraege)
    return ergebnis


if __name__ == '__main__':
    packs, stat = baue()
    zahlen = schreibe(packs)

    print('Umbau der Vokabel-Packs')
    print(f'  eingelesen            {stat["gelesen"]:4d}')
    print(f'  umsortiert            {stat["umsortiert"]:4d}')
    print(f'  Konjugationen raus    {stat["konjugiert_raus"]:4d}   (stehen jetzt im Konjugations-Pack)')
    print(f'  Dubletten raus        {stat["dublette_raus"]:4d}')
    print(f'  neu aus den Klassen   {stat["neu"]:4d}')
    print()
    gesamt = 0
    for kat in KATEGORIEN:
        print(f'  vokabeln-{kat:16s} {zahlen[kat]:4d}')
        gesamt += zahlen[kat]
    # Konjugations-Pack dazu
    kpfad = os.path.join(DIR, 'vokabeln-konjugation.csv')
    if os.path.exists(kpfad):
        with open(kpfad, encoding='utf-8-sig') as f:
            nk = sum(1 for _ in f) - 1
        print(f'  vokabeln-{"konjugation":16s} {nk:4d}   (aus _konjugation.py)')
        gesamt += nk
    print(f'  {"":26s} ----')
    print(f'  {"gesamt":26s} {gesamt:4d}')
