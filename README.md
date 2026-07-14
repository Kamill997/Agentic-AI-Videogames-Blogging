# Agentic AI for Video Game Blogging

**Agentic AI for Video Game Blogging** è un sistema di Intelligenza Artificiale basato su un'architettura ad agenti (Agentic AI) progettato per supportare un autore nella gestione e nell'automazione del processo editoriale di un blog dedicato al mondo dei videogiochi.

---

## Funzionalità Principali

Il sistema è composto da un agente specializzato in grado di assistere l'autore del blog nelle diverse fasi del processo editoriale, dalla ricerca delle informazioni fino alla pianificazione dei contenuti a lungo termine.

- **News:** Ricerca delle ultime notizie nel mondo del gaming tramite Tavily, filtraggio delle fonti e stesura di articoli aggiornati.
- **Review Generation:** Creazione di recensioni approfondite estrapolando dati di gioco, statistiche e sentiment degli utenti tramite l'integrazione di Steam Tool.
- **Recommendation & Suggestion:** Sistema di suggerimento per un possibile articolo da scrivere nel caso in cui non si sappia se scrivere una nuova News/Review, il tutto basato su un Knowledge Graph gestito con Neo4j.
- **Content Planning:** Pianificazione editoriale intelligente degli articoli per n giorni (1 post a giorno).

---

## Architettura

- **Orchestrazione:** LangGraph per la gestione e la visione del flusso esecutivo dell'agente.
- **LLM Provider:** Groq, servizio che mette a disposizione vari modelli di Large Language Model (Llama e OpenAI GPT).
- **Pattern di Ragionamento:** ReAct (Reasoning and Acting). Gli agenti non si limitano a generare testo, ma pensano a quale azione intraprendere, usano gli strumenti a disposizione e reagiscono ai risultati ottenuti.
- **Supervisione (HITL):** Implementazione Human-in-the-Loop che sospende il grafo (interrupt) per permettere all'umano di approvare, rifiutare o modificare una bozza di un articolo proposto (o di un suggerimento editoriale) prima della pubblicazione finale.

---

## Strumenti Integrati (Tools)

- **Tavily Search (via MCP):** Integrato tramite il Model Context Protocol per dotare l'agente di un motore di ricerca web semantica e in tempo reale, fondamentale per recuperare informazioni da internet.
- **Steam Tool:** Utilizzato per estrarre informazioni sui giochi, recensioni della community, prezzi e dettagli direttamente dal catalogo di Steam.
- **RAG Tool:** Utilizzato per il recupero delle informazioni affidabili all'interno del Database Chroma.
- **Neo4j:** Database a grafo per la costruzione e l'interrogazione del Knowledge Graph sui videogiochi.
- **Fine-Tuning:** Utilizzato per catalogare in un sistema multiclasse le recensioni dei videogiocatori in base a "Positivo", "Negativo", "Misto".

---

## Installazione e Avvio

### Prerequisiti

- Python 3.14
- Chiavi API dei servizi esterni (da inserire nel file `.env`)
- Creazione del Database tramite Neo4j Desktop (in alternativa è possibile utilizzare la versione AuraDB, ma per questo progetto si è optato per l'installazione in locale)

### Dipendenze

All'interno della cartella del progetto è presente un file `requirements.txt` contenente tutte le dipendenze necessarie per il corretto funzionamento dell'agente. Per installarle, eseguire:

```bash
pip install -r requirements.txt
```

### Variabili d'Ambiente

All'interno del file `.env` sarà necessario sostituire i campi designati con le proprie chiavi e password personali:

```env
GROQ_API_KEY="Inserire API"
TAVILY_API_KEY="Inserire Tavily API"
LANGCHAIN_TRACING_V2="true"
LANGSMITH_API_KEY="Inserire API LangSmith"
LANGCHAIN_PROJECT="progetto cognitive"
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD="Inserire Password del DB"
```

> **N.B.** Per quanto riguarda Groq e i modelli disponibili gratuitamente, è possibile che la chiave API gratuita non sia sufficiente a gestire richieste complesse come il planning, in quanto fanno uso di un numero elevato di token. Per questo motivo, si consiglia di utilizzare il piano **Pay-As-You-Go**, che consente di pagare esclusivamente in base all'effettivo utilizzo delle API, eliminando le limitazioni legate al piano gratuito.

### Inizializzazione dei Dati

Per quanto riguarda il RAG, sono presenti delle informazioni di partenza contenute all'interno del file `recensioni.md`, che verranno utilizzate per popolare il database. Per eseguire l'inizializzazione:

```bash
python RAG/crea_db_chroma.py
```

### Esecuzione dell'Agente

Da terminale, lanciare il seguente comando:

```bash
langgraph dev
```

> Prima di avviare l'esecuzione vera e propria, è necessario configurare **LangSmith Studio** e **Agent Inbox** per poter interagire correttamente con l'agente.

---

## Fine Tuning

A causa della limitata potenza computazionale e di problematiche relative ai dataset e al loro recupero su Hugging Face, si è deciso di utilizzare la piattaforma **Kaggle**. La procedura da seguire è la seguente:

1. Andare su **File** → **Import Notebook** e importare il notebook del progetto.
2. Dopo il corretto import, andare su **Accelerator** e selezionare la GPU **T4 x2**.
3. Avviare l'esecuzione delle celle.

---

## Autori

Progetto realizzato per il corso di **Cognitive Computing & Artificial Intelligence** (A.A. 2025-2026).

| Nome | Matricola |
|------|-----------|
| Luca Camiolo | 1000084790 |
| Gioele Messina | 1000002040 |
