from datetime import datetime
from urllib.parse import urlparse
from typing import List
from langchain_core.messages import HumanMessage
from neo4j_connection import neo4j_driver
from State_template import AgentState, llm_p, InfoPostReview, InfoPostNews
from prompts.prompt_estrattore_info_neo4j import estrazione_features_review,estrazione_features_News


def create_post_node_in_neo4j(state: AgentState):
    """
    Nodo finale: Riceve il testo puro e i link, estrae le feature
    tramite LLM strutturato e crea i nodi relazionali in Neo4j.
    """
    if neo4j_driver is None:
        raise RuntimeError("Il driver di Neo4j non è inizializzato.")
    
    content = state.get("merge_result")
    topic = state.get("classification_decision")
    raw_links = state.get("link_source", [])
    data_odierna = datetime.now().strftime("%Y-%m-%d")

    if not content or content.startswith("Nessun dato raccolto"):
        raise ValueError("Contenuto della bozza assente o non valido.")

    link_sorgente = elabora_link_sorgente(raw_links)

    with neo4j_driver.session() as session:
        if topic == "Review":
            llm_estrattore = llm_p.with_structured_output(InfoPostReview)
            extracted_data = llm_estrattore.invoke([HumanMessage(content=estrazione_features_review.format(content=content))])
            post_id = create_review_post(session, extracted_data, content, data_odierna, link_sorgente)
        
        else:  
            llm_estrattore = llm_p.with_structured_output(InfoPostNews)
            extracted_data = llm_estrattore.invoke([HumanMessage(content=estrazione_features_News.format(content=content))])
            post_id = create_news_post(session, extracted_data, content, data_odierna, link_sorgente)
    return {"neo4j_post_id": post_id}



def create_review_post(session, post_data: InfoPostReview, content: str, data_post: str, links: List[dict]):
    query = """
    CREATE (p:Post {
        titolo: $titolo,
        tipo_post: 'Review',
        data: $data_post,
        content: $content,
        overview: $overview
    })
    
    // 1. Gestione del gioco principale recensito (SENZA booleano 'uscito')
    WITH p
    MERGE (main_g:Game { nome: $gioco_principale })
    SET main_g.uscito = true 
    MERGE (p)-[:ABOUT]->(main_g)
    
    // 2. Gestione degli ALTRI giochi scoperti (CON booleano 'uscito')
    WITH p
    UNWIND $giochi_menzionati AS gioco_scoperto
    WITH p, gioco_scoperto WHERE gioco_scoperto.nome IS NOT NULL AND gioco_scoperto.nome <> ''
    MERGE (g_scoperto:Game { nome: gioco_scoperto.nome })
    SET g_scoperto.uscito = coalesce(g_scoperto.uscito, false) OR gioco_scoperto.uscito
    MERGE (p)-[:MENTIONS]->(g_scoperto) // Usiamo MENTIONS per distinguerli dal gioco recensito
    
    // Gestione editori
    WITH p
    UNWIND $case_editrici AS editore_nome
    WITH p, editore_nome WHERE editore_nome IS NOT NULL AND editore_nome <> ''
    MERGE (pub:Publisher { nome: editore_nome })
    MERGE (p)-[:PUBLISHED_BY]->(pub)
    
    // Gestione generi multipli come lista
    WITH p
    UNWIND $genere AS genere_nome
    WITH p, genere_nome WHERE genere_nome IS NOT NULL AND genere_nome <> ''
    MERGE (gen:Genere { nome: genere_nome })
    MERGE (p)-[:HAS_GENERE]->(gen)
    
    // Gestione sorgenti
    WITH p
    FOREACH (link_item IN $links |
        MERGE (s:Source { nome: link_item.domain })
        MERGE (p)-[:SOURCED_FROM { exact_url: link_item.url }]->(s)
    )
    RETURN p.id AS post_id
    """
    
    # Prepariamo la lista dei giochi menzionati strutturata per Cypher
    giochi_menzionati_strutturati = []
    if post_data.giochi_menzionati:
        for g in post_data.giochi_menzionati:
            if g and g.nome:
                giochi_menzionati_strutturati.append({
                    "nome": g.nome.strip().title(),
                    "uscito": g.uscito
                })

    result = session.run(
        query,
        {
            "titolo": post_data.titolo,
            "gioco_principale": post_data.gioco.strip().title() if post_data.gioco else "Sconosciuto",
            "giochi_menzionati": giochi_menzionati_strutturati,
            "case_editrici": [c.strip().title() for c in post_data.case_editrici if c and c.strip()],
            "genere": [g.strip().title() for g in post_data.genere if g and g.strip()],
            "overview": post_data.overview, 
            "content": content,
            "data_post": data_post,
            "links": links
        }
    )
    record = result.single()
    return record["post_id"] if record else None

def create_news_post(session, post_data: InfoPostNews, content: str, data_post: str, links: List[dict]):
    query = """
    CREATE (p:Post {
        titolo: $titolo,
        tipo_post: 'News',
        data: $data_post,
        content: $content,
        overview: $overview 
    })
    
    // Gestione dei giochi menzionati nella news (CON booleano 'uscito')
    WITH p
    UNWIND $titoli_interessati AS gioco_info
    WITH p, gioco_info WHERE gioco_info.nome IS NOT NULL AND gioco_info.nome <> ''
    MERGE (g:Game { nome: gioco_info.nome })
    // Aggiorna il valore a true se lo era già o se la news indica che è uscito
    SET g.uscito = coalesce(g.uscito, false) OR gioco_info.uscito
    MERGE (p)-[:ABOUT]->(g)
    
    // Gestione editori
    WITH p
    UNWIND $case_editrici AS editore_nome
    WITH p, editore_nome WHERE editore_nome IS NOT NULL AND editore_nome <> ''
    MERGE (pub:Publisher { nome: editore_nome })
    MERGE (p)-[:PUBLISHED_BY]->(pub)
    
    // Gestione sorgenti
    WITH p
    FOREACH (link_item IN $links |
        MERGE (s:Source { nome: link_item.domain })
        MERGE (p)-[:SOURCED_FROM { exact_url: link_item.url }]->(s)
    )
    RETURN p.id AS post_id
    """
    
    # Trasformiamo la lista di oggetti Pydantic GiocoInfo in una lista di dizionari per la query Cypher
    giochi_strutturati = []
    if post_data.titoli_interessati:
        for g in post_data.titoli_interessati:
            if g and g.nome:
                giochi_strutturati.append({
                    "nome": g.nome.strip().title(),
                    "uscito": g.uscito
                })

    result = session.run(
        query,
        {
            "titolo": post_data.titolo,
            "titoli_interessati": giochi_strutturati,
            "case_editrici": [c.strip().title() for c in post_data.case_editrici if c and c.strip()],
            "overview": post_data.overview, 
            "content": content,
            "data_post": data_post,
            "links": links
        }
    )
    record = result.single()
    return record["post_id"] if record else None

def elabora_link_sorgente(links: List[str]) -> List[dict]:
    """
    Prende la lista di URL grezzi e la trasforma in una lista di dizionari
    con il dominio pulito (es. 'everyeye.it') e l'URL completo.
    """
    link_strutturati = []
    for url in links:
        if not url:
            continue
        try:
            dominio = urlparse(url).netloc
            if dominio.startswith("www."):
                dominio = dominio[4:]
            link_strutturati.append({"domain": dominio, "url": url})
        except Exception:
            continue
    return link_strutturati