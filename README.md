Agentic AI for Video Game Blogging

[![Powered by Groq](https://img.shields.io/badge/Powered%20by-Groq-orange.svg)](https://groq.com/)
[![Built with LangGraph](https://img.shields.io/badge/Built%20with-LangGraph-blue.svg)](https://python.langchain.com/docs/langgraph)
[![Database Neo4j](https://img.shields.io/badge/GraphDB-Neo4j-008cc1.svg)](https://neo4j.com/)

è un sistema di Intelligenza Artificiale basato su architettura ad agenti (Agentic AI) progettato per gestire, automatizzare l'esecuzione editoriale di un blog di videogiochi. 

---

## Funzionalità Principali

Il sistema è composto da un Agent specializzato a coprire l'intero ciclo di vita di un articolo:

* **News:** Ricerca delle ultime notizie nel mondo del gaming tramite *Tavily*, filtraggio delle fonti e stesura di articoli aggiornati.
* **Review Generation:** Creazione di recensioni approfondite estrapolando dati di gioco, statistiche e sentiment degli utenti tramite l'integrazione di *Steam Tool*.
* **Recommendation & Suggestion:** Sistema di suggerimento per un possibile articolo da scrivere nel caso in cui non si sappia se scrivere una nuova News/Review, il tutto basato su un Knowledge Graph gestito con *Neo4j*.
* **Content Planning:** Pianificazione editoriale intelligente degli articoli.

---

## Architettura:

*   **Orchestrazione:** [LangGraph](https://python.langchain.com/docs/langgraph) per la gestione dei workflow complessi, dello stato degli agenti e della logica ciclica.
*   **LLM Provider:** [Groq](https://groq.com/) come motore principale per garantire che utilizza i migliori modelli open-source (llama e openAI GPT).
*   **Pattern di Ragionamento:** **ReAct (Reasoning and Acting)**. Gli agenti non si limitano a generare testo, ma *pensano* a quale azione intraprendere, *usano* gli strumenti a disposizione e *reagiscono* ai risultati ottenuti.
*   **Supervisione (HITL):** Implementazione **Human-in-the-Loop** che sospende il grafo (interrupt) per permettere all'editor umano di approvare, rifiutare o modificare una bozza di articolo prima della pubblicazione finale.

## Strumenti Integrati (Tools)

*   **Tavily Search (via MCP):** Integrato tramite il *Model Context Protocol* per dotare l'agente di una ricerca web semantica e in tempo reale, fondamentale per recuperare news affidabili.
*   **Steam Tool:** Utilizzato per estrarre informazioni sui giochi, recensioni della community, prezzi e dettagli direttamente dal catalogo di Steam.
*   **Rag Tool:** Utilizzato per il recupero delle informazioni affidabili all'interno del Database Chroma.
*   **Neo4j:** Database a grafo per la costruzione e l'interrogazione del Knowledge Graph sui videogiochi.
*   **Fine-Tuning:** Utilizzato per catalogare in un sistema multiclasse le recensioni dei videogiocatori in base a "Positivo","Negativo","Misto".

---

## Installazione e Avvio

* Python 3.14
* Le chiavi API dei servizi esterni (vedi .env).
* Creazione Database tramite Neo4j Desktop (si potrebbe utilizzare anche la versione AuraDB, ma per la seguente si è optato per l'opzione locale)

1. Dipendenze

All'interno della cartella del progetto è presente un file "requirments.txt". All'interno di ciò sono presenti tutte le dipendenze necessarie da installare per il corretto funzionamento dell'Agent.
Questo è possibile, tramite riga di comando, lanciando:
pip install -r requirments.txt

2. Variabili d'ambiente
All'interno del file ".env" sarà necessario sostituire i campi designati con le proprie password e chiavi personali:

GROQ_API_KEY="Inserire API"
TAVILY_API_KEY="Inserire Tavily API"
LANGCHAIN_TRACING_V2="true"
LANGSMITH_API_KEY="Inserire API LangSmith"
LANGCHAIN_PROJECT="progetto cognitive"
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD="inserire Password del DB"

N.B. Per quanto riguarda Groq e i suoi modelli è possibile che la chiave gratuita che viene generata non sia sufficiente per via del quantitativo di Token in input, per questo è consigliato un piano "Pay-As-You-Go", cosi da pagare solamente per l'effettivo utilizzo delle chiamate effettuate ed eliminare questo limite.

3. Inizializzazione dei dati

Per quanto riguarda il RAG, sono presenti delle informazioni di partenza contenute all'interno del nostro file "recensioni.md". Queste verranno utilizzate per popolare il nostro DB. 
Per fare ciò eseguiamo:
python RAG\crea_db_chroma.py

4. Esecuzione dell'Agent e Fine Tuning
Da terminale è necessario lanciare il comando:
langgraph dev

Prima di passare all'esecuzione vera e propria è necessario configurare Langsmith studio e Agent Inbox.

#Fine Tuning
Per quanto riguarda il Fine Tuning, a causa della poca potenza computazionale e problemi relativi ai Dataset e al relativo recupero su Huggin Face, si è deciso di utilizzare la Piattaforma Kaggle.
Qui è necessario andare su "File"->"Import notebook" e successivamente, dopo il corretto import, andare su "Accellerator" e selezionare la GPU "T4 x2" e successivamente avviare le celle


Autori
Progetto realizzato per il corso di Cognitive Computing & Artificial Intelligence (A.A. 2025-2026).

Luca Camio — Matricola: 
Gioele Messina — Matricola:
