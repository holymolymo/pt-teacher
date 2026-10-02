#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stellt die App auf den dunklen Neumori-Stil um.

Die Vorlage ist nicht geraten, sondern von neumori.de abgelesen:
    Markengrün   #1B371F   (alle Knöpfe, alle dunklen Flächen)
    Textfarbe    #040D21
    helle Fläche #F2F2F2
    Schriften    Poppins und Montserrat
    Radien       4 bis 8 Pixel, dazu Pillenform
Die App hatte dagegen: warmes Beige #F5F0EB, Orange #E8721D, Inter, Radien um 18 Pixel.

Weil Moritz es DUNKLER wollte, wird das Markengrün zur Fläche und ein aufgehellter
Ton daraus zum Akzent. Dunkelgrün auf dunklem Grund hätte keinen Kontrast.

Aufruf:  python3 tools/neumori_stil.py          (zeigt nur an, was passieren würde)
         python3 tools/neumori_stil.py --machen  (schreibt)
"""

import glob, os, re, sys

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------- die Palette

PALETTE = {
    # Flächen, von dunkel nach weniger dunkel
    '#f5f0eb': '#0d1410',   # Seitenhintergrund
    '#ede6df': '#26382b',   # Linien und Trenner
    '#e8d5c4': '#26382b',
    '#faf8f5': '#16221a',   # Karten
    '#fff8f2': '#16221a',
    '#ffffff': '#16221a',   # weiße Karten werden zu dunklen Karten
    '#fcfbf9': '#16221a',
    '#f7f4f0': '#121c15',

    # Schrift, von hell nach gedämpft
    '#1a1715': '#ecefea',
    '#2d2a26': '#ecefea',
    '#4a4540': '#c2ccc4',
    '#6b6560': '#9da89f',
    '#8a837c': '#6e7a71',
    '#9e9892': '#6e7a71',
    '#55504b': '#b4bfb7',

    # Akzent: das Markengrün, aufgehellt damit es auf Dunkel trägt
    '#e8721d': '#5fa86b',
    '#d4650f': '#4e9159',
    '#b34700': '#3f7a49',
    '#f08a3c': '#72b87d',

    # Richtig
    '#2e7d32': '#5fa86b',
    '#1b5e20': '#4e9159',
    '#256b29': '#4e9159',
    '#e8f5e9': '#15291a',
    '#c8e6c9': '#2a4530',

    # Falsch
    '#c62828': '#e2695f',
    '#b71c1c': '#c9564c',
    '#ffebee': '#2b1715',
    '#ffcdd2': '#3d201c',
    '#c0392b': '#e2695f',

    # Hinweis
    '#f9a825': '#d9a648',
    '#795600': '#d9a648',
    '#b8860b': '#d9a648',
    '#7a5c1e': '#d9a648',
    '#fff8e1': '#2a2113',
    '#fff3e0': '#2a2113',
    '#ffe0b2': '#3a2e18',
    '#f0e4d0': '#3a2e18',
    '#fffaf2': '#2a2113',
    '#fff8e8': '#2a2113',
    '#f0e0bd': '#3a2e18',
    '#6b5a2e': '#d9a648',
    '#e0cfa6': '#3a2e18',

    # Blau und Violett, nur vereinzelt benutzt
    '#5c6bc0': '#7e8bd4',
    '#3f51b5': '#6c7ac9',
    '#e8eaf6': '#1a2030',
    '#c5cae9': '#2a3350',
    '#1976d2': '#6fa8dc',
    '#7b1fa2': '#a672c0',
    '#6a1b9a': '#9664b0',
    '#faf5fc': '#1d1726',
    '#fdf3f7': '#241720',
    '#c2185b': '#d4738f',

    # Resttöne aus einzelnen Seiten
    '#e4ddd4': '#26382b',
    '#ece5dc': '#26382b',
    '#f2ede7': '#121c15',
    '#3a3631': '#1b371f',
    '#000000': '#0d1410',
}

# Enge Radien statt der weichen Rundungen. Pillenform bleibt.
RADIEN = {
    '24px': '12px', '22px': '12px', '20px': '10px', '18px': '10px',
    '16px': '8px', '15px': '8px', '14px': '8px', '13px': '8px', '12px': '8px',
}


def ersetze_farben(text):
    """Nur echte Farbangaben anfassen, keine Versionsnummern oder Anker."""
    def tausch(m):
        h = m.group(0).lower()
        if len(h) == 4:
            h = '#' + ''.join(c * 2 for c in h[1:])
        return PALETTE.get(h, m.group(0))
    return re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', tausch, text)


def ersetze_radien(text):
    def tausch(m):
        wert = m.group(2)
        return m.group(1) + RADIEN.get(wert, wert)
    return re.sub(r'(border-radius:\s*)(\d+px)', tausch, text)


def ersetze_schrift(text):
    text = text.replace(
        "family=Inter:wght@400;500;600;700;800",
        "family=Poppins:wght@400;500;600;700;800")
    text = text.replace("'Inter', -apple-system", "'Poppins', -apple-system")
    text = text.replace('"Inter", -apple-system', "'Poppins', -apple-system")
    text = text.replace("font-family: 'Inter'", "font-family: 'Poppins'")
    return text


def main():
    schreiben = '--machen' in sys.argv
    dateien = sorted(glob.glob(os.path.join(HIER, '*.html')) +
                     glob.glob(os.path.join(HIER, 'css', '*.css')))
    gesamt = 0
    for pfad in dateien:
        if os.path.basename(pfad).startswith('_'):
            continue
        alt = open(pfad, encoding='utf-8').read()
        neu = ersetze_schrift(ersetze_radien(ersetze_farben(alt)))
        if neu == alt:
            continue
        geaendert = sum(1 for a, b in zip(alt.split('\n'), neu.split('\n')) if a != b)
        gesamt += geaendert
        print(f'   {os.path.basename(pfad):46} {geaendert:4} Zeilen')
        if schreiben:
            open(pfad, 'w', encoding='utf-8').write(neu)
    print(f'\n{gesamt} Zeilen in {len(dateien)} Dateien' +
          ('' if schreiben else '  (Probelauf, nichts geschrieben)'))


if __name__ == '__main__':
    main()
