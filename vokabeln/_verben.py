#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verb-Datenbank für das Konjugations-Pack (europäisches Portugiesisch, pt-PT).

Reihenfolge der Formen ist IMMER: eu, tu, ele/ela, nós, eles/elas
(vós wird weggelassen, im heutigen pt-PT praktisch nicht gebraucht)

Zeiten:
  pres  = Presente do Indicativo        (Gegenwart)
  perf  = Pretérito Perfeito Simples    (abgeschlossene Vergangenheit)
  imp   = Pretérito Imperfeito          (Erzählvergangenheit, Gewohnheit)
  cond  = Condicional                   (würde-Form)

Wichtig für pt-PT:
  - 1. Person Plural im Perfeito bei -ar-Verben trägt den Akzent: falámos (BR: falamos)
  - "vós" fehlt bewusst
  - ele/ela und você teilen sich die Form, eles/elas und vocês ebenfalls
"""

PERSONEN = ['eu', 'tu', 'ele/ela', 'nós', 'eles/elas']

# gruppe: 'top'  = absolute Kernverben, muss sitzen
#         'unreg' = unregelmäßig, hohe Alltagsfrequenz
#         'muster' = Stellvertreter für die regelmäßigen Muster
#         'eu'    = regelmäßig außer in der Ich-Form (typische Stolperstelle)
VERBEN = {

    # ===================== KERNVERBEN =====================
    'ser': {
        'de': 'sein (dauerhaft)', 'gruppe': 'top',
        'pres': ['sou', 'és', 'é', 'somos', 'são'],
        'perf': ['fui', 'foste', 'foi', 'fomos', 'foram'],
        'imp':  ['era', 'eras', 'era', 'éramos', 'eram'],
        'cond': ['seria', 'serias', 'seria', 'seríamos', 'seriam'],
        'hinweis': 'Die Vergangenheit ist dieselbe wie bei ir. Was gemeint ist, sagt der Satz: fui médico heißt ich war Arzt, fui ao cinema heißt ich ging ins Kino.',
    },
    'estar': {
        'de': 'sein (gerade, vorübergehend)', 'gruppe': 'top',
        'pres': ['estou', 'estás', 'está', 'estamos', 'estão'],
        'perf': ['estive', 'estiveste', 'esteve', 'estivemos', 'estiveram'],
        'imp':  ['estava', 'estavas', 'estava', 'estávamos', 'estavam'],
        'cond': ['estaria', 'estarias', 'estaria', 'estaríamos', 'estariam'],
        'hinweis': 'Die Erzählvergangenheit ist regelmäßig (estava), die normale Vergangenheit dagegen unregelmäßig (estive).',
    },
    'ter': {
        'de': 'haben', 'gruppe': 'top',
        'pres': ['tenho', 'tens', 'tem', 'temos', 'têm'],
        'perf': ['tive', 'tiveste', 'teve', 'tivemos', 'tiveram'],
        'imp':  ['tinha', 'tinhas', 'tinha', 'tínhamos', 'tinham'],
        'cond': ['teria', 'terias', 'teria', 'teríamos', 'teriam'],
        'hinweis': 'tem (er hat) und têm (sie haben) unterscheiden sich nur durch den Akzent.',
    },
    'ir': {
        'de': 'gehen, fahren', 'gruppe': 'top',
        'pres': ['vou', 'vais', 'vai', 'vamos', 'vão'],
        'perf': ['fui', 'foste', 'foi', 'fomos', 'foram'],
        'imp':  ['ia', 'ias', 'ia', 'íamos', 'iam'],
        'cond': ['iria', 'irias', 'iria', 'iríamos', 'iriam'],
        'hinweis': 'ir plus Grundform ist die Zukunft: vou comer, ich esse gleich. Die Vergangenheit ist dieselbe wie bei ser.',
    },
    'vir': {
        'de': 'kommen', 'gruppe': 'top',
        'pres': ['venho', 'vens', 'vem', 'vimos', 'vêm'],
        'perf': ['vim', 'vieste', 'veio', 'viemos', 'vieram'],
        'imp':  ['vinha', 'vinhas', 'vinha', 'vínhamos', 'vinham'],
        'cond': ['viria', 'virias', 'viria', 'viríamos', 'viriam'],
        'hinweis': 'vimos heißt wir kommen (Gegenwart) und zugleich wir sahen (von ver). Wir kamen heißt viemos.',
    },

    # ===================== HÄUFIGE UNREGELMÄSSIGE =====================
    'fazer': {
        'de': 'machen, tun', 'gruppe': 'unreg',
        'pres': ['faço', 'fazes', 'faz', 'fazemos', 'fazem'],
        'perf': ['fiz', 'fizeste', 'fez', 'fizemos', 'fizeram'],
        'imp':  ['fazia', 'fazias', 'fazia', 'fazíamos', 'faziam'],
        'cond': ['faria', 'farias', 'faria', 'faríamos', 'fariam'],
        'hinweis': 'faço mit ç. Die würde-Form kommt vom Kurzstamm far-, also faria.',
    },
    'dizer': {
        'de': 'sagen', 'gruppe': 'unreg',
        'pres': ['digo', 'dizes', 'diz', 'dizemos', 'dizem'],
        'perf': ['disse', 'disseste', 'disse', 'dissemos', 'disseram'],
        'imp':  ['dizia', 'dizias', 'dizia', 'dizíamos', 'diziam'],
        'cond': ['diria', 'dirias', 'diria', 'diríamos', 'diriam'],
        'hinweis': 'eu disse und ele disse sind gleich. Die würde-Form kommt vom Kurzstamm dir-, also diria.',
    },
    'ver': {
        'de': 'sehen', 'gruppe': 'unreg',
        'pres': ['vejo', 'vês', 'vê', 'vemos', 'veem'],
        'perf': ['vi', 'viste', 'viu', 'vimos', 'viram'],
        'imp':  ['via', 'vias', 'via', 'víamos', 'viam'],
        'cond': ['veria', 'verias', 'veria', 'veríamos', 'veriam'],
        'hinweis': 'vemos (Gegenwart) und vimos (Vergangenheit) leicht zu verwechseln.',
    },
    'dar': {
        'de': 'geben', 'gruppe': 'unreg',
        'pres': ['dou', 'dás', 'dá', 'damos', 'dão'],
        'perf': ['dei', 'deste', 'deu', 'demos', 'deram'],
        'imp':  ['dava', 'davas', 'dava', 'dávamos', 'davam'],
        'cond': ['daria', 'darias', 'daria', 'daríamos', 'dariam'],
        'hinweis': '',
    },
    'poder': {
        'de': 'können, dürfen', 'gruppe': 'unreg',
        'pres': ['posso', 'podes', 'pode', 'podemos', 'podem'],
        'perf': ['pude', 'pudeste', 'pôde', 'pudemos', 'puderam'],
        'imp':  ['podia', 'podias', 'podia', 'podíamos', 'podiam'],
        'cond': ['poderia', 'poderias', 'poderia', 'poderíamos', 'poderiam'],
        'hinweis': 'pôde für er konnte trägt ein Dach, sonst wäre es nicht von pode, er kann, zu unterscheiden.',
    },
    'querer': {
        'de': 'wollen', 'gruppe': 'unreg',
        'pres': ['quero', 'queres', 'quer', 'queremos', 'querem'],
        'perf': ['quis', 'quiseste', 'quis', 'quisemos', 'quiseram'],
        'imp':  ['queria', 'querias', 'queria', 'queríamos', 'queriam'],
        'cond': ['quereria', 'quererias', 'quereria', 'quereríamos', 'quereriam'],
        'hinweis': 'queria heißt im Alltag ich hätte gern: queria um café, por favor.',
    },
    'saber': {
        'de': 'wissen, können (gelernt)', 'gruppe': 'unreg',
        'pres': ['sei', 'sabes', 'sabe', 'sabemos', 'sabem'],
        'perf': ['soube', 'soubeste', 'soube', 'soubemos', 'souberam'],
        'imp':  ['sabia', 'sabias', 'sabia', 'sabíamos', 'sabiam'],
        'cond': ['saberia', 'saberias', 'saberia', 'saberíamos', 'saberiam'],
        'hinweis': 'saber plus Grundform heißt etwas gelernt haben: sei nadar, ich kann schwimmen.',
    },
    'pôr': {
        'de': 'legen, setzen, stellen', 'gruppe': 'unreg',
        'pres': ['ponho', 'pões', 'põe', 'pomos', 'põem'],
        'perf': ['pus', 'puseste', 'pôs', 'pusemos', 'puseram'],
        'imp':  ['punha', 'punhas', 'punha', 'púnhamos', 'punham'],
        'cond': ['poria', 'porias', 'poria', 'poríamos', 'poriam'],
        'hinweis': 'Das einzige Verb auf -ôr. Steckt auch in compor, dispor und supor.',
    },
    'trazer': {
        'de': 'bringen, mitbringen', 'gruppe': 'unreg',
        'pres': ['trago', 'trazes', 'traz', 'trazemos', 'trazem'],
        'perf': ['trouxe', 'trouxeste', 'trouxe', 'trouxemos', 'trouxeram'],
        'imp':  ['trazia', 'trazias', 'trazia', 'trazíamos', 'traziam'],
        'cond': ['traria', 'trarias', 'traria', 'traríamos', 'trariam'],
        'hinweis': 'trouxe wird trosse gesprochen. Die würde-Form kommt vom Kurzstamm trar-, also traria.',
    },

    # ===================== MUSTER FÜR REGELMÄSSIGE =====================
    'falar': {
        'de': 'sprechen, reden', 'gruppe': 'muster', 'muster': '-ar',
        'pres': ['falo', 'falas', 'fala', 'falamos', 'falam'],
        'perf': ['falei', 'falaste', 'falou', 'falámos', 'falaram'],
        'imp':  ['falava', 'falavas', 'falava', 'falávamos', 'falavam'],
        'cond': ['falaria', 'falarias', 'falaria', 'falaríamos', 'falariam'],
        'hinweis': 'Muster für alle Verben auf -ar. In Portugal falámos mit Akzent, in Brasilien ohne.',
    },
    'comer': {
        'de': 'essen', 'gruppe': 'muster', 'muster': '-er',
        'pres': ['como', 'comes', 'come', 'comemos', 'comem'],
        'perf': ['comi', 'comeste', 'comeu', 'comemos', 'comeram'],
        'imp':  ['comia', 'comias', 'comia', 'comíamos', 'comiam'],
        'cond': ['comeria', 'comerias', 'comeria', 'comeríamos', 'comeriam'],
        'hinweis': 'Muster für alle Verben auf -er. comemos ist Gegenwart und Vergangenheit zugleich.',
    },
    'partir': {
        'de': 'abfahren, losgehen', 'gruppe': 'muster', 'muster': '-ir',
        'pres': ['parto', 'partes', 'parte', 'partimos', 'partem'],
        'perf': ['parti', 'partiste', 'partiu', 'partimos', 'partiram'],
        'imp':  ['partia', 'partias', 'partia', 'partíamos', 'partiam'],
        'cond': ['partiria', 'partirias', 'partiria', 'partiríamos', 'partiriam'],
        'hinweis': 'Muster für alle Verben auf -ir. partimos ist Gegenwart und Vergangenheit zugleich.',
    },

    # ===================== NUR DIE ICH-FORM IST UNREGELMÄSSIG =====================
    'ler': {
        'de': 'lesen', 'gruppe': 'eu',
        'pres': ['leio', 'lês', 'lê', 'lemos', 'leem'],
        'perf': ['li', 'leste', 'leu', 'lemos', 'leram'],
        'imp':  ['lia', 'lias', 'lia', 'líamos', 'liam'],
        'cond': ['leria', 'lerias', 'leria', 'leríamos', 'leriam'],
        'hinweis': '',
    },
    'perder': {
        'de': 'verlieren, verpassen', 'gruppe': 'eu',
        'pres': ['perco', 'perdes', 'perde', 'perdemos', 'perdem'],
        'perf': ['perdi', 'perdeste', 'perdeu', 'perdemos', 'perderam'],
        'imp':  ['perdia', 'perdias', 'perdia', 'perdíamos', 'perdiam'],
        'cond': ['perderia', 'perderias', 'perderia', 'perderíamos', 'perderiam'],
        'hinweis': 'Nur die Ich-Form fällt aus der Reihe: perco statt perdo.',
    },
    'ouvir': {
        'de': 'hören', 'gruppe': 'eu',
        'pres': ['ouço', 'ouves', 'ouve', 'ouvimos', 'ouvem'],
        'perf': ['ouvi', 'ouviste', 'ouviu', 'ouvimos', 'ouviram'],
        'imp':  ['ouvia', 'ouvias', 'ouvia', 'ouvíamos', 'ouviam'],
        'cond': ['ouviria', 'ouvirias', 'ouviria', 'ouviríamos', 'ouviriam'],
        'hinweis': 'ouço mit ç.',
    },
    'pedir': {
        'de': 'bitten, bestellen', 'gruppe': 'eu',
        'pres': ['peço', 'pedes', 'pede', 'pedimos', 'pedem'],
        'perf': ['pedi', 'pediste', 'pediu', 'pedimos', 'pediram'],
        'imp':  ['pedia', 'pedias', 'pedia', 'pedíamos', 'pediam'],
        'cond': ['pediria', 'pedirias', 'pediria', 'pediríamos', 'pediriam'],
        'hinweis': 'peço mit ç. Nicht mit perguntar (nach etwas fragen) verwechseln.',
    },
    'dormir': {
        'de': 'schlafen', 'gruppe': 'eu',
        'pres': ['durmo', 'dormes', 'dorme', 'dormimos', 'dormem'],
        'perf': ['dormi', 'dormiste', 'dormiu', 'dormimos', 'dormiram'],
        'imp':  ['dormia', 'dormias', 'dormia', 'dormíamos', 'dormiam'],
        'cond': ['dormiria', 'dormirias', 'dormiria', 'dormiríamos', 'dormiriam'],
        'hinweis': 'Ich-Form mit u: durmo.',
    },
    'sair': {
        'de': 'rausgehen, weggehen', 'gruppe': 'eu',
        'pres': ['saio', 'sais', 'sai', 'saímos', 'saem'],
        'perf': ['saí', 'saíste', 'saiu', 'saímos', 'saíram'],
        'imp':  ['saía', 'saías', 'saía', 'saíamos', 'saíam'],
        'cond': ['sairia', 'sairias', 'sairia', 'sairíamos', 'sairiam'],
        'hinweis': 'sair de casa (aus dem Haus gehen), sair para (losgehen nach).',
    },
    'conhecer': {
        'de': 'kennen, kennenlernen', 'gruppe': 'eu',
        'pres': ['conheço', 'conheces', 'conhece', 'conhecemos', 'conhecem'],
        'perf': ['conheci', 'conheceste', 'conheceu', 'conhecemos', 'conheceram'],
        'imp':  ['conhecia', 'conhecias', 'conhecia', 'conhecíamos', 'conheciam'],
        'cond': ['conheceria', 'conhecerias', 'conheceria', 'conheceríamos', 'conheceriam'],
        'hinweis': 'conheço mit ç. conhecer für Personen und Orte, saber für Fakten.',
    },
    'esquecer': {
        'de': 'vergessen', 'gruppe': 'eu',
        'pres': ['esqueço', 'esqueces', 'esquece', 'esquecemos', 'esquecem'],
        'perf': ['esqueci', 'esqueceste', 'esqueceu', 'esquecemos', 'esqueceram'],
        'imp':  ['esquecia', 'esquecias', 'esquecia', 'esquecíamos', 'esqueciam'],
        'cond': ['esqueceria', 'esquecerias', 'esqueceria', 'esqueceríamos', 'esqueceriam'],
        'hinweis': 'esqueço mit ç. Meist reflexiv: esqueço-me de (ich vergesse).',
    },
    'conseguir': {
        'de': 'schaffen, hinbekommen', 'gruppe': 'eu',
        'pres': ['consigo', 'consegues', 'consegue', 'conseguimos', 'conseguem'],
        'perf': ['consegui', 'conseguiste', 'conseguiu', 'conseguimos', 'conseguiram'],
        'imp':  ['conseguia', 'conseguias', 'conseguia', 'conseguíamos', 'conseguiam'],
        'cond': ['conseguiria', 'conseguirias', 'conseguiria', 'conseguiríamos', 'conseguiriam'],
        'hinweis': 'consigo heißt ich bringe es zustande. posso heißt ich darf oder ich habe die Möglichkeit.',
    },
    'sentir': {
        'de': 'fühlen, spüren', 'gruppe': 'eu',
        'pres': ['sinto', 'sentes', 'sente', 'sentimos', 'sentem'],
        'perf': ['senti', 'sentiste', 'sentiu', 'sentimos', 'sentiram'],
        'imp':  ['sentia', 'sentias', 'sentia', 'sentíamos', 'sentiam'],
        'cond': ['sentiria', 'sentirias', 'sentiria', 'sentiríamos', 'sentiriam'],
        'hinweis': 'Meist reflexiv: sinto-me bem (ich fühle mich gut).',
    },
    'preferir': {
        'de': 'lieber mögen, vorziehen', 'gruppe': 'eu',
        'pres': ['prefiro', 'preferes', 'prefere', 'preferimos', 'preferem'],
        'perf': ['preferi', 'preferiste', 'preferiu', 'preferimos', 'preferiram'],
        'imp':  ['preferia', 'preferias', 'preferia', 'preferíamos', 'preferiam'],
        'cond': ['preferiria', 'preferirias', 'preferiria', 'preferiríamos', 'prefeririam'],
        'hinweis': 'Ich-Form mit i: prefiro.',
    },
}

# ===================== REFLEXIVE VERBEN =====================
# Eigene Struktur, weil hier nicht die Form das Problem ist, sondern die Stellung
# des Pronomens. Deshalb je Person zwei Varianten:
#   'nach' = Standard, Pronomen hängt hinten am Verb (chamo-me)
#   'vor'  = nach einem Auslöser, Pronomen steht vor dem Verb (não me chamo)
PRONOMEN = ['me', 'te', 'se', 'nos', 'se']

REFLEXIVE = {
    'chamar-se': {
        'de': 'heißen',
        'nach': ['chamo-me', 'chamas-te', 'chama-se', 'chamamo-nos', 'chamam-se'],
        'vor':  ['me chamo', 'te chamas', 'se chama', 'nos chamamos', 'se chamam'],
        'hinweis': 'Bei "wir" fällt das s weg: chamamo-nos, nicht chamamos-nos.',
    },
    'levantar-se': {
        'de': 'aufstehen',
        'nach': ['levanto-me', 'levantas-te', 'levanta-se', 'levantamo-nos', 'levantam-se'],
        'vor':  ['me levanto', 'te levantas', 'se levanta', 'nos levantamos', 'se levantam'],
        'hinweis': 'Bei "wir" fällt das s weg: levantamo-nos.',
    },
    'deitar-se': {
        'de': 'sich hinlegen, schlafen gehen',
        'nach': ['deito-me', 'deitas-te', 'deita-se', 'deitamo-nos', 'deitam-se'],
        'vor':  ['me deito', 'te deitas', 'se deita', 'nos deitamos', 'se deitam'],
        'hinweis': 'Bei "wir" fällt das s weg: deitamo-nos.',
    },
    'esquecer-se': {
        'de': 'vergessen',
        'nach': ['esqueço-me', 'esqueces-te', 'esquece-se', 'esquecemo-nos', 'esquecem-se'],
        'vor':  ['me esqueço', 'te esqueces', 'se esquece', 'nos esquecemos', 'se esquecem'],
        'hinweis': 'Ich-Form mit ç: esqueço. Steht immer mit de: esqueço-me das chaves.',
    },
    'lembrar-se': {
        'de': 'sich erinnern',
        'nach': ['lembro-me', 'lembras-te', 'lembra-se', 'lembramo-nos', 'lembram-se'],
        'vor':  ['me lembro', 'te lembras', 'se lembra', 'nos lembramos', 'se lembram'],
        'hinweis': 'Steht immer mit de: lembro-me disso.',
    },
    'sentir-se': {
        'de': 'sich fühlen',
        'nach': ['sinto-me', 'sentes-te', 'sente-se', 'sentimo-nos', 'sentem-se'],
        'vor':  ['me sinto', 'te sentes', 'se sente', 'nos sentimos', 'se sentem'],
        'hinweis': 'Ich-Form mit i: sinto. Bei "wir" fällt das s weg: sentimo-nos.',
    },
}

# Wörter, nach denen das Pronomen vor das Verb rutscht
AUSLOESER = ['não', 'nunca', 'sempre', 'também', 'já', 'só', 'que', 'quem', 'ninguém',
             'como', 'quando', 'onde', 'porque']

ZEIT_NAMEN = {
    'pres': 'Gegenwart',
    'perf': 'Vergangenheit',
    'imp':  'Erzählvergangenheit',
    'cond': 'würde-Form',
}
ZEIT_LANG = {
    'pres': 'Presente',
    'perf': 'Pretérito Perfeito',
    'imp':  'Pretérito Imperfeito',
    'cond': 'Condicional',
}


def selbsttest():
    """
    Prüft die Datenbank auf Vollständigkeit und auf Verstöße gegen Regeln,
    die im Portugiesischen ausnahmslos gelten. Findet vor allem vergessene Akzente.
    """
    probleme = []
    for inf, v in VERBEN.items():
        if not v.get('de'):
            probleme.append(f'{inf}: keine Übersetzung')

        for zeit in ('pres', 'perf', 'imp', 'cond'):
            formen = v.get(zeit)
            if not formen:
                probleme.append(f'{inf}: {zeit} fehlt')
                continue
            if len(formen) != 5:
                probleme.append(f'{inf}/{zeit}: {len(formen)} Formen statt 5')
                continue
            if any(not f or not f.strip() for f in formen):
                probleme.append(f'{inf}/{zeit}: leere Form')
            if len(set(formen)) < 3:
                probleme.append(f'{inf}/{zeit}: verdächtig wenige verschiedene Formen ({formen})')

        # Regel 1: Konditional endet ausnahmslos auf -ia/-ias/-ia/-íamos/-iam
        cond = v.get('cond') or []
        if len(cond) == 5:
            erwartet = ('ia', 'ias', 'ia', 'íamos', 'iam')
            for form, end in zip(cond, erwartet):
                if not form.endswith(end):
                    probleme.append(f'{inf}/cond: "{form}" endet nicht auf -{end}')
            if cond[0] != cond[2]:
                probleme.append(f'{inf}/cond: eu und ele müssen gleich sein ({cond[0]} vs {cond[2]})')

        # Regel 2: Imperfeito endet auf -va.../-ia..., nós trägt IMMER einen Akzent
        imp = v.get('imp') or []
        if len(imp) == 5 and not any(z in imp[3] for z in 'áéíóúâêô'):
            probleme.append(f'{inf}/imp: nós-Form "{imp[3]}" ohne Akzent, erwartet z. B. -ávamos/-íamos')

        # Regel 3: Imperfeito hat eu == ele (gilt für alle Verben, auch ser/ter/vir/pôr)
        if len(imp) == 5 and imp[0] != imp[2]:
            probleme.append(f'{inf}/imp: eu und ele müssen gleich sein ({imp[0]} vs {imp[2]})')

        # Regel 4: bei regelmäßigen -ar-Verben trägt die nós-Form im Perfeito in pt-PT den Akzent
        perf = v.get('perf') or []
        if v.get('muster') == '-ar' and len(perf) == 5 and 'á' not in perf[3]:
            probleme.append(f'{inf}/perf: nós-Form "{perf[3]}" braucht in pt-PT den Akzent (falámos)')

    # ---- Reflexive Verben ----
    for inf, r in REFLEXIVE.items():
        for schluessel in ('nach', 'vor'):
            formen = r.get(schluessel)
            if not formen or len(formen) != 5:
                probleme.append(f'{inf}/{schluessel}: nicht 5 Formen')
                continue
            if any(not f.strip() for f in formen):
                probleme.append(f'{inf}/{schluessel}: leere Form')

        nach, vor = r.get('nach') or [], r.get('vor') or []
        if len(nach) == 5 and len(vor) == 5:
            # nachgestellt: muss einen Bindestrich haben
            for i, f in enumerate(nach):
                if '-' not in f:
                    probleme.append(f'{inf}/nach[{PERSONEN[i]}]: "{f}" ohne Bindestrich')
            # vorangestellt: darf keinen Bindestrich haben und beginnt mit dem Pronomen
            for i, f in enumerate(vor):
                if '-' in f:
                    probleme.append(f'{inf}/vor[{PERSONEN[i]}]: "{f}" darf keinen Bindestrich haben')
                if not f.startswith(PRONOMEN[i] + ' '):
                    probleme.append(f'{inf}/vor[{PERSONEN[i]}]: "{f}" beginnt nicht mit "{PRONOMEN[i]}"')
            # nós nachgestellt: das s des Verbs fällt weg, die Form endet auf -mo-nos
            if not nach[3].endswith('mo-nos'):
                probleme.append(f'{inf}/nach[nós]: "{nach[3]}" muss auf -mo-nos enden (das s fällt weg)')
            # die reine Verbform muss in beiden Varianten dieselbe sein
            for i in range(5):
                v_nach = nach[i].split('-')[0]
                v_vor = vor[i].split(' ', 1)[1] if ' ' in vor[i] else ''
                if i != 3 and v_nach != v_vor:
                    probleme.append(f'{inf}[{PERSONEN[i]}]: Verbform weicht ab ({v_nach} vs {v_vor})')

    return probleme


if __name__ == '__main__':
    p = selbsttest()
    print(f'{len(VERBEN)} Verben, {len(VERBEN) * 4 * 5} Einzelformen')
    if p:
        print('PROBLEME:')
        for x in p:
            print('  -', x)
    else:
        print('Selbsttest bestanden: alle Zeiten vollständig, 5 Personen je Zeit.')
    for gruppe in ('top', 'unreg', 'muster', 'eu'):
        namen = [k for k, v in VERBEN.items() if v['gruppe'] == gruppe]
        print(f'  {gruppe:7s} ({len(namen):2d}): {", ".join(namen)}')
