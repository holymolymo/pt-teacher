#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setzt die Artikel-Ergebnisse in vokabeln-nomen.csv um."""
import csv, json, os, re, unicodedata

DIR = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    s = (s or '').strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[.!?,;:\'"\\/()\-–—]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

r = json.load(open(os.path.join(DIR, '_artikel.json'), encoding='utf-8'))
# Zweitmeinung überschreibt den unsicheren Erstvorschlag
geklaert = {norm(g['alt']): g['neu'] for g in (r.get('geklaert') or [])}

karten = {}
for k in r['karten']:
    karten[norm(k['alt'])] = k

pfad = os.path.join(DIR, 'vokabeln-nomen.csv')
rows = list(csv.reader(open(pfad, encoding='utf-8-sig'), delimiter=';'))
kopf, daten = rows[0], rows[1:]

neu, geloescht, geaendert, unberuehrt = [], 0, 0, 0
for row in daten:
    if not row or not row[0].strip():
        continue
    pt, de, notiz = (row + ['', ''])[:3]
    k = karten.get(norm(pt))
    if not k:
        neu.append([pt, de, notiz]); unberuehrt += 1; continue
    if k.get('loeschen'):
        geloescht += 1; continue
    npt = geklaert.get(norm(pt)) or k.get('neu') or pt
    nde = k.get('de_neu') or de
    nnotiz = k.get('notiz') or notiz
    if npt != pt or nde != de or nnotiz != notiz:
        geaendert += 1
    neu.append([npt, nde, nnotiz])

with open(pfad, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    w.writerow(kopf)
    for row in sorted(neu, key=lambda x: norm(x[0])):
        w.writerow(row)

print(f'geändert   {geaendert}')
print(f'gelöscht   {geloescht}')
print(f'unberührt  {unberuehrt}')
print(f'jetzt      {len(neu)} Substantive')
