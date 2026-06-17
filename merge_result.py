import json
from State_tameplate import AgentState, llm_x
from langchain_core.messages import HumanMessage, ToolMessage
from prompts.prompt_merge import summarize_webpage_gameReview, summarize_webpage_news

def merge_result(state: AgentState):
    """
    Estrae i risultati dei tool dalla cronologia dei messaggi, 
    li combina e genera un report finale.
    """
    messages = state["messages"]
    topic = state["classification_decision"]
    richiesta_utente = state.get("query")

    links = []
    all_contents = []

    for msg in messages:
        if isinstance(msg, ToolMessage):
            if msg.name == "tavily_search_tool":
                try:
                    data = json.loads(msg.content)
                    for r in data.get("results", []):
                        if r.get("url"):
                            links.append(r.get("url"))
                        all_contents.append(r.get("content", ""))
                except Exception:
                    all_contents.append(msg.content)
            elif msg.name == "RAG_tool":
                all_contents.append(f"--- RISULTATI RAG (Interno) ---\n{msg.content}\n")
            elif msg.name == "recensioni_utenti_steam" or  msg.name == "ottieni_prezzo_gioco" or  msg.name == "numero_giocatori_attivi":
                all_contents.append(f"--- RISULTATI numero_giocatori_attivi ---\n{msg.content}\n")

    combined_content = "\n\n".join(all_contents)
    
    if not combined_content.strip():
        final_summary = "Nessun dato raccolto dai tool per poter generare un riassunto."
    else:
        final_summary = summarize_webpage_content(combined_content, topic,richiesta_utente)

    return {"merge_result": final_summary,"link_source": list(set(links))}


def summarize_webpage_content(webpage_content: str, topic: str,richiesta_utente: str) -> str:
    """
    Riassume il contenuto della pagina web utilizzando il modello di riassunto configurato.
    """
    try:
        if topic == "News":
            summarize_prompt = summarize_webpage_news
        else: 
            summarize_prompt = summarize_webpage_gameReview

        summary = llm_x.invoke([HumanMessage(content=summarize_prompt.format(webpage_content=webpage_content, richiesta=richiesta_utente))])
        
        formatted_summary = f"{summary.content}\n"
        return formatted_summary
        
    except Exception as e:
        print(f"Failed to summarize webpage: {str(e)}")
        # Fallback in caso di errore
        return webpage_content[:1000] + "...\n[Errore durante la generazione del riassunto]"