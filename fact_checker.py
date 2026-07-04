import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from State_template import AgentState, llm_p,FactCheckResult

def fact_check_node(state: AgentState):
    bozza = state.get("merge_result", "")
    messages = state.get("messages", [])
    query=state.get("query","")

    raw_facts = []
    
    for msg in messages:
        if isinstance(msg, ToolMessage):
            if msg.name == "tavily_search_tool":
                try:
                    data = json.loads(msg.content)
                    for r in data.get("results", []):
                        raw_facts.append(r.get("content", ""))
                except Exception:
                    raw_facts.append(msg.content)
            elif msg.name in ["RAG_tool"]:
                raw_facts.append(msg.content)

    contesto_fonti = "\n\n".join(raw_facts)

    if not bozza or not contesto_fonti.strip():
        return {"fact_check_warning": None}

    system_prompt = """
    Sei un revisore editoriale (Fact-Checker) rigoroso.
    Il tuo unico scopo è verificare che la BOZZA non contenga "allucinazioni".
    Regole Tassative:
    1. La bozza NON deve contenere numeri, nomi, date o fatti concreti che non siano esplicitamente presenti o deducibili dalle FONTI GREZZE.
    2. Non valutare lo stile di scrittura, valuta SOLO la coerenza fattuale.
    4. Se la bozza è perfettamente aderente alle fonti, rispondi has_conflicts='no' e discrepancies='Nessuna'.
    5. Se il RAG non ha dati su questo gioco, rispondi has_conflicts='no' e discrepancies='Nessuna'.
    6. Se trovi discrepanze restituisci has_conflicts='si' e discrepancies='Discrepanza trovata'
    7. Se i dati trovati NON SONO RELATIVI AL GIOCO RICHIESTO restituisci has_conflicts='no' e discrepancies='Nessuna'

    --- FONTI GREZZE ESTRATTE DAL TOOL RAG ---
    {contesto_fonti}
    {bozza_da_controllare}
    {richiesta_utente}
    --------------------------------------
    """

    llm_structured = llm_p.with_structured_output(FactCheckResult)
    risultato_check = llm_structured.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=system_prompt.format(contesto_fonti=contesto_fonti,bozza_da_controllare=bozza,richiesta_utente=query))
    ])
    print(f"conflitto rilevato: {risultato_check.has_conflicts }, discrepanza: {risultato_check.discrepancies}")

    warning = ""
    if risultato_check.has_conflicts == "si":
        warning = f"ALLUCINAZIONE/DISCREPANZA RILEVATA RISPETTO AI TOOL:\n{risultato_check.discrepancies}"

    return {
        "fact_check_warning": warning if warning else None
    }