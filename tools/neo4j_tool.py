import json
from typing import List, Optional
from langchain_core.tools import tool
from neo4j_connection import neo4j_driver


@tool
def get_planning_context_tool() -> str:
    """
    Recupera numero di review e news, le ultime 5 news, 
    i generi degli ultimi 5 giochi recensiti e il conteggio globale di tutti i generi recensiti.
    """
    query = """
    // 1. Conteggi totali
    MATCH (p:Post)
    WITH count(CASE WHEN p.tipo_post = 'News' THEN 1 END) AS news_count,
         count(CASE WHEN p.tipo_post = 'Review' THEN 1 END) AS rec_count

    // 2. Info sulle ultime 5 Recensioni e i loro generi
    OPTIONAL MATCH (p_rev:Post {tipo_post: 'Review'})
    WITH news_count, rec_count, p_rev
    ORDER BY p_rev.data DESC LIMIT 5
    
    OPTIONAL MATCH (p_rev)-[:HAS_GENERE]->(g:Genere)
    WITH news_count, rec_count, 
         collect(DISTINCT p_rev.titolo) AS recent_rec_titles,
         collect(DISTINCT g.nome) AS ultimi_5_generi_raw
         
    // Pulisce eventuali valori nulli
    WITH news_count, rec_count, recent_rec_titles, 
         [x IN ultimi_5_generi_raw WHERE x IS NOT NULL] AS ultimi_5_generi

    // 3. Titoli e Overview delle ultime 5 News in assoluto
    OPTIONAL MATCH (n:Post {tipo_post: 'News'})
    WITH news_count, rec_count, recent_rec_titles, ultimi_5_generi, n
    ORDER BY n.data DESC LIMIT 5
    
    WITH news_count, rec_count, recent_rec_titles, ultimi_5_generi, 
         collect(DISTINCT CASE WHEN n IS NOT NULL THEN {titolo: n.titolo, overview: n.overview} END) AS recent_news_raw
         
    WITH news_count, rec_count, recent_rec_titles, ultimi_5_generi, 
         [x IN recent_news_raw WHERE x IS NOT NULL] AS recent_news_details

    // 4. Tutti i generi recensiti nel DB con il rispettivo conteggio totale
    OPTIONAL MATCH (all_rev:Post {tipo_post: 'Review'})-[:HAS_GENERE]->(all_g:Genere)
    WITH news_count, rec_count, recent_rec_titles, ultimi_5_generi, recent_news_details, all_g, count(DISTINCT all_rev) AS conteggio
    
    WITH news_count, rec_count, recent_rec_titles, ultimi_5_generi, recent_news_details,
         collect(DISTINCT CASE WHEN all_g IS NOT NULL THEN {genere: all_g.nome, volte_recensito: conteggio} END) AS tutti_generi_raw
         
    RETURN 
        news_count, 
        rec_count, 
        recent_rec_titles, 
        ultimi_5_generi, 
        recent_news_details,
        [x IN tutti_generi_raw WHERE x IS NOT NULL] AS tutti_i_generi_recensiti
    """
    
    try:
        with neo4j_driver.session() as session:
            result_cursor = session.run(query)
            record = result_cursor.single()

            if record is None:
                news, recs, recent_rec_titles, ultimi_5_generi, recent_news_details, tutti_i_generi = 0, 0, [], [], [], []
            else:
                news = record["news_count"]
                recs = record["rec_count"]
                recent_rec_titles = record["recent_rec_titles"]
                ultimi_5_generi = record["ultimi_5_generi"]
                recent_news_details = record["recent_news_details"]
                tutti_i_generi = record["tutti_i_generi_recensiti"]
                
            context = {
                "statistiche": {"news": news, "recensioni": recs},
                "varietà_tematica": {
                    "ultimi_5_generi": ultimi_5_generi,
                    "tutti_i_generi_recensiti": tutti_i_generi
                },
                "ultime_recensioni": recent_rec_titles,
                "news_recenti_pubblicate": recent_news_details 
            }
                        
            return json.dumps(context, indent=2, ensure_ascii=False)
            
    except Exception as e:
        return f"Errore critico durante il recupero del contesto: {str(e)}"

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
def check_game_already_reviewed_tool(game_name: str) -> dict:
    """Usa questo tool prima di finalizzare una recensione.
       Verifica se un gioco è già stato recensito nel database e ritorna i match trovati.
    """
    query = """
    MATCH (p:Post {tipo_post: 'Review'})
    WHERE toLower(p.overview) CONTAINS toLower($game_name)
       OR EXISTS {
           MATCH (p)-[:ABOUT]->(g:Game)
           WHERE toLower(g.nome) = toLower($game_name)
       }
    RETURN p.titolo AS titolo, p.overview AS overview
    """
    try:
        with neo4j_driver.session() as session:
            result_cursor = session.run(query, game_name=game_name)
            records = [record.data() for record in result_cursor]
            
            if not records:
                return {
                    "is_duplicate": False, 
                    "message": f"Il gioco '{game_name}' non ha recensioni esistenti. È disponibile.",
                    "data": []
                }
            
            return {
                "is_duplicate": True, 
                "message": f"Attenzione: Il gioco '{game_name}' risulta già recensito.",
                "data": records
            }       
    except Exception as e:
        return {"is_duplicate": False, "error": f"Errore: {str(e)}", "data": []}


@tool
def check_news_already_published_tool(argomento: str) -> dict:
    """
    Usa questo tool prima di finalizzare una notizia.
    Verifica se esistono già news pubblicate nel database su un determinato argomento o gioco.
    Ritorna i match trovati con titolo e overview.
    """
    query = """
    MATCH (p:Post {tipo_post: 'News'})
    WHERE toLower(p.titolo) CONTAINS toLower($argomento)
       OR toLower(p.overview) CONTAINS toLower($argomento)
       OR EXISTS {
           MATCH (p)-[:ABOUT]->(g:Game)
           WHERE toLower(g.nome) = toLower($argomento)
       }
    RETURN p.titolo AS titolo, p.overview AS overview
    """
    try:
        with neo4j_driver.session() as session:
            result_cursor = session.run(query, argomento=argomento)
            records = [record.data() for record in result_cursor]
            
            if not records:
                return {
                    "is_duplicate": False, 
                    "message": f"Nessuna news trovata per '{argomento}'. L'argomento è libero.",
                    "data": []
                }
            
            return {
                "is_duplicate": True, 
                "message": f"Esistono già news pubblicate su '{argomento}'.",
                "data": records
            }
            
    except Exception as e:
        return {"is_duplicate": False, "error": f"Errore: {str(e)}", "data": []}
    

@tool
def get_unreviewed_released_games_tool() -> dict:
    """
    Da usare quando si vuole proporre una RECENSIONE.
    Recupera dal database la lista dei giochi 'scoperti' (tramite news o citazioni) 
    che sono già usciti sul mercato (uscito: true) ma che NON hanno ancora una recensione.
    Ritorna una lista di nomi di videogiochi da cui poter attingere.
    """
    query = """
    MATCH (g:Game)
    // Il gioco deve essere uscito
    WHERE g.uscito = true 
      // E NON deve esistere una recensione che parla esplicitamente di lui
      AND NOT EXISTS { MATCH (p:Post {tipo_post: 'Review'})-[:ABOUT]->(g) }
    RETURN g.nome AS gioco
    """
    try:
        with neo4j_driver.session() as session:
            result_cursor = session.run(query)
            records = [record["gioco"] for record in result_cursor]
            
            if not records:
                return {
                    "success": True,
                    "message": "Nessun gioco in backlog. Non ci sono giochi usciti in attesa di recensione.",
                    "giochi_disponibili": []
                }
            
            return {
                "success": True,
                "message": f"Trovati {len(records)} giochi usciti e in attesa di recensione.",
                "giochi_disponibili": records
            }
            
    except Exception as e:
        return {"success": False, "error": f"Errore durante il recupero dei giochi: {str(e)}", "giochi_disponibili": []}
    
