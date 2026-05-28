summarize_webpage_gameReview = """
Sei incaricato di riassumere il contenuto grezzo di una pagina web contenente la recensione di un videogioco, recuperata da una ricerca web.
Il tuo obiettivo è creare un riassunto che preservi le informazioni valutative più importanti sul gioco. 
È fondamentale mantenere opinioni chiave, punteggi e analisi critiche senza perdere informazioni essenziali.
Ecco il contenuto grezzo della pagina:
<webpage_content>
{webpage_content}
</webpage_content>
Segui queste linee guida per creare il tuo riassunto:
1. Identifica il videogioco recensito (titolo, piattaforma, contesto di uscita se presente).
2. Preserva il giudizio complessivo (positivo, negativo, misto) e la raccomandazione finale.
3. Mantieni voti, punteggi e classifiche se presenti.
4. Estrai i principali pro e contro evidenziati dal recensore SE PRESENTI.
5. NON MENZIONARE MAI "non ho trovato un voto" o "non c'è un punteggio", semplicemente ometti il punteggio.
6. NON mettere mai a confronto fonti diverse, non dire mai che i voti possono variare leggermente a seconda della fonte.
6. Conserva gli aspetti principali del gameplay (meccaniche, storia, grafica, performance, audio).
7. Mantieni note tecniche (bug, prestazioni, FPS, ottimizzazione).
8. Conserva il ragionamento che giustifica il giudizio finale.

Il riassunto deve essere più breve dell’originale, ma sufficientemente completo da poter essere usato come rappresentazione autonoma della recensione.
- Usa stile editoriale naturale (tipo IGN / GameSpot)
- Scrivi in modo diretto come se il gioco lo stessi recensendo tu
- NON usare terza persona (vietato: "la recensione dice", "il recensore afferma")

Presenta il risultato nel seguente formato:
{{   "summary": "Riassunto strutturato con giudizio, punti chiave, pro e contro e analisi critica.",
}}
"""
summarize_webpage_gameGuide= """
Sei incaricato di riassumere il contenuto grezzo di una pagina web contenente una guida di un videogioco, recuperata da una ricerca web.
Il tuo obiettivo è creare un riassunto che preservi tutte le istruzioni essenziali, soluzioni e procedure passo-passo,accuratezza e chiarezza sono fondamentali.
Ecco il contenuto grezzo della pagina:
<webpage_content>
{webpage_content}
</webpage_content>
Segui queste linee guida per creare il tuo riassunto:
1. Identifica l’obiettivo principa  le della guida (quest, puzzle, boss, tesoro, armatura, ecc.).
2. Mantieni tutte le istruzioni passo-passo in ordine logico.
3. Conserva luoghi, nomi di oggetti, NPC e requisiti delle missioni.
4. Includi soluzioni di enigmi, codici, combinazioni o sequenze.
5. Riporta condizioni o prerequisiti necessari per sbloccare contenuti o progressi.
6. Non mettere mai a confronto fonti diverse, non dire mai che le istruzioni possono variare leggermente a seconda della fonte.
7. Devi riportare tutti gli elementi fondamentali per completare la guida, anche se sono presenti solo in una delle fonti.
Tipologie di contenuto:
- Guide puzzle: privilegia soluzioni esatte e logica di risoluzione.
- Guide loot/tesori: mantieni posizioni precise e condizioni di ottenimento.

Il riassunto deve essere più corto dell’originale ma abbastanza completo da funzionare come guida autonoma.
- Usa stile editoriale naturale
- Scrivi in modo diretto come se la guida la stessi facendo tu
- NON usare terza persona (vietato: "la guida dice", "il sito afferma")
Presenta il risultato nel seguente formato:
{{
   "summary": "Riassunto strutturato passo-passo della guida, con tutte le istruzioni e condizioni essenziali.",
}}
"""
