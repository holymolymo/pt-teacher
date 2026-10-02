#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bildet die Verbformen regelmäßiger portugiesischer Verben (pt-PT).

Warum überhaupt: Aus den Live-Klassen kommen laufend neue Verben dazu. Die
allermeisten sind regelmäßig, ihre Formen lassen sich also rechnen statt von
Hand eintippen. Von Hand eingetippte Tabellen sind die häufigste Fehlerquelle,
gerechnete nicht, solange der Rechner selbst geprüft ist.

Geprüft wird er gegen die 28 Verben in _verben.py, deren Formen bereits von
mehreren Muttersprachlern Form für Form kontrolliert wurden. Alles, was dieser
Rechner bei den regelmäßigen davon anders bildet, ist ein Fehler im Rechner.

Was er NICHT kann und auch nicht können soll: unregelmäßige Verben. Die gehören
weiterhin von Hand in _verben.py, nachdem ein Muttersprachler sie bestätigt hat.

Die Rechtschreibregeln, die hier stecken, sind die üblichen Verdächtigen:
    -car  → qu vor e      ficar  → fiquei
    -gar  → gu vor e      chegar → cheguei, ligar → liguei
    -çar  → c  vor e      começar → comecei
    -cer  → ç  vor o, a   crescer → cresço
    -ger  → j  vor o, a   proteger → protejo
    -gir  → j  vor o, a   dirigir → dirijo
    -guir → g  vor o, a   seguir → sigo (dazu meist Stammwechsel)
Dazu der Stammwechsel e→i in der Ich-Form vieler -ir-Verben (gerir → giro).
"""

import re
import unicodedata

PERSONEN = ['eu', 'tu', 'ele/ela', 'nós', 'eles/elas']

# Endungen je Konjugationsklasse, Reihenfolge wie PERSONEN.
# Beim Perfeito der -ar-Verben trägt die wir-Form in Portugal den Akzent:
# falámos. In Brasilien steht dort falamos, also dieselbe Form wie die Gegenwart.
ENDUNGEN = {
    'ar': {
        'pres': ['o', 'as', 'a', 'amos', 'am'],
        'perf': ['ei', 'aste', 'ou', 'ámos', 'aram'],
        'imp':  ['ava', 'avas', 'ava', 'ávamos', 'avam'],
    },
    'er': {
        'pres': ['o', 'es', 'e', 'emos', 'em'],
        'perf': ['i', 'este', 'eu', 'emos', 'eram'],
        'imp':  ['ia', 'ias', 'ia', 'íamos', 'iam'],
    },
    'ir': {
        'pres': ['o', 'es', 'e', 'imos', 'em'],
        'perf': ['i', 'iste', 'iu', 'imos', 'iram'],
        'imp':  ['ia', 'ias', 'ia', 'íamos', 'iam'],
    },
}
# Der Konditional hängt immer an der vollen Grundform, auch bei unregelmäßigen.
# Drei Verben kürzen den Stamm: dizer → diria, fazer → faria, trazer → traria.
COND_ENDUNGEN = ['ia', 'ias', 'ia', 'íamos', 'iam']
COND_SONDERSTAMM = {'dizer': 'dir', 'fazer': 'far', 'trazer': 'trar',
                    'pôr': 'por', 'vir': 'vir', 'ter': 'ter'}


def _rechtschreibung_vor_e(stamm):
    """Vor einem e muss der Klang erhalten bleiben: ficar → fiquei."""
    if stamm.endswith('c'):
        return stamm[:-1] + 'qu'
    if stamm.endswith('g'):
        return stamm + 'u'
    if stamm.endswith('ç'):
        return stamm[:-1] + 'c'
    return stamm


def _rechtschreibung_vor_o_a(stamm):
    """Vor o und a ebenso: crescer → cresço, dirigir → dirijo."""
    if stamm.endswith('gu'):
        return stamm[:-2] + 'g'
    if stamm.endswith('c'):
        return stamm[:-1] + 'ç'
    if stamm.endswith('g'):
        return stamm[:-1] + 'j'
    return stamm


def _stamm_mit_i(stamm):
    """
    Stammwechsel e→i in der Ich-Form vieler -ir-Verben: gerir → giro,
    sentir → sinto, preferir → prefiro. Gewechselt wird das LETZTE e im Stamm.
    """
    i = stamm.rfind('e')
    return stamm[:i] + 'i' + stamm[i + 1:] if i >= 0 else stamm


def konjugiere(infinitiv, stammwechsel=None):
    """
    Vollständige Tabelle für ein regelmäßiges Verb.

    stammwechsel='e_i'  für -ir-Verben, die in der Ich-Form e zu i wechseln
    stammwechsel='o_u'  für -ir-Verben wie dormir (durmo), subir (subo bleibt)

    Reflexive Verben (auf -se) werden ohne Pronomen gebildet; das Anhängen
    übernimmt reflexiv_formen().
    """
    inf = infinitiv.strip()
    reflexiv = inf.endswith('-se')
    if reflexiv:
        inf = inf[:-3]

    klasse = inf[-2:]
    if klasse not in ENDUNGEN:
        raise ValueError(f'{infinitiv}: endet nicht auf -ar, -er oder -ir')
    stamm = inf[:-2]

    # Verben auf -ear schieben in den betonten Formen ein i ein:
    # passear → passeio, passeias, passeia, ABER passeamos ohne i.
    # Betont sind hier die Formen 1, 2, 3 und 5, nicht die wir-Form.
    ear = inf.endswith('ear')

    tabelle = {}
    for zeit in ('pres', 'perf', 'imp'):
        formen = []
        for i, endung in enumerate(ENDUNGEN[klasse][zeit]):
            s = stamm
            # Welche Rechtschreibregel greift, hängt an der KLASSE, nicht nur am
            # Buchstaben der Endung. Bei -ar-Verben muss der harte Klang vor e
            # gerettet werden (ficar → fiquei). Bei -er- und -ir-Verben ist das c
            # vor e ohnehin weich, dort muss umgekehrt vor o und a gerettet
            # werden (conhecer → conheço). Beides zu vermischen erzeugt Unsinn
            # wie "conhequeste", und genau das hat der Selbsttest gefangen.
            if klasse == 'ar':
                if endung[0] in 'eéií':
                    s = _rechtschreibung_vor_e(s)
            else:
                if endung[0] in 'oa':
                    s = _rechtschreibung_vor_o_a(s)
            if ear and zeit == 'pres' and i != 3:
                s = s + 'i'
            if i == 0 and endung[0] in 'oa':
                if stammwechsel == 'e_i':
                    s = _stamm_mit_i(s)
                elif stammwechsel == 'o_u':
                    j = s.rfind('o')
                    if j >= 0:
                        s = s[:j] + 'u' + s[j + 1:]
            formen.append(s + endung)
        tabelle[zeit] = formen

    stamm_cond = COND_SONDERSTAMM.get(inf, inf)
    tabelle['cond'] = [stamm_cond + e for e in COND_ENDUNGEN]
    return tabelle


def reflexiv_formen(tabelle_pres):
    """
    Pronomen angehängt (Standardstellung in Portugal) und vorangestellt
    (nach einem Auslöserwort wie não, já, que).

    Die eine Stolperstelle: bei "wir" fällt das s vor -nos weg.
    levantamos + nos wird levantamo-nos, nicht levantamos-nos.
    """
    pronomen = ['me', 'te', 'se', 'nos', 'se']
    nach, vor = [], []
    for i, form in enumerate(tabelle_pres):
        f = form
        if pronomen[i] == 'nos' and f.endswith('s'):
            f = f[:-1]
        nach.append(f + '-' + pronomen[i])
        vor.append(pronomen[i] + ' ' + form)
    return nach, vor


# ------------------------------------------------------------------ Selbsttest

def selbsttest(laut=True):
    """
    Prüft den Rechner gegen die von Muttersprachlern bestätigten Tabellen in
    _verben.py. Geprüft werden nur die Verben, die dort als regelmäßig oder als
    nur-in-der-Ich-Form-unregelmäßig geführt sind.
    """
    import _verben as V

    # Diese Verben sind unregelmäßig und dürfen vom Rechner abweichen.
    UNREGELMAESSIG = {'ser', 'estar', 'ter', 'ir', 'vir', 'fazer', 'dizer', 'ver',
                      'dar', 'poder', 'querer', 'saber', 'trazer', 'pôr', 'ler',
                      # eigene Ich-Form oder Hiatus-Akzent, nicht rechenbar:
                      'perder', 'ouvir', 'pedir', 'sair'}
    # Stammwechsel, soweit in der geprüften Datenbank erkennbar.
    WECHSEL = {'sentir': 'e_i', 'preferir': 'e_i', 'pedir': 'e_i',
               'dormir': 'o_u', 'conseguir': 'e_i', 'sair': None, 'perder': None}

    fehler, geprueft = [], 0
    for inf, v in V.VERBEN.items():
        if inf in UNREGELMAESSIG:
            continue
        try:
            t = konjugiere(inf, WECHSEL.get(inf))
        except ValueError as e:
            fehler.append(str(e)); continue
        for zeit in ('pres', 'perf', 'imp', 'cond'):
            if zeit not in v:
                continue
            geprueft += 1
            if t[zeit] != v[zeit]:
                for i, (a, b) in enumerate(zip(t[zeit], v[zeit])):
                    if a != b:
                        fehler.append(f'{inf} {zeit} {PERSONEN[i]}: gerechnet {a}, geprüft {b}')

    # Reflexive gegen die geprüften Tabellen
    for inf, v in V.REFLEXIVE.items():
        basis = inf[:-3]
        wechsel = 'e_i' if basis in ('sentir', 'esquecer') and basis == 'sentir' else None
        if basis == 'sentir':
            wechsel = 'e_i'
        try:
            t = konjugiere(basis, wechsel)
        except ValueError:
            continue
        nach, vor = reflexiv_formen(t['pres'])
        geprueft += 2
        if nach != v['nach']:
            for i, (a, b) in enumerate(zip(nach, v['nach'])):
                if a != b:
                    fehler.append(f'{inf} angehängt {PERSONEN[i]}: gerechnet {a}, geprüft {b}')
        if vor != v['vor']:
            for i, (a, b) in enumerate(zip(vor, v['vor'])):
                if a != b:
                    fehler.append(f'{inf} vorangestellt {PERSONEN[i]}: gerechnet {a}, geprüft {b}')

    if laut:
        print(f'Formenbildner gegen {geprueft} geprüfte Reihen getestet.')
        if fehler:
            print(f'{len(fehler)} Abweichungen:')
            for f in fehler:
                print('   ', f)
        else:
            print('Keine Abweichung.')
    return fehler


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    f = selbsttest()
    raise SystemExit(1 if f else 0)
