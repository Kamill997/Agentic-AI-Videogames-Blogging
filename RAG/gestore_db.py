import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import nome_db_RAG,percorso_DB_RAG,modello_embeddings

percorso_DB_RAG = "./chroma_db"
nome_db_RAG = "recensioni"
modello_embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")

def ottieni_db():
    return Chroma(
        persist_directory=percorso_DB_RAG, 
        embedding_function=modello_embeddings,
        collection_name=nome_db_RAG
    )

def cerca_recensioni_semantica_pura(query, k=1):
    db = ottieni_db()
    
    # Aggiungiamo il prefisso richiesto dal modello E5
    query_formattata = f"query: {query}"
    
    # NOTA: Abbiamo rimosso il parametro filter! L'IA cercherà liberamente ovunque.
    risultati = db.similarity_search(query_formattata, k=k)    
    
    print(f"\nRicerca semantica pura per: '{query}'")    
    if not risultati:
        print("Nessun chunk trovato.")
        return []

    for i, res in enumerate(risultati):
        sezione = res.metadata.get('sezione', 'Info')
        print(f"\n--- Risultato {i+1} [Sezione: {sezione}] ---")
        print(f"Gioco rilevato dai Metadati: {res.metadata.get('game')}")
        print(f"Contenuto del chunk:\n{res.page_content}") 
    return risultati


if __name__ == "__main__":
    cerca_recensioni_semantica_pura("informazioni di gta 5", k=3)
    
    
