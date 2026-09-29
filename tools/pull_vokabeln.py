#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liest Moritz' Stand im Vokabeltrainer aus Supabase.

Am Anfang jeder Sitzung aufrufen, zusammen mit pull_results.py:

    python3 tools/pull_vokabeln.py            # Überblick
    python3 tools/pull_vokabeln.py --schwach  # nur was hakt
    python3 tools/pull_vokabeln.py --tage 7   # nur die letzte Woche
    python3 tools/pull_vokabeln.py --json     # roh zum Weiterrechnen

ACHTUNG: Das Supabase-Projekt ist im Gratis-Tarif und pausiert nach etwa einer
Woche ohne Zugriff. Kommt hier ein Verbindungsfehler, ist es meist nur das.
Aufwecken über den Supabase-MCP (restore_project) oder die Weboberfläche,
dann dauert es ein bis zwei Minuten. Moritz' Antworten gehen dabei nicht
verloren, sie warten auf seinem Gerät in der Warteschlange.
"""

import argparse, collections, json, sys, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone

URL   = 'https://zhddqcgvrfhajbgpekon.supabase.co'
KEY   = 'sb_publishable_FuqpDPiql_-yAbBauzq06Q_of3BWnMd'
NOTEN = {0: 'nicht gut', 1: 'geht so', 2: 'sitzt'}


def hole(pfad, params):
    frage = '&'.join(f'{k}={v}' for k, v in params.items())
    req = urllib.request.Request(
        f'{URL}/rest/v1/{pfad}?{frage}',
        headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tage', type=int, help='nur Antworten der letzten N Tage')
    p.add_argument('--schwach', action='store_true', help='nur Aufgaben, die zuletzt nicht saßen')
    p.add_argument('--json', action='store_true', help='Rohdaten ausgeben')
    a = p.parse_args()

    params = {'select': '*', 'order': 'client_ts.desc', 'limit': '5000'}
    if a.tage:
        seit = (datetime.now(timezone.utc) - timedelta(days=a.tage)).isoformat()
        params['client_ts'] = f'gte.{seit}'

    try:
        log = hole('pt_vokabel_log', params)
    except urllib.error.URLError as e:
        print(f'Kein Zugriff auf die Datenbank: {e}')
        print('Wahrscheinlich pausiert das Projekt. Siehe Hinweis oben im Skript.')
        sys.exit(1)

    if a.json:
        print(json.dumps(log, ensure_ascii=False, indent=1))
        return

    if not log:
        print('Noch keine einzige Antwort im Vokabeltrainer.')
        print('Entweder hat Moritz noch nicht angefangen, oder seine Antworten hängen')
        print('noch in der Warteschlange auf dem Gerät, weil die Datenbank schlief.')
        return

    # Aktueller Stand je Aufgabe = neueste Zeile (die Liste kommt absteigend sortiert)
    stand = {}
    for z in log:
        stand.setdefault(z['aufgabe_id'], z)

    noten = collections.Counter(z['note'] for z in stand.values())
    pakete = collections.defaultdict(lambda: collections.Counter())
    for z in stand.values():
        pakete[z.get('paket') or '?'][z['note']] += 1

    tage = collections.Counter(z['client_ts'][:10] for z in log)
    erste, letzte = log[-1]['client_ts'][:16], log[0]['client_ts'][:16]

    print(f'{len(log)} Antworten auf {len(stand)} verschiedene Aufgaben')
    print(f'von {erste} bis {letzte}, an {len(tage)} verschiedenen Tagen\n')

    print('Wie steht es um die Aufgaben, die er schon gesehen hat:')
    for n in (2, 1, 0):
        anteil = noten[n] / len(stand) * 100 if stand else 0
        print(f'   {NOTEN[n]:10} {noten[n]:5}  ({anteil:.0f} %)')

    print('\nJe Paket (sitzt / geht so / nicht gut):')
    for paket, c in sorted(pakete.items(), key=lambda kv: -sum(kv[1].values())):
        gesamt = sum(c.values())
        print(f'   {paket:16} {gesamt:4} gesehen   {c[2]:4} / {c[1]:4} / {c[0]:4}')

    print('\nDie letzten sieben Lerntage:')
    for tag, n in sorted(tage.items(), reverse=True)[:7]:
        print(f'   {tag}   {n:4} Antworten')

    schwach = sorted([z for z in stand.values() if z['note'] == 0],
                     key=lambda z: (z.get('paket') or '', z.get('pt') or ''))
    if schwach:
        grenze = len(schwach) if a.schwach else 25
        print(f'\nWas gerade nicht sitzt ({len(schwach)} Aufgaben, hier {min(grenze, len(schwach))}):')
        for z in schwach[:grenze]:
            antwort = f'  er tippte: {z["antwort"]}' if z.get('antwort') else ''
            print(f'   [{z.get("paket","?")[:12]:13}] {(z.get("pt") or "")[:40]:42} {(z.get("de") or "")[:34]}{antwort}')

    falsch = [z for z in log if z.get('antwort') and z.get('richtig') is False]
    if falsch:
        print(f'\nGetippte Antworten, die falsch waren ({len(falsch)}, hier die letzten 20):')
        for z in falsch[:20]:
            print(f'   {z["client_ts"][:10]}  {(z.get("de") or "")[:40]:42} er: {z["antwort"][:22]:24} richtig: {(z.get("pt") or "")[:22]}')


if __name__ == '__main__':
    main()
