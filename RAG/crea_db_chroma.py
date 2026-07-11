import os
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import MarkdownHeaderTextSplitter
from crea_chunk import chunka_con_titolo 
from config import nome_db_RAG,percorso_DB_RAG,modello_embeddings

def crea_db_RAG(file_path):
    
    headers_to_split_on = [
        ("#", "gioco"),  #Salva il nome del paragrafo nel metadato "game"
        ("##", "sezione")  #Salva il nome del sottoparagrafo nel metadato "seziones"
    ]
    
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    sezioni = splitter.split_text(md_text) #sezioni è una lista di Documenti e ogni documento contiene una sezione (es. la trama) e i suoi metadati
    
    documenti_finali = []
    
    for sezione in sezioni:
        titolo_gioco = sezione.metadata.get("gioco", "Info")
        nome_sezione = sezione.metadata.get("sezione", "Info")
        
        titolo_sezione = f"{titolo_gioco} - {nome_sezione}"
        
        chunks = chunka_con_titolo(sezione.page_content, titolo_sezione, 400, 50)
        
        for chunk in chunks:
            documenti_finali.append(Document(
                page_content=chunk, 
                metadata={
                    "gioco": titolo_gioco,
                    "sezione": nome_sezione
                }
            ))
            
    print(f"Salvataggio di {len(documenti_finali)} sezioni in Chroma")
    Chroma.from_documents(
        documents=documenti_finali,
        embedding=modello_embeddings,
        persist_directory=percorso_DB_RAG,
        collection_name=nome_db_RAG
    )

if __name__ == "__main__":
    percorso_file = os.path.join("RAG", "recensioni.md")
    crea_db_RAG(percorso_file)
    