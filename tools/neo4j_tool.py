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
            if len(categorie_scelte) == 1:
                # Caso Disparità: Imponiamo la scelta
                categoria_obbligatoria = categorie_scelte[0]
                return (
                    f"ATTENZIONE - DIRETTIVA OBBLIGATORIA: Il database è sbilanciato. "
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
def tool_cerca_post(parola: str) -> str:
    """
    Cerca nei titoli dei post per una parola chiave.
    Usalo per verificare se un argomento è già stato trattato.
    Args:
        parola: parola da cercare nel titolo, es. "Elden Ring"
    """
    risultati = cerca_post_per_parola(parola)
    if not risultati:
        return f"Nessun post trovato con '{parola}' nel titolo."
    testo = f"Post trovati con '{parola}':\n"
    for p in risultati:
        testo += f"  - [{p['tipo']}] {p['title']}\n"
    return testo

def cerca_post_per_parola(parola):
    query = """
    MATCH (p:Post)
    WHERE toLower(p.titolo) CONTAINS toLower($parola)
    RETURN p.titolo AS title, p.tipo_post AS tipo
    """
    with neo4j_driver.session() as session:
      return session.run(query, {"parola": parola})
    
