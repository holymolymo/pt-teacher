#!/usr/bin/env python3
"""
Kategorisiert alle Vokabeln in 7 thematische Packs für Lengo:
- verben, adjektive, nomen, redewendungen, fragen, umgangssprache, grammatik

Nutzt Sektions-Header aus _generator.py, um bestehende Karten zu kategorisieren.
Fügt neue Karten aus den Klassen 15.07 / 17.07 / 24.07 explizit kategorisiert an.
"""
import csv
import os
import re
import unicodedata

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATOR_PATH = os.path.join(OUTPUT_DIR, '_generator.py')

# --- SEKTIONS-HEADER → KATEGORIE ---
# Ordnet die 55+ Sektionen im _generator.py zu einer der 7 Kategorien
SECTION_TO_CAT = {
    'BEGRÜSSUNG & BASICS':          'redewendungen',
    'PRONOMEN':                     'grammatik',
    'VORSTELLEN':                   'redewendungen',
    'FRAGEWÖRTER':                  'fragen',
    'SER (sein, dauerhaft)':        'verben',
    'ESTAR (sein, vorübergehend)':  'verben',
    'TER (haben)':                  'verben',
    'IR (gehen)':                   'verben',
    'VIR (kommen)':                 'verben',
    'BERUFE':                       'nomen',
    'ESTADO CIVIL':                 'nomen',
    'FAMILIE':                      'nomen',
    'POSSESSIV':                    'grammatik',
    'KONTRAKTIONEN':                'grammatik',
    'VERBEN -AR':                   'verben',
    'VERBEN -ER':                   'verben',
    'VERBEN -IR':                   'verben',
    'HÄUFIGKEIT & ZEIT':            'grammatik',
    'WOCHENTAGE':                   'nomen',
    'UHRZEIT':                      'redewendungen',
    'ORTE':                         'nomen',
    'RICHTUNG / DISTANZ':           'grammatik',
    'BESCHREIBUNG (Adjektive)':     'adjektive',
    'KÖRPER':                       'nomen',
    'KLEIDUNG':                     'nomen',
    'FARBEN':                       'adjektive',
    'ESSEN & TRINKEN':              'nomen',
    'FRÜCHTE':                      'nomen',
    'ESTAR + COM (Gefühle/Bedürfnisse)': 'redewendungen',
    'GEFÜHLE / ZUSTÄNDE':           'adjektive',
    'VERLAUFSFORM':                 'grammatik',
    'ZUKUNFT (ir + Inf)':           'grammatik',
    'VERGANGENHEIT (Pretérito Perfeito)': 'verben',
    'IMPERFEITO (durative Vergangenheit)': 'verben',
    'KONDITIONAL':                  'verben',
    'MODALVERBEN-AUSDRÜCKE':        'grammatik',
    'VERBINDUNGEN / FÜLLER':        'grammatik',
    'PRONOMEN MIT PRÄPOSITION':     'grammatik',
    'KONVERSATION':                 'redewendungen',
    'SPRÜCHE / IDIOME':             'redewendungen',
    'BUSINESS / ARBEIT':            'nomen',
    'SPORT':                        'nomen',
    'LERNEN':                       'nomen',
    'ESSEN & SOZIALES':             'redewendungen',
    'WETTER':                       'redewendungen',
    'NATUR':                        'nomen',
    'ZUHAUSE':                      'nomen',
    'VERSCHIEDENES':                'redewendungen',
    # Klassen (alt) — heuristisch aufteilen
    'Klasse 20.05.2026 — Valencia':                        'MIXED',
    'Klasse 27.05.2026 — Verspätung, Schmerz, Konditional, se': 'MIXED',
    'Buch — Konjugação pronominal reflexa (Stellung der Pronomen)': 'grammatik',
    'Klasse 03.06.2026 — Business-Plan, Restaurant, Fast Food':   'MIXED',
    'Klasse 10.06.2026 — Wasserfall, Stromausfall, Partys, Beziehungen': 'MIXED',
    'Klasse 17.06.2026 — Coworking, Filme, Fußball':       'MIXED',
}

def heuristic_category(pt, de):
    """Für MIXED-Sektionen: rate anhand der Form der Karte."""
    pt_lower = pt.lower().strip()
    de_lower = de.lower().strip()
    # Verben: enden auf -ar/-er/-ir/-or (nur einzelnes Wort)
    if re.match(r'^[a-zçãáéíóúâêôàõü-]+(-se)?$', pt_lower) and pt_lower.endswith(('ar', 'er', 'ir', 'or', 'ar-se', 'er-se', 'ir-se')):
        return 'verben'
    # Slang
    if any(w in pt_lower for w in ('foda', 'porra', 'merda', 'caralho')):
        return 'umgangssprache'
    # Fragen
    if pt.strip().endswith('?'):
        return 'fragen'
    # Adjektive: enden auf -o/-a und Deutsch beginnt mit "sein" oder ist kurz
    if re.match(r'^[a-zçãáéíóúâêôàõü]+[oa]$', pt_lower) and (len(de_lower) < 15 or de_lower.startswith('sein')):
        return 'adjektive'
    # Redewendungen: mehrere Wörter, Satzbau
    if ' ' in pt.strip() and len(pt.strip().split()) >= 2:
        return 'redewendungen'
    # Fallback: nomen
    return 'nomen'


# --- NEUE KARTEN AUS 3 KLASSEN (explizit kategorisiert) ---
NEW_CARDS = [
    # === Klasse 15.07.2026 ===
    # Verben
    ('Olhar', 'schauen (auf etwas)', 'V: olhar para', 'verben'),
    ('Ouvir', 'hören', 'eu ouço', 'verben'),
    ('Escutar', 'zuhören / lauschen', 'eu escuto todos os dias', 'verben'),
    ('Entender', 'verstehen', '', 'verben'),
    ('Compreender', 'verstehen (Synonym)', '', 'verben'),
    ('Pedir', 'bitten / bestellen', 'eu peço', 'verben'),
    ('Conseguir', 'schaffen / hinbekommen', 'eu consigo', 'verben'),
    ('Diferenciar', 'unterscheiden', 'diferenciar espanhol de português', 'verben'),
    ('Ficar em forma', 'in Form bleiben', '', 'verben'),
    # Nomen
    ('Complicação / Complicações', 'Komplikation(en)', 'muitas complicações com o negócio', 'nomen'),
    ('Falha humana / Falhas humanas', 'menschliche(r) Fehler', '', 'nomen'),
    ('Lei / Leis', 'Gesetz(e)', '', 'nomen'),
    ('Regulamentos', 'Regulierungen', '', 'nomen'),
    ('Relatório', 'Bericht', '', 'nomen'),
    ('Consistência', 'Konsistenz / Beständigkeit', 'a consistência é o mais importante', 'nomen'),
    ('Coração', 'Herz', 'coração acelera', 'nomen'),
    ('Zona', 'Zone (auch Puls-Zone)', 'zona 0/1/2 (Puls beim Laufen)', 'nomen'),
    ('Corrida', 'Lauf / Rennen', 'corri 12 km', 'nomen'),
    ('Caminhada', 'Spaziergang', '', 'nomen'),
    # Adjektive
    ('Estranho / Estranha', 'seltsam', 'é muito estranho', 'adjektive'),
    ('Tranquilo / Tranquila', 'ruhig', 'seu coração fica tranquilo', 'adjektive'),
    ('Parecido / Parecida', 'ähnlich', 'línguas parecidas', 'adjektive'),
    # Redewendungen
    ('Vai e vem', 'Hin und Her', 'muito vai e vem com a lei', 'redewendungen'),
    ('Fora + Nomen', 'außer / außerhalb', 'fora os negócios (außer dem Geschäft)', 'redewendungen'),
    ('Na verdade', 'eigentlich / tatsächlich', 'na verdade eu tenho treinado muito', 'redewendungen'),
    ('Ultimamente', 'kürzlich / in letzter Zeit', 'eu treino muito ultimamente', 'redewendungen'),
    ('Enquanto', 'während', 'enquanto corres', 'grammatik'),
    ('Vi / Assisti o jogo', 'sah / schaute das Spiel an', 'ver = sehen, assistir = anschauen (Film/Serie)', 'redewendungen'),
    ('Sim, vi / Sim, assisti', 'ja, ich sah / ich schaute an', '', 'redewendungen'),
    ('Ajuda a aprender', 'hilft beim Lernen', 'ouvir espanhol ajuda a aprender português', 'redewendungen'),

    # === Klasse 17.07.2026 ===
    # Verben
    ('Acelerar', 'beschleunigen', 'o coração acelera', 'verben'),
    ('Tentar', 'versuchen', 'eu tento', 'verben'),
    ('Concordar', 'zustimmen', 'eu concordo', 'verben'),
    ('Defender-se', 'sich verteidigen', 'reflexiv! me defendo', 'verben'),
    # Nomen
    ('Punho / Punhos', 'Faust / Fäuste', 'Kampfsport', 'nomen'),
    ('Cotovelo / Cotovelos', 'Ellbogen', '', 'nomen'),
    ('Joelho / Joelhos', 'Knie', '', 'nomen'),
    ('Pontapé / Pontapés', 'Tritt / Tritte', '', 'nomen'),
    ('Cenário', 'Szenario', 'num cenário da vida real', 'nomen'),
    ('Luta', 'Kampf', '', 'nomen'),
    ('Confronto', 'Konfrontation', 'confronto de rua', 'nomen'),
    ('Sucesso', 'Erfolg', 'com muito sucesso', 'nomen'),
    ('Desporto de combate', 'Kampfsport', '', 'nomen'),
    ('Confiança', 'Vertrauen / Selbstvertrauen', 'dá confiança', 'nomen'),
    ('Karaté', 'Karate', '', 'nomen'),
    ('Capoeira', 'Capoeira', '', 'nomen'),
    ('Basquetebol', 'Basketball', '', 'nomen'),
    ('Palavrão / Palavrões', 'Schimpfwort / Schimpfwörter', '', 'nomen'),
    ('Gíria / Gírias', 'Slang', 'aprender gírias em português', 'nomen'),
    ('Tarefa', 'Aufgabe', 'não tive tempo para fazer minha tarefa', 'nomen'),
    ('Alguém / Uma pessoa', 'jemand / eine Person', '', 'nomen'),
    # Adjektive
    ('Intenso / Intensa', 'intensiv', 'mais intenso do que Muay Thai', 'adjektive'),
    ('Infeliz / Infelizes', 'unglücklich', 'infelizes com a vida', 'adjektive'),
    ('Musculoso / Musculosa', 'muskulös', '', 'adjektive'),
    ('Burro / Burra', 'dumm', 'pessoas burras', 'adjektive'),
    # Redewendungen
    ('É permitido + Inf', 'es ist erlaubt zu ...', 'é permitido usar punhos', 'grammatik'),
    ('Do que', 'als (Vergleich)', 'mais X do que Y', 'grammatik'),
    ('Já + Perfeito', 'schon einmal', 'eu já tentei', 'grammatik'),
    ('Nunca + Perfeito', 'nie', 'eu nunca estive', 'grammatik'),
    ('Sem sentido', 'sinnlos', 'coisas sem sentido', 'redewendungen'),
    ('Sério?', 'ernsthaft?', '', 'redewendungen'),
    ('Estou a ver', 'ich verstehe / ich sehe (bildlich)', 'PT-PT Standard-Antwort', 'redewendungen'),
    ('Diga não à violência', 'Sag nein zur Gewalt', '', 'redewendungen'),
    ('Aproveitar', 'genießen', 'aproveite as tuas cervejas!', 'verben'),
    ('Desfrutar', 'genießen (Synonym)', '', 'verben'),
    # UMGANGSSPRACHE (NEU!)
    ('Foda-se', 'Fuck / Verdammt', 'sehr vulgär!', 'umgangssprache'),
    ('Que porra é essa', 'Was zum Fick ist das', 'sehr vulgär', 'umgangssprache'),
    ('Que merda é essa', 'Was zum Scheiß ist das', 'vulgär', 'umgangssprache'),
    ('Merda', 'Scheiße', 'vulgär, alltäglich', 'umgangssprache'),
    ('Caralho', 'Verdammt / Fick', 'sehr vulgär', 'umgangssprache'),

    # === Klasse 24.07.2026 ===
    # Verben
    ('Melhorar', 'besser werden / verbessern', 'vai melhorar', 'verben'),
    ('Aumentar', 'erhöhen / steigern', 'aumentar a distância', 'verben'),
    ('Construir', 'bauen', 'construir um forno', 'verben'),
    ('Focar (em)', 'sich fokussieren auf', 'devias focar em dois produtos', 'verben'),
    ('Testar', 'testen', '', 'verben'),
    ('Cozinhar', 'kochen', '', 'verben'),
    ('Preparar', 'vorbereiten', '', 'verben'),
    ('Praticar', 'üben', 'para praticar', 'verben'),
    ('Jogar', 'spielen (Sport / Spiel)', 'jogar futebol', 'verben'),
    ('Tocar', 'spielen (Instrument) / berühren', 'tocar guitarra', 'verben'),
    ('Brincar', 'spielen (Kinder)', 'crianças brincam', 'verben'),
    ('Pegar', 'nehmen / greifen', 'pegar um avião', 'verben'),
    ('Voar', 'fliegen', 'voar para Moçambique', 'verben'),
    ('Roubar', 'stehlen', 'roubar a tua ideia', 'verben'),
    # Nomen
    ('Dedo / Dedos', 'Finger / Zehen', '', 'nomen'),
    ('Distância', 'Entfernung', 'aumentar a distância', 'nomen'),
    ('Velocidade', 'Geschwindigkeit', 'aumentar a velocidade', 'nomen'),
    ('Treino', 'Training', 'teu treino', 'nomen'),
    ('Serralheiro', 'Schlosser', '', 'nomen'),
    ('Forno', 'Ofen', 'forno para pizza', 'nomen'),
    ('Hambúrguer', 'Hamburger', '', 'nomen'),
    ('Shawarma', 'Shawarma', '', 'nomen'),
    ('Congelador', 'Gefrierschrank', '', 'nomen'),
    ('Chapa', 'Grillplatte', 'chapa de hambúrguer', 'nomen'),
    ('Lugar', 'Ort / Platz', '', 'nomen'),
    ('Avião', 'Flugzeug', 'pegar um avião', 'nomen'),
    ('Console / Consolas', 'Konsole(n)', 'comprar consoles', 'nomen'),
    ('Fisio', 'Physio(therapie)', 'vou ter fisio', 'nomen'),
    # Redewendungen / Grammatik
    ('Abaixo de', 'unterhalb von', '', 'grammatik'),
    ('Em menos de', 'in weniger als', '', 'grammatik'),
    ('Enfim', 'jedenfalls / na gut', '', 'redewendungen'),
    ('Assim espero', 'das hoffe ich', '', 'redewendungen'),
    ('No início / No começo', 'am Anfang', '', 'redewendungen'),
    ('Muitas vezes', 'oft (viele Male)', '', 'redewendungen'),
    ('Devias + Inf', 'du solltest ...', 'Konditional, sehr häufig!', 'grammatik'),
    ('Tenho trabalhado muito', 'ich habe viel gearbeitet', 'Pretérito Perfeito Composto', 'grammatik'),
]


# --- HAUPT-LOGIK ---

def parse_generator():
    """Liest _generator.py und extrahiert (Sektion, pt, de, notiz) pro Karte."""
    with open(GENERATOR_PATH, 'r', encoding='utf-8') as f:
        source = f.read()

    # Nur die CARDS-Liste extrahieren
    m = re.search(r'CARDS\s*=\s*\[(.*?)^\]', source, re.DOTALL | re.MULTILINE)
    if not m:
        raise SystemExit('CARDS-Liste nicht gefunden')
    cards_block = m.group(1)

    lines = cards_block.split('\n')
    current_section = 'UNBEKANNT'
    cards = []

    # Karten-Pattern: ("pt", "de", "notiz"),
    card_re = re.compile(r'^\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)\s*,?\s*$')
    section_re = re.compile(r'^\s*#\s*===\s*(.+?)\s*===\s*$')

    for line in lines:
        sec = section_re.match(line)
        if sec:
            current_section = sec.group(1).strip()
            continue
        c = card_re.match(line)
        if c:
            pt, de, note = c.group(1), c.group(2), c.group(3)
            cards.append((current_section, pt, de, note))
    return cards


def normalize_key(s):
    s = s.strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[.!?,;:\'"\\/\(\)]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def main():
    old_cards = parse_generator()
    print(f'  Aus _generator.py: {len(old_cards)} Karten in {len(set(c[0] for c in old_cards))} Sektionen')

    # Kategorisieren
    by_cat = {c: [] for c in ('verben', 'adjektive', 'nomen', 'redewendungen', 'fragen', 'umgangssprache', 'grammatik')}
    unmapped_sections = set()

    for section, pt, de, note in old_cards:
        cat = SECTION_TO_CAT.get(section, 'MIXED')
        if cat == 'MIXED':
            cat = heuristic_category(pt, de)
        if cat not in by_cat:
            unmapped_sections.add(section)
            cat = 'redewendungen'
        by_cat[cat].append((pt, de, note))

    if unmapped_sections:
        print(f'  ⚠️  Sektionen ohne Mapping: {unmapped_sections}')

    # Neue Karten anhängen
    for pt, de, note, cat in NEW_CARDS:
        if cat not in by_cat:
            raise SystemExit(f'Unbekannte Kategorie in NEW_CARDS: {cat}')
        by_cat[cat].append((pt, de, note))

    # Dedup pro Kategorie
    total = 0
    for cat, cards in by_cat.items():
        seen = {}
        dedup = []
        for pt, de, note in cards:
            key = (normalize_key(pt), normalize_key(de))
            if key not in seen:
                seen[key] = True
                dedup.append((pt, de, note))
        by_cat[cat] = dedup
        total += len(dedup)

    # CSVs schreiben
    for cat, cards in by_cat.items():
        path = os.path.join(OUTPUT_DIR, f'vokabeln-{cat}.csv')
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            w.writerow(['Portugiesisch', 'Deutsch', 'Notiz'])
            for pt, de, note in cards:
                w.writerow([pt, de, note])
        print(f'  ✓ vokabeln-{cat}.csv ({len(cards)} Karten)')

    # Master (alles zusammen, dedupliziert)
    master_seen = {}
    master = []
    for cards in by_cat.values():
        for pt, de, note in cards:
            key = (normalize_key(pt), normalize_key(de))
            if key not in master_seen:
                master_seen[key] = True
                master.append((pt, de, note))

    master_path = os.path.join(OUTPUT_DIR, 'vokabeln-master.csv')
    with open(master_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(['Portugiesisch', 'Deutsch', 'Notiz'])
        for pt, de, note in master:
            w.writerow([pt, de, note])

    print(f'\n  Master: {len(master)} Karten')
    print(f'  Summe kategorisiert (mit Überschneidungen): {total}')

if __name__ == '__main__':
    main()
