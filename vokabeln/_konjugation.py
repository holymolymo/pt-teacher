#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baut das Konjugations-Pack für Lengo (vokabeln-konjugation.csv).

Drei Kartenarten:
  REIHE    "ter — Vergangenheit"  ->  "tive, tiveste, teve, tivemos, tiveram"
           Das ganze Paradigma auf einer Karte. Lengo fragt beidseitig ab, damit
           trainiert dieselbe Karte auch das Erkennen.
  SATZ     "Ontem fui ao ginásio."  ->  "Gestern bin ich ins Fitnessstudio gegangen."
           Vollständiger Satz mit sichtbarem Zeit-Auslöser. Kein Lückentext, weil
           der rückwärts nicht funktioniert. Die deutsche Seite ist die Lücke:
           Moritz muss Zeitform wählen UND Form bilden.
  REGEL    Eine Frage als Vorderseite, die Regel als Antwort. Für die Zeiten,
           die man herleiten kann, statt sie auswendig zu lernen.

Alle Formen stammen aus _verben.py und sind dort geprüft.
Sätze sind bewusst aus Moritz' eigenen Themen: Laufen, Hyrox, Business, Familie, Schlaf.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verben import VERBEN, REFLEXIVE, PERSONEN, ZEIT_NAMEN, ZEIT_LANG, selbsttest

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def reihe(inf, zeit, anzeige=None, notiz=None):
    """Formenreihe als eine Karte."""
    v = VERBEN[inf]
    name = anzeige or inf
    vorne = f'{name} — {ZEIT_NAMEN[zeit]}'
    hinten = ', '.join(v[zeit])
    n = notiz or v.get('hinweis') or ''
    if not n:
        n = f'{v["de"]} · {ZEIT_LANG[zeit]}'
    return (vorne, hinten, n)


# ============================================================================
# BLOCK A — Zeit-Anker: die Wörter, die eine Zeitform auslösen
# Kommen zuerst, weil Moritz' Fehler ein Auslöser-Problem ist, kein Formen-Problem.
# ============================================================================
ANKER = [
    ('ontem', 'gestern',
     'Verlangt immer die Vergangenheit. Ontem fui ao ginásio, nie ontem vou.'),
    ('anteontem', 'vorgestern',
     'Verlangt die Vergangenheit. Anteontem tive uma reunião.'),
    ('na semana passada', 'letzte Woche',
     'Verlangt die Vergangenheit. Na semana passada corri quinze quilómetros.'),
    ('no mês passado / no ano passado', 'letzten Monat / letztes Jahr',
     'Verlangt die Vergangenheit. No mês passado estive na Alemanha.'),
    ('há dois dias / há um ano', 'vor zwei Tagen / vor einem Jahr',
     'Bei einem abgeschlossenen Ereignis steht die Vergangenheit: há dois meses ela saiu. Dauert die Sache bis heute an, heißt há seit und die Gegenwart bleibt: há dois anos que moro aqui. Und: há dois meses reicht, há dois meses atrás ist doppelt gemoppelt.'),
    ('normalmente / todos os dias', 'normalerweise / jeden Tag',
     'Verlangt die Gegenwart: normalmente corro de manhã. Für Gewohnheiten, die früher galten, nimmst du die Erzählvergangenheit: antigamente corria.'),
]


# ============================================================================
# BLOCK B — Vergangenheit (Pretérito Perfeito): Reihen
# Größte Lücke, deshalb der dickste Block.
# ============================================================================
PERF_REIHEN = [
    ('ser', 'ser / ir', 'Beide Verben haben dieselbe Vergangenheit. Was gemeint ist, sagt der Satz: fui médico heißt ich war Arzt, fui ao cinema heißt ich ging ins Kino.'),
    ('estar', None, 'Im Test hast du "estou doente na semana passada" geschrieben. Estou ist jetzt, estive war letzte Woche.'),
    ('ter', None, 'Im Test hast du temos gesagt, wo tivemos hingehörte. Temos ist die Gegenwart, tivemos ist gestern.'),
    ('vir', None, 'vim heißt ich kam. Achtung bei vimos: das ist die Gegenwart von vir (wir kommen) und zugleich die Vergangenheit von ver (wir sahen). Wir kamen heißt viemos.'),
    ('fazer', None, 'Der Stamm ist fiz-, nur die er-Form bricht aus und heißt fez.'),
    ('dizer', None, 'Ich und er sind gleich: eu disse, ele disse.'),
    ('ver', None, 'vimos heißt hier wir sahen. Dieselbe Form ist bei vir die Gegenwart wir kommen.'),
    ('dar', None, 'dei, deu und deram sind kurz, deshalb leicht zu überhören.'),
    ('poder', None, 'pôde für er trägt ein Dach, sonst wäre es nicht von pode zu unterscheiden.'),
    ('querer', None, 'Ich und er sind gleich: quis. quis heißt ich wollte in dem Moment, queria heißt ich hätte gern. Verneint ist não quis ein deutliches ich weigerte mich.'),
    ('saber', None, 'soube ist der Moment, in dem du etwas erfahren hast. Für den Zustand ich wusste nimmst du sabia. Verneint dreht es sich um: não soube heißt ich wusste nicht.'),
    ('pôr', None, 'pus, pôs. Sehr kurz, sehr unregelmäßig.'),
    ('trazer', None, 'trouxe wird trosse gesprochen. Ich und er sind gleich.'),
    ('falar', None, 'So geht jedes regelmäßige Verb auf -ar. In Portugal trägt die Wir-Form den Akzent: falámos. Ohne Akzent wäre es die Gegenwart.'),
    ('comer', None, 'So geht jedes regelmäßige Verb auf -er. comemos ist Gegenwart und Vergangenheit zugleich, der Satz entscheidet.'),
    ('partir', None, 'So geht jedes regelmäßige Verb auf -ir. partimos ist Gegenwart und Vergangenheit zugleich.'),
]


# ============================================================================
# BLOCK C — Vergangenheit: Sätze mit Zeit-Auslöser
# Genau der Fehler aus dem Test: Auslöser da, trotzdem Gegenwart benutzt.
# ============================================================================
PERF_SAETZE = [
    ('Ontem fui ao ginásio depois do trabalho.',
     'Gestern bin ich nach der Arbeit ins Fitnessstudio gegangen.',
     'Ontem verlangt fui. Genau hier hast du im Test vou geschrieben. Ganze Reihe: fui, foste, foi, fomos, foram.'),
    ('Na semana passada estive doente e não treinei.',
     'Letzte Woche war ich krank und habe nicht trainiert.',
     'estou wäre jetzt in diesem Moment, für letzte Woche brauchst du estive. Ganze Reihe: estive, estiveste, esteve, estivemos, estiveram.'),
    ('Anteontem tivemos uma reunião com o fornecedor.',
     'Vorgestern hatten wir ein Treffen mit dem Lieferanten.',
     'Wir-Form: tivemos, nicht temos. Ganze Reihe: tive, tiveste, teve, tivemos, tiveram.'),
    ('Ontem fiz uma caminhada na montanha com os meus amigos.',
     'Gestern habe ich mit meinen Freunden eine Bergwanderung gemacht.',
     'fiz von fazer. Beachte auch os meus amigos, in Portugal steht vor dem Possessiv der Artikel.'),
    ('O meu irmão disse que se demitiu no ano passado.',
     'Mein Bruder sagte, dass er letztes Jahr gekündigt hat.',
     'disse von dizer. Nach que rutscht das Pronomen vor das Verb: que se demitiu.'),
    ('Ontem à noite vi um filme português muito bom.',
     'Gestern Abend habe ich einen sehr guten portugiesischen Film gesehen.',
     'vi von ver. In Portugal sagt man ver um filme, nicht assistir um filme.'),
    ('Na semana passada corri quinze quilómetros até à praia.',
     'Letzte Woche bin ich fünfzehn Kilometer bis zum Strand gelaufen.',
     'corri ist regelmäßig. Beachte até à praia mit Verschmelzung, nicht até a praia.'),
    ('Ontem não pude ir à festa porque estava cansado.',
     'Gestern konnte ich nicht zur Party gehen, weil ich müde war.',
     'pude von poder. Im zweiten Teil steht estava, weil es einen Zustand beschreibt.'),
    ('Há dois meses ela saiu da empresa, mas eu continuei.',
     'Vor zwei Monaten hat sie die Firma verlassen, aber ich habe weitergemacht.',
     'Dein eigener Satz aus der Klasse. Há dois meses reicht, das atrás am Ende ist doppelt gemoppelt.'),
    ('No mês passado reservei uma casa no Brasil.',
     'Letzten Monat habe ich ein Haus in Brasilien gebucht.',
     'reservei ist regelmäßig auf -ar. Auslöser ist no mês passado.'),
    ('Ontem dormi mal porque a aula acabou muito tarde.',
     'Gestern habe ich schlecht geschlafen, weil der Kurs sehr spät zu Ende war.',
     'Zwei Vergangenheitsformen in einem Satz: dormi und acabou.'),
    ('Quando soube da festa, já era tarde.',
     'Als ich von der Party erfuhr, war es schon zu spät.',
     'soube heißt erfuhr, nicht wusste. Era beschreibt den Zustand drumherum.'),
    ('Ele trouxe o jantar e pusemos tudo na mesa.',
     'Er brachte das Abendessen mit und wir stellten alles auf den Tisch.',
     'trouxe von trazer, pusemos von pôr. Beide sehen fremd aus und brauchen Wiederholung.'),
    ('Esta semana voltei a ver One Piece.',
     'Diese Woche habe ich wieder angefangen, One Piece zu schauen.',
     'voltar a fazer heißt etwas wieder tun. In Portugal sagt man ver um filme oder assistir a um filme, nie assistir um filme ohne a.'),
    ('Ontem falei com o meu irmão sobre o casamento.',
     'Gestern habe ich mit meinem Bruder über die Hochzeit gesprochen.',
     'falei ist regelmäßig. Man spricht com alguém sobre alguma coisa.'),
    ('Eles vieram tarde e nós já tínhamos comido.',
     'Sie kamen spät und wir hatten schon gegessen.',
     'vieram von vir. Tínhamos comido ist die Vorvergangenheit, kommt später dran.'),
    ('Consegui correr a minha primeira meia maratona.',
     'Ich habe meinen ersten Halbmarathon geschafft.',
     'Dein eigener Satz. consegui von conseguir, regelmäßig auf -ir.'),
]


# ============================================================================
# BLOCK D — Kipp-Sätze: zwei Zeiten in einem Satz
# Trainiert genau die Stelle, an der die Gegenwart wieder durchrutscht.
# ============================================================================
KIPP_SAETZE = [
    ('Normalmente faço desporto de manhã, mas ontem não fiz nada.',
     'Normalerweise mache ich morgens Sport, aber gestern habe ich nichts gemacht.',
     'Ein Satz, zwei Zeiten: normalmente zieht faço, ontem zieht fiz.'),
    ('Hoje vou ao escritório, mas ontem fui ao coworking.',
     'Heute gehe ich ins Büro, aber gestern ging ich ins Coworking.',
     'hoje zieht vou, ontem zieht fui. Dieselbe Wurzel, zwei Zeiten.'),
    ('Agora estou bem, mas na semana passada estive doente.',
     'Jetzt geht es mir gut, aber letzte Woche war ich krank.',
     'agora zieht estou, na semana passada zieht estive.'),
    ('Todos os dias corro cinco quilómetros, ontem corri quinze.',
     'Jeden Tag laufe ich fünf Kilometer, gestern bin ich fünfzehn gelaufen.',
     'Bei Verben auf -er und -ir trennt die Ich-Form nur ein Buchstabe: corro und corri, como und comi. Bei -ar-Verben ist der Abstand größer: falo und falei.'),
    ('Sei que tens razão, mas ontem não soube o que dizer.',
     'Ich weiß, dass du recht hast, aber gestern wusste ich nicht, was ich sagen sollte.',
     'Verneint heißt não soube tatsächlich ich wusste nicht. Bejaht wäre soube der Moment des Erfahrens.'),
    ('Este mês temos muitos clientes, no mês passado tivemos poucos.',
     'Diesen Monat haben wir viele Kunden, letzten Monat hatten wir wenige.',
     'temos gegen tivemos. Genau dieses Paar hast du im Test verwechselt.'),
]


# ============================================================================
# BLOCK E — Gegenwart: nur die unregelmäßigen Reihen
# Die regelmäßige Gegenwart sitzt zu 100 Prozent und bekommt keine Karte.
# ============================================================================
PRES_REIHEN = [
    ('ser', None, None), ('estar', None, None), ('ter', None, None),
    ('ir', None, None), ('vir', None, None),
    ('fazer', None, 'Nur die Ich-Form bricht aus, der Rest läuft normal. Das ç muss sein, sonst spricht man fako.'),
    ('dizer', None, 'Ich-Form digo, danach normal.'),
    ('ver', None, 'vês und vê mit Dach, veem mit zwei e.'),
    ('dar', None, 'dou, dás, dá. Sehr kurz.'),
    ('poder', None, 'posso mit zwei s.'),
    ('querer', None, 'quer für er ohne Endung.'),
    ('saber', None, 'sei ist die Ausnahme, sabes und sabe sind normal.'),
    ('pôr', None, 'ponho, pões, põe. Das einzige Verb auf -ôr.'),
    ('trazer', None, 'trago, danach normal.'),
]

PRES_ICHFORM_SAETZE = [
    ('Faço desporto três vezes por semana.', 'Ich mache dreimal pro Woche Sport.',
     'faço mit ç. Alles andere ist normal: fazes, faz, fazemos, fazem.'),
    ('Digo sempre a verdade.', 'Ich sage immer die Wahrheit.',
     'digo. Alles andere ist normal: dizes, diz, dizemos, dizem.'),
    ('Ouço música enquanto corro.', 'Ich höre Musik, während ich laufe.',
     'ouço mit ç. Alles andere ist normal: ouves, ouve, ouvimos, ouvem.'),
    ('Peço sempre a mesma coisa no café.', 'Ich bestelle im Café immer dasselbe.',
     'peço mit ç. pedir heißt bitten oder bestellen, perguntar heißt eine Frage stellen.'),
    ('Conheço Lisboa muito bem.', 'Ich kenne Lissabon sehr gut.',
     'conheço mit ç. conhecer für Orte und Menschen, saber für Fakten.'),
    ('Esqueço-me sempre das chaves.', 'Ich vergesse immer die Schlüssel.',
     'esqueço mit ç, dazu das angehängte -me. Immer mit de: esqueço-me de.'),
    ('Consigo correr dez quilómetros sem parar.', 'Ich schaffe es, zehn Kilometer ohne Pause zu laufen.',
     'consigo heißt ich bringe es zustande. posso heißt ich darf oder ich habe die Möglichkeit: não posso ir, tenho de trabalhar.'),
    ('Perco sempre o telemóvel.', 'Ich verliere ständig das Handy.',
     'perco statt perdo. In Portugal telemóvel, nicht celular.'),
    ('Ponho as chaves em cima da mesa.', 'Ich lege die Schlüssel auf den Tisch.',
     'ponho von pôr. Alles andere: pões, põe, pomos, põem.'),
    ('Durmo sete horas por noite.', 'Ich schlafe sieben Stunden pro Nacht.',
     'durmo mit u. Alles andere ist normal: dormes, dorme, dormimos, dormem.'),
    ('Saio de casa às sete da manhã.', 'Ich gehe um sieben Uhr morgens aus dem Haus.',
     'saio. sair de casa, aber sair para o trabalho.'),
]


# ============================================================================
# BLOCK F — Reflexive Verben und die Stellung von me, te, se
# ============================================================================
REFLEXIV_KARTEN = [
    ('chamar-se — Standardstellung', 'chamo-me, chamas-te, chama-se, chamamo-nos, chamam-se',
     'Ohne Auslöserwort hängt das Pronomen hinten am Verb. Bei wir fällt das s weg: chamamo-nos.'),
    ('levantar-se — Standardstellung', 'levanto-me, levantas-te, levanta-se, levantamo-nos, levantam-se',
     'Bei wir fällt das s weg: levantamo-nos, nicht levantamos-nos.'),
    ('sentir-se — Standardstellung', 'sinto-me, sentes-te, sente-se, sentimo-nos, sentem-se',
     'Ich-Form sinto mit i. Bei wir fällt das s weg: sentimo-nos.'),
    ('Nach welchen Wörtern rutscht me, te, se vor das Verb?',
     'Immer: não, nunca, nada, ninguém, alle Fragewörter und alles, was einen Nebensatz einleitet (que, porque, quando, se). Nur wenn sie vor dem Verb stehen: sempre, também, já, só.',
     'Ohne so ein Wort steht es hinten: chamo-me Moritz. Mit einem davor: não me chamo Pedro. Steht sempre hinter dem Verb, bleibt das Pronomen hinten: esqueço-me sempre.'),
    ('Não me deito antes da meia-noite.', 'Ich gehe nicht vor Mitternacht schlafen.',
     'não zieht das me nach vorn. Ohne não hieße es deito-me antes da meia-noite.'),
    ('Nunca me esqueço do teu aniversário.', 'Ich vergesse deinen Geburtstag nie.',
     'nunca steht vor dem Verb und zieht das me mit. Ohne nunca hieße es esqueço-me do teu aniversário.'),
    ('Como te chamas?', 'Wie heißt du?',
     'Fragewörter ziehen das Pronomen nach vorn. Deshalb te chamas, nicht chamas-te.'),
    ('Levantamo-nos sempre às sete.', 'Wir stehen immer um sieben auf.',
     'Hier steht sempre hinter dem Verb, deshalb bleibt das Pronomen hinten. Und das s fällt weg: levantamo-nos.'),
    ('Sei que ela se chama Marta.', 'Ich weiß, dass sie Marta heißt.',
     'que zieht das se nach vorn.'),
    ('Na semana passada inscrevi-me num ginásio novo.', 'Letzte Woche habe ich mich in einem neuen Fitnessstudio angemeldet.',
     'Auch in der Vergangenheit hängt das Pronomen hinten an, solange kein Auslöser davorsteht.'),
]


# ============================================================================
# BLOCK G — Verb-Ketten: die Bausteine, die er täglich braucht
# ============================================================================
KETTEN = [
    ('estar a + Grundform', 'gerade dabei sein, etwas zu tun',
     'Estou a trabalhar heißt ich arbeite gerade. In Brasilien sagt man estou trabalhando, in Portugal nicht.'),
    ('ir + Grundform', 'gleich etwas tun, nahe Zukunft',
     'Vou fazer heißt ich mache gleich. So bildet man in Portugal die Zukunft, das echte Futur farei hört man kaum.'),
    ('ter + Partizip', 'seit einer Weile etwas tun, bis jetzt',
     'Tenho treinado muito heißt ich trainiere zurzeit viel. Du benutzt das schon frei.'),
    ('acabar de + Grundform', 'gerade eben etwas getan haben',
     'Acabei de chegar heißt ich bin gerade angekommen.'),
    ('costumava + Grundform', 'früher gewohnheitsmäßig etwas tun',
     'Costumava correr aos domingos heißt früher lief ich sonntags immer.'),
    ('devias + Grundform', 'du solltest',
     'Devias concentrar-te no negócio. In Portugal ist focar reflexiv: focar-te em, nicht focar em. Formal ist devias die Erzählvergangenheit von dever, im Gespräch ersetzt sie die würde-Form.'),
]


# ============================================================================
# BLOCK H — Erzählvergangenheit (Imperfeito)
# Nur vier Verben sind unregelmäßig, der Rest folgt zwei Endungssätzen.
# ============================================================================
IMP_REIHEN = [
    ('ser', None, 'Eine der nur vier Ausnahmen dieser Zeit.'),
    ('ter', None, 'Eine der nur vier Ausnahmen. tinha ist sehr häufig.'),
    ('vir', None, 'Eine der nur vier Ausnahmen.'),
    ('pôr', None, 'Die vierte und letzte Ausnahme dieser Zeit.'),
]

IMP_REGEL = [
    ('Wie bildest du die Erzählvergangenheit?',
     'Bei -ar: -ava, -avas, -ava, -ávamos, -avam. Bei -er und -ir: -ia, -ias, -ia, -íamos, -iam.',
     'Nur vier Verben der ganzen Sprache fallen aus der Reihe: ser, ter, vir und pôr. Sogar estar ist hier regelmäßig: estava.'),
    ('Wann nimmst du die Erzählvergangenheit statt der normalen Vergangenheit?',
     'Für Zustände, Gewohnheiten und Beschreibungen. Für ein einzelnes abgeschlossenes Ereignis nimmst du die normale Vergangenheit.',
     'Ontem fui ao cinema ist ein Ereignis. Quando era pequeno, ia ao cinema aos domingos beschreibt eine Gewohnheit.'),
]


# ============================================================================
# BLOCK I — würde-Form (Condicional)
# Vollständig regelbar, deshalb keine einzige Reihe.
# ============================================================================
COND_KARTEN = [
    ('Wie bildest du die würde-Form?',
     'Grundform plus -ia, -ias, -ia, -íamos, -iam. Also falaria, comeria, partiria.',
     'Nur drei Verben kürzen den Stamm: fazer wird faria, dizer wird diria, trazer wird traria. Ich und er sind immer gleich.'),
    ('Wie sagt man in Portugal im Gespräch lieber statt der würde-Form?',
     'Man nimmt die Erzählvergangenheit: gostava de ir statt gostaria de ir, podias statt poderias.',
     'Das gilt für die gesprochene Sprache, vor allem bei gostar, poder, dever und querer. Geschrieben nimmt man die würde-Form.'),
    ('Gostava de mudar-me para Portugal.', 'Ich würde gerne nach Portugal ziehen.',
     'Alltagsform. Mit der würde-Form hieße es gostaria de mudar-me.'),
    ('No teu lugar, não diria isso.', 'An deiner Stelle würde ich das nicht sagen.',
     'diria von dizer, einer der drei Kurzstämme.'),
]


def baue():
    karten, gesehen = [], set()

    def add(pt, de, notiz=''):
        key = (pt.strip().lower(), de.strip().lower())
        if key in gesehen:
            return
        gesehen.add(key)
        # Semikolon würde die CSV-Spalte zerreißen
        karten.append((pt.replace(';', ','), de.replace(';', ','), (notiz or '').replace(';', ',')))

    # A — Zeit-Anker
    for pt, de, n in ANKER:
        add(pt, de, n)

    # B — Vergangenheit, Reihen
    for inf, anzeige, notiz in PERF_REIHEN:
        pt, de, n = reihe(inf, 'perf', anzeige, notiz)
        add(pt, de, n)

    # C + D — Vergangenheit, Sätze
    for pt, de, n in PERF_SAETZE + KIPP_SAETZE:
        add(pt, de, n)

    # E — Gegenwart, unregelmäßige Reihen und Ich-Form-Sätze
    for inf, anzeige, notiz in PRES_REIHEN:
        pt, de, n = reihe(inf, 'pres', anzeige, notiz)
        add(pt, de, n)
    for pt, de, n in PRES_ICHFORM_SAETZE:
        add(pt, de, n)

    # F — Reflexive
    for pt, de, n in REFLEXIV_KARTEN:
        add(pt, de, n)

    # G — Verb-Ketten
    for pt, de, n in KETTEN:
        add(pt, de, n)

    # H — Erzählvergangenheit
    for inf, anzeige, notiz in IMP_REIHEN:
        pt, de, n = reihe(inf, 'imp', anzeige, notiz)
        add(pt, de, n)
    for pt, de, n in IMP_REGEL:
        add(pt, de, n)

    # I — würde-Form
    for pt, de, n in COND_KARTEN:
        add(pt, de, n)

    return karten


def schreibe(karten, dateiname='vokabeln-konjugation.csv'):
    pfad = os.path.join(OUTPUT_DIR, dateiname)
    with open(pfad, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(['Portugiesisch', 'Deutsch', 'Notiz'])
        for pt, de, notiz in karten:
            w.writerow([pt, de, notiz])
    return pfad


if __name__ == '__main__':
    probleme = selbsttest()
    if probleme:
        print('Verb-Datenbank fehlerhaft, Abbruch:')
        for p in probleme:
            print('  -', p)
        sys.exit(1)

    karten = baue()
    pfad = schreibe(karten)

    bloecke = [
        ('A  Zeit-Anker', len(ANKER)),
        ('B  Vergangenheit, Reihen', len(PERF_REIHEN)),
        ('C  Vergangenheit, Sätze', len(PERF_SAETZE)),
        ('D  Kipp-Sätze, zwei Zeiten', len(KIPP_SAETZE)),
        ('E  Gegenwart unregelmäßig', len(PRES_REIHEN) + len(PRES_ICHFORM_SAETZE)),
        ('F  Reflexive und Stellung', len(REFLEXIV_KARTEN)),
        ('G  Verb-Ketten', len(KETTEN)),
        ('H  Erzählvergangenheit', len(IMP_REIHEN) + len(IMP_REGEL)),
        ('I  würde-Form', len(COND_KARTEN)),
    ]
    for name, n in bloecke:
        print(f'  {name:32s} {n:3d}')
    print(f'  {"":32s} ---')
    print(f'  {"gesamt":32s} {len(karten):3d}   -> {os.path.basename(pfad)}')
