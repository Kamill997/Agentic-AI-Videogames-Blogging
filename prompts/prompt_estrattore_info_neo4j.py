estrazione_features_review="""
Analizza questa recensione ed estrai i metadati richiesti
REGOLA TASSATIVA PER I GENERI: Se nel testo trovi generi composti (es. 'Action-Avventura', 'Action/RPG', 'Sparatutto in prima persona, Stealth')
devi OBBLIGATORIAMENTE separarli e restituirli come elementi singoli in una lista "
(es. ['Action', 'Avventura'] o ['FPS', 'Stealth']). 
USA IL GENERE FPS PER I GIOCHI SPARATTUTTO O SIMILI
Non restituire mai un genere composto da punteggiatura
Testo della recensione:
{content}
"""      

estrazione_features_News="""
Sei un caporedattore specializzato in giornalismo videoludico.
Il tuo compito è analizzare il testo grezzo della notizia fornita ed estrarre i metadati strutturati richiesti.
Testo della news:
{content}

<REGOLE DI ESTRAZIONE RIGIDE>
1. Titolo: Estrai o genera un titolo giornalistico chiaro e diretto. Deve far capire immediatamente l'evento principale (es. "[Rumor] Svelata la data di uscita di GTA VI" oppure "Rinviata la patch 2.0 di Cyberpunk 2077").
2. Titoli Interessati: Estrai ESCLUSIVAMENTE i nomi dei videogiochi o dei franchise menzionati. Restituisci una lista pulita. Non includere nomi di console, tecnologie o personaggi.
3. Case Editrici: Identifica publisher o team di sviluppo citati (es. "Sony", "Ubisoft", "Naughty Dog"). Se non ce ne sono, restituisci una lista vuota.
4. Overview: Crea un riassunto discorsivo e conciso. Devi catturare il nucleo della notizia riportando però tutti i videogiochi coinvolti anche se accennati.
</REGOLE DI ESTRAZIONE RIGIDE>



"""