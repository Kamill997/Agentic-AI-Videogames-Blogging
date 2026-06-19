from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma
from RAG.config import percorso_DB_RAG, nome_db_RAG, modello_embeddings

SOGLIA_MASSIMA_DISTANZA = 0.76

@tool
def RAG_tool(query: str, ragionamento: str) -> str:
    """
    Cerca nel database locale di conoscenza (recensioni strutturate) informazioni approfondite:
    Per la recensioni riguardo:
    trame, meccaniche di gioco, gameplay, analisi critica e dettagli tecnici dei videogiochi.
    Per le News riguardo informazioni su eventi, case produttrici

    Args:
        query: Le parole chiave o la frase naturale da cercare nel database. 
               (Includi sempre il nome del gioco per risultati ottimali).
        ragionamento: Spiega sinteticamente il motivo per cui hai deciso di consultare il database locale.
    """
    db = Chroma(
        persist_directory=percorso_DB_RAG, 
        embedding_function=modello_embeddings,
        collection_name=nome_db_RAG
    )
    
    # Prepariamo la query
    query_formattata = f"query: {query}"
    
    # Aumentiamo k a 3 per avere più contesto, ma filtreremo ogni risultato
    risultati = db.similarity_search_with_relevance_scores(query_formattata, k=3) 
    
    if not risultati:
        return "Nessuna informazione trovata nel database locale per questa ricerca."
    
    frammenti_accettati = []
    
    for documento, score in risultati:
        if score is not None and score >= SOGLIA_MASSIMA_DISTANZA:
            gioco = documento.metadata.get('gioco', 'Gioco Sconosciuto')
            sezione = documento.metadata.get('sezione', 'Info')
            
            blocco = (
                f"--- ESTRATTO PERTINENTE (Score: {score:.2f}) ---\n"
                f"Gioco: {gioco}\n"
                f"Sezione: {sezione}\n"
                f"Contenuto:\n{documento.page_content}\n"
            )
            frammenti_accettati.append(blocco)
    
    if not frammenti_accettati:
        return "Ho trovato risultati, ma nessuno è risultato abbastanza pertinente (troppo distanti semanticamente)."
        
    return "\n\n".join(frammenti_accettati)