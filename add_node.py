from datetime import datetime
from urllib.parse import urlparse
from typing import List
from langchain_core.messages import HumanMessage
from neo4j_connection import neo4j_driver
from State_tameplate import AgentState, llm_p, InfoPostReview, InfoPostNews


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
            # Chiamata LLM accoppiata al tuo schema InfoPostReview
            llm_estrattore = llm_p.with_structured_output(InfoPostReview)
            prompt = f"Analizza questa recensione ed estrai i metadati richiesti:\n\n{content}"
            extracted_data = llm_estrattore.invoke([HumanMessage(content=prompt)])
            post_id = create_review_post(session, extracted_data, content, data_odierna, link_sorgente)
        
        else:  # Caso "News"
            llm_estrattore = llm_p.with_structured_output(InfoPostNews)
            prompt = f"Analizza questa news ed estrai i videogiochi coinvolti e il publisher se presente:\n\n{content}"
            extracted_data = llm_estrattore.invoke([HumanMessage(content=prompt)])
            post_id = create_news_post(session, extracted_data, content, data_odierna, link_sorgente)
    return {"neo4j_post_id": post_id}



def create_review_post(session, post_data: InfoPostReview, content: str, data_post: str, links: List[dict]):
    query = """
    CREATE (p:Post {
        id: randomUUID(),
        titolo: $titolo,
        tipo_post: 'Review',
        data: $data_post,
        content: $content
    })
    WITH p
    MERGE (g:Game { nome: $gioco })
    MERGE (p)-[:ABOUT]->(g)
    
    // Gestione editori come lista
    WITH p
    UNWIND $case_editrici AS editore_nome
    WITH p, editore_nome WHERE editore_nome IS NOT NULL AND editore_nome <> ''
    MERGE (pub:Publisher { nome: editore_nome })
    MERGE (p)-[:PUBLISHED_BY]->(pub)
    
    // Gestione genere singolo
    WITH p
    FOREACH (_ IN CASE WHEN $genere IS NULL OR $genere = '' THEN [] ELSE [1] END |
        MERGE (gen:Genere { nome: $genere })
        MERGE (p)-[:HAS_GENERE]->(gen)
    )
    
    // Gestione sorgenti
    WITH p
    FOREACH (link_item IN $links |
        MERGE (s:Source { nome: link_item.domain })
        MERGE (p)-[:SOURCED_FROM { exact_url: link_item.url }]->(s)
    )
    RETURN p.id AS post_id
    """
    result = session.run(
        query,
        {
            "titolo": post_data.titolo,
            "gioco": post_data.gioco,
            "case_editrici": post_data.case_editrici,
            "genere": post_data.genere,
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
        id: randomUUID(),
        titolo: $titolo,
        tipo_post: 'News',
        data: $data_post,
        content: $content
    })
    
    // Srotoliamo i giochi menzionati
    WITH p
    UNWIND $titoli_interessati AS game_title
    MERGE (g:Game { nome: game_title })
    MERGE (p)-[:ABOUT]->(g)
    
    // Srotoliamo gli editori
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
    result = session.run(
        query,
        {
            "titolo": post_data.titolo,
            "titoli_interessati": post_data.titoli_interessati or [],
            "case_editrici": post_data.case_editrici or [],
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