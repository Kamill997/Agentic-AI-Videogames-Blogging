import json
from langgraph.graph import END
from State_tameplate import TriageState, ClarifyWithUser, ResearchQuestion
from prompts.prompt_chiarificazione_richiesta_utente import clarify_news_instructions,clarify_review_instructions,transform_messages_into_research_topic_prompt
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, get_buffer_string
from langgraph.types import Command
from typing import Literal
from langgraph.types import interrupt, Command
from State_tameplate import llm_p
from tools.neo4j_tool import check_game_already_reviewed_tool,check_news_already_published_tool

def clarify_and_write_brief(state: TriageState) -> Command[Literal["clarify_and_write_brief", END]]:
    """
    Gestisce i chiarimenti con l'utente (se necessari) e, una volta ottenute 
    le info sufficienti, procede alla stesura del brief e verifica dei duplicati.
    """
    classification = state.get("classification_decision")
    triage_messages = state.get("triage_messages", [])

    structured_clarify_model = llm_p.with_structured_output(ClarifyWithUser)
    
    if classification == "Review":
        default_prompt = clarify_review_instructions
    elif classification == "News":
        default_prompt = clarify_news_instructions
    else:
        default_prompt = clarify_news_instructions

    conversation_history = default_prompt.format(messages=triage_messages)
    message = HumanMessage(content=conversation_history)
    response_clarify = structured_clarify_model.invoke([message])

    if response_clarify.need_clarification:
        user_answer = interrupt(response_clarify.question)
        
        return Command(
            goto="clarify_and_write_brief",  
            update={"triage_messages": [AIMessage(content=response_clarify.question), HumanMessage(content=str(user_answer))]}
        )

    structured_brief_model = llm_p.with_structured_output(ResearchQuestion)
    prompt_query = transform_messages_into_research_topic_prompt.format(messages=get_buffer_string(triage_messages))
    response_brief = structured_brief_model.invoke([HumanMessage(content=prompt_query)])
    
    tool_result = {"is_duplicate": False, "message": "Nessun controllo eseguito", "data": []}
    
    if classification == "Review":
        tool_result = check_game_already_reviewed_tool.invoke({"game_name": response_brief.game_name})
    elif classification == "News":
        tool_result = check_news_already_published_tool.invoke({"argomento": response_brief.game_name})
    
    if tool_result.get("is_duplicate") == True:
        
        records = tool_result.get("data", [])
        segnalazioni_match = []
        
        for i, doc in enumerate(records, 1):
            titolo_doc = doc.get("titolo", "Titolo non disponibile")
            overview_doc = doc.get("overview", "Nessun abstract o riassunto presente")

            blocco = (
                f"Match #{i}: {titolo_doc}**\n"
                f"> *Abstract/Overview:* {overview_doc}\n"
                f"---"
            )
            segnalazioni_match.append(blocco)
            
        messaggio_match = "\n".join(segnalazioni_match)
    
        request = {
            "action_request": {
                "action": "Verifica Duplicati", 
                "args": {
                    "risultato_database": tool_result 
                }
            },
            "config": {
                "allow_accept": True, 
                "allow_ignore": True
            },
            "description": (
                f"**ATTENZIONE: {tool_result['message'].upper()}**\n\n"
                f"Il sistema ha rilevato i seguenti contenuti simili già presenti nel database:\n\n"
                f"{messaggio_match}\n\n"
                f"Vuoi procedere comunque con la creazione del nuovo post o preferisci annullare?"
            ),
        }
            
        risposta = interrupt([request])[0] 
        
        if risposta.get("type") == "ignore":
            return Command(goto=END, update={"classification_decision": "Ignore"})
        
    return Command(goto=END, update={"query": response_brief.research_brief})