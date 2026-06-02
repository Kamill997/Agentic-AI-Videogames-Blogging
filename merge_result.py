import json
from State_tameplate import AgentState, llm
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# Assumo che tu abbia i prompt importati
from prompts.prompt_merge import summarize_webpage_gameReview, summarize_webpage_news

def merge_result(state: AgentState):
    """
    Estrae i risultati dei tool dalla cronologia dei messaggi, 
    li combina e genera un report finale.
    """
    messages = state["messages"]
    
    topic = state["classification_decision"]
    
    all_contents = []

    # 1. CERCA I RISULTATI NELLA CRONOLOGIA
    for msg in messages:
        # Filtriamo solo i messaggi generati dai Tool
        if isinstance(msg, ToolMessage):
            if msg.name == "tavily_search_tool":
                all_contents.append(f"--- RISULTATI TAVILY ---\n{msg.content}\n")
            elif msg.name == "RAG_tool":
                all_contents.append(f"--- RISULTATI RAG (Interno) ---\n{msg.content}\n")

    # 2. UNISCI TUTTO IL TESTO
    combined_content = "\n\n".join(all_contents)
    
    # 3. GENERA IL RIASSUNTO
    # Se per qualche motivo i tool non hanno prodotto nulla, evitiamo di far crashare l'LLM
    if not combined_content.strip():
        final_summary = "Nessun dato raccolto dai tool per poter generare un riassunto."
    else:
        final_summary = summarize_webpage_content(combined_content, topic)

    # 4. AGGIORNA LO STATO
    # Restituiamo il riassunto come un nuovo messaggio dell'AI (o puoi salvarlo in un'altra chiave di stato)
    return {"compose_res": final_summary}


def summarize_webpage_content(webpage_content: str, topic: str) -> str:
    """
    Summarize webpage content using the configured summarization model.
    """
    try:
        # Seleziona il prompt in base al topic
        if topic == "Review":
            summarize_prompt = summarize_webpage_gameReview
        else: # Default
            summarize_prompt = summarize_webpage_news

        # Chiamata all'LLM (Nota: usiamo invoke e passiamo il template formattato)
        summary = llm.invoke([
            HumanMessage(content=summarize_prompt.format(webpage_content=webpage_content))
        ])
        
        formatted_summary = f"<summary>\n{summary.content}\n</summary>\n\n"
        return formatted_summary
        
    except Exception as e:
        print(f"Failed to summarize webpage: {str(e)}")
        # Fallback in caso di errore
        return webpage_content[:1000] + "...\n[Errore durante la generazione del riassunto]"