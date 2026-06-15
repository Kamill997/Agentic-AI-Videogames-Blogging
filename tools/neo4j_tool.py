import json
from langchain_core.tools import tool
from neo4j_connection import neo4j_driver


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