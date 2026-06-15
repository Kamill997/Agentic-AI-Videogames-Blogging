import json
from langchain_core.tools import tool
from neo4j_connection import neo4j_driver

@tool
def get_least_populated_category_info_tool() -> str:
    """
    Analizza il database, individua in automatico la o le categorie con meno articoli 
    (tra News e Review) e restituisce i post già pubblicati della categoria carente.
    In caso di pareggio, restituisce i post di entrambe le categorie lasciando all'LLM la scelta.
    """
    if not neo4j_driver:
        return "Errore: Connessione al database Neo4j non disponibile."

    # 1. Base di partenza
    categorie_base = {"News": 0, "Review": 0}
    
    query_conteggio = """
    MATCH (p:Post)
    WHERE p.tipo_post IN ["News", "Review"]
    RETURN p.tipo_post AS category, count(p) AS totale
    """
    
    try:
        with neo4j_driver.session() as session:
            # 2. Aggiorniamo i conteggi reali dal DB
            result_conteggio = session.run(query_conteggio)
            for record in result_conteggio:
                cat = record["category"]
                if cat in categorie_base:
                    categorie_base[cat] = record["totale"]
            
            valore_minimo = min(categorie_base.values())
            categorie_scelte = [k for k, v in categorie_base.items() if v == valore_minimo]
            
            # Se sono entrambe a zero post
            if valore_minimo == 0:
                nomi_cat = " e ".join([f"'{c}'" for c in categorie_scelte])
                return f"Le categorie {nomi_cat} non hanno ancora nessun post. Hai campo totalmente libero, scegli tu quale categoria trattare e proponi idee originali!"
                
            # 3. Recupero titoli combinato usando "IN $cats"
            query_titoli = """
            MATCH (p:Post)
            WHERE p.tipo_post IN $cats
            OPTIONAL MATCH (p)-[:HAS_GENERE]->(g:Genere)
            RETURN p.titolo AS title, p.tipo_post AS topic, p.data AS date, g.nome AS genere
            ORDER BY p.data DESC
            """
            
            # Passiamo la lista di categorie (es. ["News", "Review"])
            result_titoli = session.run(query_titoli, cats=categorie_scelte)
            
            lista_post = []

            # 4. Formattazione dell'array JSON
            for index, record in enumerate(result_titoli, start=1):
                post_strutturato = {
                    "id": index,
                    "titolo": record["title"],
                    "topic": record["topic"],
                    "data": record["date"]
                }
                
                if record["genere"] is not None:
                    post_strutturato["genere"] = record["genere"]
                
                lista_post.append(post_strutturato)
                
            dati_json = json.dumps(lista_post, indent=2, ensure_ascii=False)
            
            # 6. AVVISO ESPLICITO PER L'LLM
            recap_numeri = f"[Conteggio attuale -> News: {categorie_base['News']}, Review: {categorie_base['Review']}]"
            if len(categorie_scelte) == 1:
                # Caso Disparità: Imponiamo la scelta
                categoria_obbligatoria = categorie_scelte[0]
                return (
                    f"ATTENZIONE - DIRETTIVA OBBLIGATORIA: Il database è sbilanciato. {recap_numeri}\n"
                    f"La categoria più carente è '{categoria_obbligatoria}'. "
                    f"DEVI ASSOLUTAMENTE scegliere il formato '{categoria_obbligatoria}' per la tua nuova proposta, "
                    f"non ti è permesso scegliere l'altra. \n"
                    f"Ecco gli ultimi post di tipo '{categoria_obbligatoria}' per non ripetere gli argomenti:\n\n"
                    f"{dati_json}"
                )
            else:
                # Caso Pareggio: Lasciamo la scelta all'LLM
                nomi_cat = " e ".join(categorie_scelte)
                return (
                    f"ATTENZIONE - PAREGGIO: C'è un perfetto equilibrio tra {nomi_cat}. "
                    f"Scegli tu arbitrariamente quale formato usare per la tua nuova proposta. \n"
                    f"Ecco gli ultimi post di entrambe le categorie per non ripetere gli argomenti:\n\n"
                    f"{dati_json}"
                )

    except Exception as e:
        return f"Errore critico durante l'analisi delle categorie deboli: {str(e)}"
    

@tool
def check_active_plan_tool() -> str:
    """
    Verifica se esistono nodi PENDING. 
    Se esistono, li ordina per 'ordine'. 
    Se non esistono, ritorna il messaggio di nessun piano.
    """
    query = """
        MATCH (p:Pianificazione {stato: 'PENDING'})
        WITH p
        ORDER BY COALESCE(p.ordine, 0) ASC
        RETURN collect(p.titolo) AS titoli
    """
    with neo4j_driver.session() as session:
        result = session.run(query).single()
        titoli = result["titoli"] if result else []
    
    if titoli:
        return f"PIANO_ATTIVO: Ecco gli articoli in attesa: {', '.join(titoli)}"
    return "NESSUN_PIANO: Non c'è alcuna pianificazione attiva al momento."

@tool
def get_planning_context_tool() -> str:
    """
    Recupera numero di review e news, ultime 5 news, generi degli ultimi 5 giochi recensiti:
.
    """
    query = """
    // 1. Conteggi totali basati su tipo_post
    MATCH (p:Post)
    WITH count(CASE WHEN p.tipo_post = 'News' THEN 1 END) AS news_count,
         count(CASE WHEN p.tipo_post = 'Review' THEN 1 END) AS rec_count

    // 2. Info sulle ultime 5 Recensioni (titoli e generi)
    OPTIONAL MATCH (p_rev:Post {tipo_post: 'Review'})
    WITH news_count, rec_count, p_rev
    ORDER BY p_rev.data DESC LIMIT 5
    OPTIONAL MATCH (p_rev)-[:HAS_GENERE]->(gen:Genere)
    
    WITH news_count, rec_count, 
         collect(DISTINCT p_rev.titolo) AS recent_rec_titles,
         collect(DISTINCT gen.nome) AS recent_genres
    
    // 3. Titoli e Overview delle News recenti (ultimi 5 giorni)
    OPTIONAL MATCH (n:Post {tipo_post: 'News'})
    WHERE date(n.data) >= date() - duration('P5D')
    
    RETURN 
        news_count, 
        rec_count, 
        recent_genres, 
        recent_rec_titles,
        collect(DISTINCT {titolo: n.titolo, overview: n.overview}) AS recent_news_details
        
    """
    
    try:
        with neo4j_driver.session() as session:
            result_cursor = session.run(query)
            record = result_cursor.single()
            avvisi = []

            if record is None:
                news, recs, genres, rec_titles, news_details = 0, 0, [], [], []
            else:
                news = record["news_count"]
                recs = record["rec_count"]
                genres = record["recent_genres"]
                rec_titles = record["recent_rec_titles"]
                news_details = record["recent_news_details"] 
            context = {
                "avvisi": avvisi,
                "statistiche": {"news": news, "recensioni": recs},
                "varietà_tematica": {"ultimi_5_generi": genres},
                "ultime_recensioni": rec_titles,
                "news_recenti_dettagli": news_details 
            }
                        
            return json.dumps(context, indent=2, ensure_ascii=False)
            
    except Exception as e:
        return f"Errore critico durante il recupero del contesto: {str(e)}"

@tool
def check_game_already_reviewed_tool(game_name: str) -> str:
    """Usa questo tool prima di finalizzare una recensione.
       Verifica se un gioco è già stato recensito nel database. 
       Passa come parametro in game_name il nome del gioco.
       """
    query = """
    OPTIONAL MATCH (g:Game {nome: $game_name})
    OPTIONAL MATCH (p1:Post {tipo_post: 'Review'})-[:ABOUT]->(g)
        OPTIONAL MATCH (p2:Post {tipo_post: 'Review'})
    WHERE toLower(p2.overview) CONTAINS toLower($game_name)
    
    RETURN count(p1) > 0 OR count(p2) > 0 AS gia_recensito
    """
    try:
        with neo4j_driver.session() as session:
            result_cursor = session.run(query, game_name=game_name)
            record = result_cursor.single()
            
            if record and record["gia_recensito"]:
                return f"SI: Il gioco '{game_name}' è già stato recensito."
            
            return "OK: Il gioco è disponibile."
            
    except Exception as e:
        return f"Errore durante la verifica: {str(e)}"