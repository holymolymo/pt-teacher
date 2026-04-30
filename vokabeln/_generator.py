#!/usr/bin/env python3
"""
Generiert EINE saubere CSV-Datei für die Lengo-Vokabelapp.
Konsolidierte Liste — semantische Duplikate zusammengeführt, Beispielsätze
in Notizen verschoben statt als eigene Karten.
"""
import csv
import os
import re
import unicodedata

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Konsolidierte Karten — kuratiert von Hand:
# - Synonyme zusammengefasst (viver/morar)
# - Beispielsätze in Notizen verschoben
# - Wetter-Varianten gemerged
# - estar com X als 1 Pattern + Beispiele in Notiz
CARDS = [

    # === BEGRÜSSUNG & BASICS ===
    ("Bom dia", "Guten Morgen / Guten Tag", ""),
    ("Boa tarde", "Guten Nachmittag", ""),
    ("Boa noite", "Guten Abend / Gute Nacht", ""),
    ("Olá", "Hallo", ""),
    ("Por favor / Se faz favor", "bitte", ""),
    ("Obrigado / Obrigada", "danke (m / w)", "passt sich an Sprecher an!"),
    ("Sim / Não", "ja / nein", ""),

    # === PRONOMEN ===
    ("Eu", "ich", ""),
    ("Tu", "du (informell)", "in Brasilien selten, in Portugal Standard"),
    ("Você", "Sie / du (BR)", "formell PT, informell BR"),
    ("Ele / Ela", "er / sie", ""),
    ("Nós", "wir", ""),
    ("Vocês", "ihr / Sie (Plural)", ""),
    ("Eles / Elas", "sie (m+gemischt / nur w)", ""),

    # === VORSTELLEN ===
    ("Chamo-me Moritz", "Ich heiße Moritz", "chamar-se reflexiv"),
    ("Como te chamas?", "Wie heißt du? (informell)", "Como é que te chamas? = ausführlicher"),
    ("Qual é o seu nome?", "Wie heißen Sie? (formell)", ""),
    ("Meu nome é...", "Mein Name ist...", "Alternative zu chamar-se"),
    ("Sou da Alemanha", "Ich komme aus Deutschland", "ser + de"),
    ("Sou alemão", "Ich bin Deutscher", "Nationalität ohne Artikel"),
    ("Tenho 28 anos", "Ich bin 28 Jahre alt", "Achtung: ter (haben), nicht ser!"),
    ("Quantos anos tens?", "Wie alt bist du?", "alternative: Que idade tem?"),
    ("Sou empreendedor", "Ich bin Unternehmer", "Beruf ohne Artikel"),

    # === FRAGEWÖRTER ===
    ("Quem", "Wer", "nur für Personen"),
    ("Como", "Wie", ""),
    ("Qual / Quais", "Welche/r", "Auswahl aus mehreren"),
    ("O que / Que", "Was", "für Dinge, allgemein"),
    ("Onde", "Wo", ""),
    ("Quando", "Wann", ""),
    ("Quanto / Quantos", "Wie viel / Wie viele", ""),
    ("Porquê?", "Warum?", "Frage am Satzende"),
    ("Porque", "weil", "Antwort"),

    # === SER (sein, dauerhaft) ===
    ("Eu sou", "Ich bin", "ser - Identität"),
    ("Tu és", "Du bist", ""),
    ("Ele/Ela é", "Er/Sie ist", ""),
    ("Nós somos", "Wir sind", ""),
    ("Eles são", "Sie sind", ""),

    # === ESTAR (sein, vorübergehend) ===
    ("Eu estou", "Ich bin (gerade)", "estar - temporär"),
    ("Tu estás", "Du bist (gerade)", ""),
    ("Ele/Ela está", "Er/Sie ist (gerade)", ""),
    ("Nós estamos", "Wir sind (gerade)", ""),
    ("Eles estão", "Sie sind (gerade)", ""),

    # === TER (haben) ===
    ("Eu tenho", "Ich habe", "ter unregelmäßig"),
    ("Tu tens", "Du hast", ""),
    ("Ele/Ela tem", "Er/Sie hat", ""),
    ("Nós temos", "Wir haben", ""),
    ("Eles têm", "Sie haben", "mit Akzent!"),

    # === IR (gehen) ===
    ("Eu vou", "Ich gehe / werde", "ir + Inf = Zukunft"),
    ("Tu vais", "Du gehst", ""),
    ("Ele/Ela vai", "Er/Sie geht", ""),
    ("Nós vamos", "Wir gehen", ""),
    ("Eles vão", "Sie gehen", ""),

    # === VIR (kommen) ===
    ("Eu venho", "Ich komme", "vir unregelmäßig"),
    ("Tu vens", "Du kommst", ""),
    ("Ele/Ela vem", "Er/Sie kommt", ""),
    ("Nós vimos", "Wir kommen", ""),
    ("Eles vêm", "Sie kommen", ""),

    # === BERUFE ===
    ("Médico / Médica", "Arzt / Ärztin", "ohne Artikel: Sou médico"),
    ("Advogado / Advogada", "Anwalt / Anwältin", ""),
    ("Professor / Professora", "Lehrer / Lehrerin", ""),
    ("Engenheiro / Engenheira", "Ingenieur / Ingenieurin", ""),
    ("Tradutor / Tradutora", "Übersetzer / Übersetzerin", ""),
    ("Cantor / Cantora", "Sänger / Sängerin", ""),
    ("Pintor / Pintora", "Maler / Malerin", ""),
    ("Cabeleireiro / Cabeleireira", "Friseur / Friseurin", ""),
    ("Jornalista", "Journalist (gleich m/f)", ""),
    ("Dentista", "Zahnarzt (gleich m/f)", ""),
    ("Motorista", "Fahrer (gleich m/f)", ""),
    ("Estudante", "Student (gleich m/f)", ""),
    ("Empreendedor / Empreendedora", "Unternehmer / Unternehmerin", ""),

    # === ESTADO CIVIL ===
    ("Casado / Casada", "verheiratet", ""),
    ("Solteiro / Solteira", "ledig / single", ""),
    ("Divorciado / Divorciada", "geschieden", ""),
    ("Viúvo / Viúva", "verwitwet", ""),

    # === FAMILIE ===
    ("Pai", "Vater", ""),
    ("Mãe", "Mutter", ""),
    ("Pais", "Eltern", "ohne Akzent!"),
    ("País", "Land", "MIT Akzent — anderes Wort!"),
    ("Filho / Filha", "Sohn / Tochter", ""),
    ("Irmão / Irmã", "Bruder / Schwester", ""),
    ("Avó / Avô", "Großmutter / Großvater", ""),
    ("Namorado / Namorada", "Freund/in (Beziehung)", ""),

    # === POSSESSIV ===
    ("Meu / Minha", "mein/e", "passt zum BESITZ, nicht Besitzer"),
    ("Teu / Tua", "dein/e", "informell"),
    ("Seu / Sua", "sein / ihr / Ihr (formell)", "ggf. mit dele/dela präzisieren"),
    ("Nosso / Nossa", "unser/e", ""),
    ("Vosso / Vossa", "euer/e", "selten in PT-PT"),
    ("Dele / Dela", "von ihm / von ihr", "de + ele/ela"),

    # === KONTRAKTIONEN ===
    ("no / na / nos / nas", "in/im (em + Artikel)", "em+o=no, em+a=na"),
    ("do / da / dos / das", "vom/von (de + Artikel)", "de+o=do"),
    ("ao / à / aos / às", "zum/zur (a + Artikel)", "a+o=ao"),
    ("num / numa", "in einem/einer", "em+um, em+uma"),

    # === VERBEN -AR ===
    ("trabalhar", "arbeiten", "Trabalho com... / como..."),
    ("morar / viver", "wohnen / leben", "synonym; Moro/Vivo em Frankfurt"),
    ("estudar", "lernen / studieren", ""),
    ("falar", "sprechen / reden", ""),
    ("comprar", "kaufen", ""),
    ("apanhar", "nehmen / fangen", "z.B. metro, autocarro"),
    ("tomar", "nehmen / trinken", "Tomar café"),
    ("almoçar", "zu Mittag essen", "Achtung: ç!"),
    ("jantar", "zu Abend essen / Abendessen", ""),
    ("cozinhar", "kochen", ""),
    ("viajar", "reisen", ""),
    ("acordar", "aufwachen", ""),
    ("começar", "anfangen", "Comecei a escrever = ich begann zu schreiben"),
    ("chegar", "ankommen", ""),
    ("regressar / voltar / retornar", "zurückkehren", "drei Synonyme"),
    ("encontrar", "treffen / finden", ""),
    ("ganhar", "gewinnen / verdienen", ""),
    ("relaxar", "entspannen", ""),
    ("desestressar", "Stress abbauen", ""),
    ("caminhar / passear", "spazieren gehen", ""),

    # === VERBEN -ER ===
    ("comer", "essen", ""),
    ("beber", "trinken", ""),
    ("conhecer", "kennen", "eu conheço (mit ç!)"),
    ("aprender", "lernen", ""),
    ("compreender", "verstehen", "eu compreendo"),
    ("correr", "laufen / joggen", ""),
    ("escrever", "schreiben", ""),
    ("ver", "sehen", "eu vejo unregelmäßig"),
    ("dizer", "sagen", "eu digo"),
    ("fazer", "machen", "eu faço (mit ç!)"),
    ("ler", "lesen", "eu leio"),
    ("trazer", "bringen", "eu trago"),
    ("perder", "verlieren", "eu perco"),
    ("querer", "wollen", "eu quero"),
    ("poder", "können / dürfen", "eu posso"),
    ("saber", "wissen / können (gelernt)", "eu sei + Inf = Fähigkeit"),
    ("dever", "sollen / müssen", ""),
    ("dar", "geben", "eu dou"),

    # === VERBEN -IR ===
    ("partir", "abreisen", ""),
    ("abrir", "öffnen", ""),
    ("dividir", "teilen", ""),
    ("decidir", "entscheiden", ""),
    ("discutir", "diskutieren", ""),
    ("permitir", "erlauben", ""),
    ("admitir", "zugeben", ""),
    ("vestir", "anziehen", "eu visto (e→i!)"),
    ("servir", "servieren", "eu sirvo"),
    ("sentir", "fühlen", "eu sinto"),
    ("preferir", "bevorzugen", "eu prefiro"),
    ("conseguir", "schaffen / können", "eu consigo"),
    ("seguir", "folgen", "eu sigo"),
    ("corrigir", "korrigieren", "eu corrijo (g→j)"),
    ("dirigir", "fahren / leiten", "eu dirijo"),
    ("traduzir", "übersetzen", "ele traduz (3.Pers ohne -e)"),
    ("subir", "hinaufsteigen", "ele sobe (Vokalwechsel)"),
    ("dormir", "schlafen", "eu durmo"),
    ("fugir", "fliehen", "eu fujo"),
    ("rir", "lachen", ""),
    ("ouvir", "hören", "eu ouço (mit ç)"),
    ("pedir", "bitten", "eu peço"),
    ("sair", "rausgehen", "eu saio"),
    ("cair", "fallen", "eu caio"),
    ("construir", "bauen", "Construí uma casa"),
    ("mentir", "lügen", "eu minto"),
    ("descer", "hinuntergehen", "eu desço (mit ç!)"),
    ("esquecer-se", "vergessen", "eu esqueço-me; reflexiv konjugieren!"),

    # === HÄUFIGKEIT & ZEIT ===
    ("Sempre", "immer", ""),
    ("Nunca", "nie", ""),
    ("Às vezes", "manchmal", ""),
    ("Com frequência", "oft", ""),
    ("Quase", "fast / beinahe", ""),
    ("Poucas vezes", "selten", ""),
    ("Uma vez por semana", "einmal pro Woche", ""),
    ("Duas a três vezes por semana", "zwei bis drei Mal pro Woche", ""),
    ("Todos os dias", "jeden Tag", ""),
    ("Hoje / Ontem / Amanhã", "heute / gestern / morgen", ""),
    ("De manhã / De tarde / De noite", "morgens / nachmittags / abends", ""),
    ("Cedo / Tarde", "früh / spät", ""),
    ("Depois", "danach / später / dann", ""),
    ("Depois de", "nach (zeitlich)", "+ Substantiv/Infinitiv"),
    ("Antes / Antes de", "vorher / vor", ""),
    ("Agora", "jetzt", ""),
    ("Até agora", "bis jetzt", ""),
    ("De novo / Novamente", "wieder / nochmal", ""),
    ("Logo / Mais tarde", "gleich / später", ""),
    ("Última / Último", "letzte/r", "No último fim de semana"),

    # === WOCHENTAGE ===
    ("Segunda-feira", "Montag", ""),
    ("Terça-feira", "Dienstag", ""),
    ("Quarta-feira", "Mittwoch", ""),
    ("Quinta-feira", "Donnerstag", ""),
    ("Sexta-feira", "Freitag", ""),
    ("Sábado / Domingo", "Samstag / Sonntag", ""),
    ("Fim de semana", "Wochenende", ""),

    # === UHRZEIT ===
    ("Que horas são?", "Wie spät ist es?", ""),
    ("É uma hora", "Es ist 1 Uhr", "Singular!"),
    ("São duas horas", "Es ist 2 Uhr", "ab 2: São + Plural"),
    ("E meia / E um quarto", "halb / Viertel nach", ""),
    ("Meio-dia / Meia-noite", "Mittag / Mitternacht", ""),
    ("A que horas?", "Um wie viel Uhr?", "Antwort: às oito"),

    # === ORTE ===
    ("Em casa", "zu Hause", ""),
    ("No escritório", "im Büro", ""),
    ("Na rua", "auf der Straße", ""),
    ("Na praia", "am Strand", ""),
    ("No restaurante", "im Restaurant", ""),
    ("Cidade / Cidade natal", "Stadt / Heimatstadt", ""),
    ("Vila", "Dorf", "Viver na vila"),
    ("Faculdade / Universidade", "Hochschule / Universität", ""),
    ("Estação do comboio", "Bahnhof", "PT-PT (BR: estação de trem)"),
    ("Ginásio", "Fitnessstudio", ""),
    ("Sauna", "Sauna", ""),
    ("Terraço", "Dachterrasse", ""),
    ("Parque", "Park", ""),
    ("Floresta", "Wald", ""),
    ("Natureza", "Natur", "Na natureza"),

    # === RICHTUNG / DISTANZ ===
    ("Direito / À direita", "geradeaus / rechts", ""),
    ("À esquerda", "links", ""),
    ("Diretamente", "direkt", ""),
    ("Longe", "weit (weg)", ""),
    ("Perto", "nah / in der Nähe", ""),
    ("Aqui / Lá", "hier / dort", ""),
    ("Fora", "draußen", ""),
    ("Dentro", "drinnen", ""),

    # === BESCHREIBUNG (Adjektive) ===
    ("Alto / Baixo", "groß / klein", ""),
    ("Magro / Magra", "schlank / dünn", ""),
    ("Gordo / Gorda", "dick", ""),
    ("Forte", "stark", ""),
    ("Em forma", "in Form / fit", ""),
    ("Sarado", "muskulös / sportlich", "umgangssprachlich"),
    ("Bonito / Bonita", "schön", ""),
    ("Engraçado / Engraçada", "lustig", ""),
    ("Inteligente", "intelligent", ""),
    ("Ambicioso / Ambiciosa", "ehrgeizig", ""),
    ("Tranquilo / Tranquila", "ruhig", ""),
    ("Difícil / Fácil", "schwierig / einfach", ""),
    ("Cansativo", "anstrengend", ""),
    ("Cansado / Cansada", "müde", "Estou cansado"),
    ("Feliz / Triste", "glücklich / traurig", ""),
    ("Contente", "zufrieden / froh", ""),
    ("Saboroso", "schmackhaft", ""),
    ("Fresco / Fresca", "frisch", ""),
    ("Pesado / Pesada", "schwer / deftig (Essen)", ""),
    ("Salgado / Doce", "salzig / süß", ""),
    ("Subestimado / Subestimada", "unterschätzt", ""),
    ("Caro / Barato", "teuer / billig", ""),
    ("Delicioso", "köstlich", ""),
    ("Sozinho", "allein", "Eu vivo sozinho"),
    ("Careca", "Glatze / glatzköpfig", ""),
    ("Comprido", "lang", ""),
    ("Largo / Larga", "breit", ""),
    ("Preguiçoso / Preguiçosa", "faul", "Substantiv: preguiça"),

    # === KÖRPER ===
    ("Corpo", "Körper", "Todo o corpo = full body"),
    ("Cabeça", "Kopf", ""),
    ("Cabelo", "Haar", ""),
    ("Olhos", "Augen", "Olhos castanhos = braune Augen"),
    ("Pele", "Haut", "Secura na pele = trockene Haut"),
    ("Dentes", "Zähne", ""),
    ("Mão / Mãos", "Hand / Hände", ""),
    ("Dor / Dores", "Schmerz / Schmerzen", ""),

    # === KLEIDUNG ===
    ("Camisa", "Hemd", ""),
    ("Calças", "Hose", ""),
    ("Calções", "kurze Hose", ""),
    ("Casaco", "Jacke / Mantel", ""),
    ("Saia", "Rock", ""),
    ("Sapatos", "Schuhe", ""),
    ("Fato", "Anzug", ""),

    # === FARBEN ===
    ("Branco / Branca", "weiß", ""),
    ("Preto / Preta", "schwarz", ""),
    ("Vermelho / Vermelha", "rot", ""),
    ("Azul / Azuis", "blau (Sg/Pl)", ""),
    ("Verde", "grün", ""),
    ("Amarelo / Amarela", "gelb", ""),
    ("Castanho / Castanha", "braun", ""),
    ("Cinzento / Cinzenta", "grau", ""),
    ("Cor-de-laranja", "orange", ""),
    ("Cor-de-rosa", "rosa", ""),
    ("Louro / Loiro", "blond", ""),
    ("Dourado", "golden", ""),

    # === ESSEN & TRINKEN ===
    ("Comida", "Essen", "Comida favorita = Lieblingsessen"),
    ("Pequeno-almoço", "Frühstück", ""),
    ("Almoço / Jantar", "Mittagessen / Abendessen", ""),
    ("Café", "Kaffee", ""),
    ("Pão", "Brot", ""),
    ("Manteiga", "Butter", ""),
    ("Queijo / Queijos", "Käse", ""),
    ("Arroz", "Reis", ""),
    ("Massa", "Pasta / Nudeln", ""),
    ("Carne", "Fleisch", ""),
    ("Peixe", "Fisch", ""),
    ("Frango / Peito de frango", "Hähnchen / Hähnchenbrust", ""),
    ("Fígado", "Leber", ""),
    ("Feijão", "Bohnen", ""),
    ("Aveia", "Hafer", ""),
    ("Ovos", "Eier", ""),
    ("Cebola", "Zwiebel", ""),
    ("Alho", "Knoblauch", ""),
    ("Limão", "Zitrone", ""),
    ("Cenoura", "Karotte", ""),
    ("Batata / Batatas", "Kartoffel/n", ""),
    ("Pepino", "Gurke", ""),
    ("Temperos", "Gewürze", "Páprica, folha de louro..."),
    ("Sopa", "Suppe", ""),
    ("Bolo", "Kuchen", ""),
    ("Sushi", "Sushi", ""),
    ("Bitoque", "Bitoque (typisches PT-Gericht)", "Schweinefleisch + Reis + Pommes + Ei"),

    # === FRÜCHTE ===
    ("Fruta", "Frucht / Obst", ""),
    ("Morango", "Erdbeere", "Época de morango = Erdbeerzeit"),
    ("Ananás", "Ananas", "PT-PT (BR: abacaxi)"),
    ("Papaia", "Papaya", ""),
    ("Graviola", "Stachelannone", "tropische Frucht"),
    ("Maçã / Banana / Laranja", "Apfel / Banane / Orange", ""),

    # === ESTAR + COM (Gefühle/Bedürfnisse) ===
    ("Estou com fome", "Ich habe Hunger", "estar com + Substantiv"),
    ("Estou com sede", "Ich habe Durst", ""),
    ("Estou com sono", "Ich bin müde / schläfrig", ""),
    ("Estou com calor / frio", "Mir ist heiß / kalt", ""),
    ("Estou com medo", "Ich habe Angst", ""),
    ("Estou com saudades", "Ich habe Sehnsucht", "typisch portugiesisch!"),
    ("Estou com inveja", "Ich bin neidisch", ""),
    ("Estou com vontade de", "Ich habe Lust auf", "+ Inf/Substantiv"),
    ("Estou com dor de dentes", "Ich habe Zahnschmerzen", ""),

    # === GEFÜHLE / ZUSTÄNDE ===
    ("Estou bem", "Es geht mir gut", ""),
    ("Estou cheio", "Ich bin satt", ""),
    ("Estou cansado", "Ich bin müde", ""),
    ("Estou feliz", "Ich bin glücklich", ""),
    ("Me sinto muito bem", "Ich fühle mich sehr gut", "sentir-se reflexiv"),
    ("Muito bem disposto", "sehr gut gelaunt", ""),
    ("Diverti-me", "Ich hatte Spaß", "divertir-se"),
    ("Foi divertido / Foi fixe", "Es hat Spaß gemacht / Es war cool", "fixe = umgangssprachlich"),

    # === VERLAUFSFORM ===
    ("Estou a + Inf", "Ich bin gerade dabei zu...", "PT-PT (BR: -ndo Form)"),
    ("Estou a trabalhar", "Ich arbeite gerade", ""),
    ("Está a funcionar", "Es funktioniert (gerade)", ""),
    ("Está a chover", "Es regnet (gerade)", ""),
    ("O que estás a fazer agora?", "Was machst du gerade?", ""),

    # === ZUKUNFT (ir + Inf) ===
    ("Vou cozinhar", "Ich werde kochen", "ir + Inf"),
    ("Vou viajar amanhã", "Ich werde morgen reisen", ""),
    ("O que vais fazer?", "Was wirst du machen?", ""),
    ("Fazer a mala", "den Koffer packen", ""),

    # === VERGANGENHEIT (Pretérito Perfeito) ===
    ("Eu fui", "Ich war / ich ging", "ir/ser Pretérito"),
    ("Eu fiz", "Ich habe gemacht", "fazer Pretérito"),
    ("Eu tive", "Ich hatte", "ter Pretérito"),
    ("Eu estive", "Ich war (gerade)", "estar Pretérito"),
    ("Eu vi", "Ich habe gesehen", "ver Pretérito"),
    ("Eu disse", "Ich habe gesagt", "dizer Pretérito"),
    ("Eu fiquei", "Ich blieb", "ficar Pretérito"),
    ("Eu saí", "Ich ging raus", "sair Pretérito"),
    ("Eu comi / bebi", "Ich aß / trank", ""),
    ("Eu comprei", "Ich kaufte", ""),
    ("Eu cozinhei", "Ich kochte", ""),
    ("Eu treinei", "Ich trainierte", ""),
    ("Eu corri", "Ich lief / joggte", ""),
    ("Eu encontrei", "Ich traf", ""),
    ("Eu construí", "Ich baute", "construir"),
    ("Eu provei", "Ich probierte", ""),
    ("Eu notei", "Ich bemerkte", ""),
    ("Eles deram", "Sie gaben", "dar Pretérito"),
    ("Como foi o teu fim de semana?", "Wie war dein Wochenende?", ""),
    ("O que fizeste?", "Was hast du gemacht?", ""),
    ("O que tens feito?", "Was hast du so gemacht?", "Pretérito Perfeito Composto"),

    # === IMPERFEITO (durative Vergangenheit) ===
    ("Eu estava", "Ich war (Zustand)", "estar Imperfeito"),
    ("Eu tinha", "Ich hatte", "ter Imperfeito"),
    ("Eu era", "Ich war", "ser Imperfeito"),
    ("Quando era criança", "als ich Kind war", "typischer Imperfeito-Trigger"),
    ("Tinha sol", "Es war sonnig", "Imperfeito beim Wetter"),
    ("Estava ensolarado", "Es war sonnig", ""),
    ("Vivia em Portugal", "Ich lebte in Portugal", ""),

    # === KONDITIONAL ===
    ("Eu gostaria", "Ich würde gerne", "Konditional - höflich"),
    ("Queria", "Ich hätte gerne", "höflich beim Bestellen"),

    # === MODALVERBEN-AUSDRÜCKE ===
    ("Eu sei + Inf", "Ich kann + Inf (gelernt)", "Sei nadar = Ich kann schwimmen"),
    ("Posso + Inf", "Ich darf / kann + Inf", "Erlaubnis/Möglichkeit"),
    ("Eu tento + Inf", "Ich versuche + Inf", ""),
    ("Tenho que + Inf", "Ich muss + Inf", ""),
    ("Comecei a + Inf", "Ich habe angefangen zu...", "começar a"),
    ("Continuar a + Inf", "weiter machen", ""),

    # === VERBINDUNGEN / FÜLLER ===
    ("Mas", "aber", ""),
    ("Também", "auch", ""),
    ("Então", "also / dann", "Füllwort"),
    ("Por exemplo", "zum Beispiel", ""),
    ("Principalmente", "vor allem", ""),
    ("Infelizmente", "leider", ""),
    ("Felizmente", "zum Glück", ""),
    ("Assim", "so / auf diese Weise", ""),
    ("Quase", "fast", ""),
    ("Só / Apenas", "nur", ""),
    ("Já", "schon", ""),
    ("Ainda", "noch", ""),
    ("Para / Por", "für / durch", "Faustregel: para=Ziel, por=Grund"),

    # === PRONOMEN MIT PRÄPOSITION ===
    ("Comigo", "mit mir", ""),
    ("Contigo", "mit dir", ""),
    ("Connosco / Conosco", "mit uns", "PT-PT: connosco"),
    ("Convosco", "mit euch", ""),
    ("Para ti / Para si", "für dich / für Sie", ""),

    # === KONVERSATION ===
    ("Tu tens razão", "Du hast Recht", ""),
    ("Não há problema", "Kein Problem", ""),
    ("Não é bem...", "Es ist nicht wirklich...", ""),
    ("É verdade", "Das stimmt", ""),
    ("Acho que...", "Ich denke, dass...", ""),
    ("O que achas?", "Was hältst du davon?", ""),
    ("Quero te contar uma coisa", "Ich möchte dir etwas erzählen", ""),
    ("O que mais?", "Was noch?", ""),
    ("Pouco a pouco", "Stück für Stück", ""),
    ("Vamos chegar lá", "Wir werden es schaffen", ""),

    # === SPRÜCHE / IDIOME ===
    ("Sem consistência, sem sucesso", "Ohne Konsistenz kein Erfolg", "Spruch"),
    ("Quanto mais tu tentas, mais chances tens", "Je mehr du versuchst, desto mehr Chancen", "Spruch"),
    ("Não há sucesso sem riscos", "Kein Erfolg ohne Risiken", ""),
    ("Não tens muito a perder", "Du hast nicht viel zu verlieren", ""),

    # === BUSINESS / ARBEIT ===
    ("Trabalho com / como", "Ich arbeite mit / als", "com=Bereich, como=Rolle"),
    ("Negócio", "Geschäft", ""),
    ("Cliente", "Kunde", ""),
    ("Parceiro / Parceira de negócios", "Geschäftspartner/in", ""),
    ("Colega", "Kollege/in", ""),
    ("Aplicação / App", "App / Anwendung", ""),
    ("Sessão de fotos", "Foto-Session", ""),
    ("Website", "Website", ""),
    ("Mensagem / Mensagens", "Nachricht/en", ""),
    ("Inteligência artificial", "künstliche Intelligenz", ""),
    ("Sucesso", "Erfolg", ""),
    ("Consistência", "Konsistenz / Beständigkeit", ""),
    ("Riscos", "Risiken", ""),
    ("Capítulo", "Kapitel", "Um novo capítulo"),
    ("Futuro", "Zukunft", "Para o meu futuro"),
    ("Resolver", "lösen", ""),

    # === SPORT ===
    ("Fazer desporto", "Sport machen", "PT-PT (BR: esporte)"),
    ("Treino / Treinar", "Training / trainieren", ""),
    ("Quilómetros", "Kilometer", "PT-PT mit -ó (BR: quilômetros)"),
    ("Caminhada", "Spaziergang", ""),
    ("Corrida", "Lauf / Joggen", ""),

    # === LERNEN ===
    ("Aprendizagem", "Lernen / Lernprozess", ""),
    ("Vocabulário", "Vokabular", ""),
    ("Conversação", "Konversation", ""),
    ("Conversar por mensagem", "per Nachricht chatten", ""),
    ("Estou satisfeito", "Ich bin zufrieden", ""),
    ("Progresso", "Fortschritt", ""),

    # === ESSEN & SOZIALES ===
    ("Comer fora", "auswärts essen", ""),
    ("Cultura de comer fora", "Restaurantkultur", ""),
    ("Restaurante tradicional", "traditionelles Restaurant", ""),
    ("Doce de mandioca", "Maniok-Süßspeise", ""),
    ("Matraquilhos", "Tischkicker", "PT-PT-Wort"),

    # === WETTER ===
    ("Tempo / Clima", "Wetter / Klima", ""),
    ("Temperatura", "Temperatur", ""),
    ("Tem sol / Está ensolarado", "Es ist sonnig", ""),
    ("Chove / Está a chover", "Es regnet", ""),
    ("Frio / Calor", "Kalt / Hitze", "Está frio / Está calor"),
    ("Nuvens / Céu", "Wolken / Himmel", ""),
    ("Inverno / Verão / Primavera / Outono", "Winter / Sommer / Frühling / Herbst", ""),
    ("22 graus", "22 Grad", ""),

    # === NATUR ===
    ("Flores / Árvores", "Blumen / Bäume", ""),
    ("Arco-íris", "Regenbogen", ""),

    # === ZUHAUSE ===
    ("Casa", "Haus / Zuhause", ""),
    ("Casa de banho", "Badezimmer / Toilette", "Onde fica a casa de banho?"),
    ("Construir uma casa", "ein Haus bauen", ""),

    # === VERSCHIEDENES ===
    ("Coisa / Coisinhas", "Sache / Kleinigkeiten", ""),
    ("Mistura", "Mischung", ""),
    ("A mesma coisa", "dasselbe", ""),
    ("Atrasado / Atrasada", "verspätet", "Atrasar-se = sich verspäten"),
    ("Mudar-se", "umziehen", "reflexiv: De me mudar"),
    ("Levar", "mitnehmen / bringen", ""),
    ("Colocar / Pôr", "setzen / legen", ""),
    ("Focar", "sich konzentrieren", ""),
    ("Energia", "Energie", "Dá-te muita energia"),
    ("Quão grande?", "Wie groß?", ""),
    ("Durante o dia / a semana", "während des Tages / der Woche", ""),
    ("Rotina semanal", "Wochenroutine", ""),
    ("Infância", "Kindheit", ""),
]


def normalize_key(s):
    s = s.strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[.!?,;:\'"\\/\(\)]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


# Sicherheitsprüfung: Duplikate ans Licht bringen
seen = {}
for pt, de, note in CARDS:
    key = (normalize_key(pt), normalize_key(de))
    if key in seen:
        print(f"⚠️ DUPLIKAT: '{pt}' = '{de}' (vorher: '{seen[key]}')")
    seen[key] = pt

# CSV schreiben
master_path = os.path.join(OUTPUT_DIR, "vokabeln-master.csv")
with open(master_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    w.writerow(['Portugiesisch', 'Deutsch', 'Notiz/Beispiel'])
    for pt, de, note in CARDS:
        w.writerow([pt, de, note])

print(f"\n✓ vokabeln-master.csv ({len(CARDS)} Karten, kuratiert & dedupliziert)")
