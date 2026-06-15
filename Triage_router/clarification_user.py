from langgraph.graph import END
from State_tameplate import TriageState, ClarifyWithUser, ResearchQuestion
from prompts.prompt_chiarificazione_richiesta_utente import clarify_news_instructions,clarify_review_instructions,transform_messages_into_research_topic_prompt
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.types import Command
from typing import Literal
from langgraph.types import interrupt, Command
from State_tameplate import llm_p
from neo4j_connection import neo4j_driver


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
        
        return Command(goto="clarify_and_write_brief",  update={"triage_messages": [AIMessage(content=response_clarify.question),HumanMessage(content=str(user_answer))]})

    structured_brief_model = llm_p.with_structured_output(ResearchQuestion)
    response_brief = structured_brief_model.invoke([HumanMessage(content=transform_messages_into_research_topic_prompt.format(messages=get_buffer_string(triage_messages)))])
    
    post_trovati = cerca_post_per_parola(response_brief.game_name, classification)
    
    if post_trovati:
        lista_formattata = "\n".join([f"**{p['title']}** (Categoria: {p['tipo']})\n *Overview:* {p['overview']}" for p in post_trovati])
        request = {
            "action_request": {
                "action": "Verifica Duplicati", 
                "args": {"trovati": post_trovati}
            },
            "config": {
                "allow_accept": True, 
                "allow_ignore": True
            },
            "description": (
                f" Ho trovato dei contenuti esistenti per {response_brief.game_name}:\n\n"
                f"{lista_formattata}\n\n"
                "Vuoi procedere con la creazione di un nuovo post o annullare?"
            ),
        }
        
        risposta = interrupt([request])[0]
        if risposta["type"] == "ignore":
            return Command(goto=END, update={"classification_decision": "Ignore"})
    return Command(goto=END, update={"query": response_brief.research_brief})

def cerca_post_per_parola(parola: str, tipo_post: str):
    """
    Cerca post filtrando per tipo (News o Review) e per parola chiave .
    """
    query = """
    MATCH (p:Post {tipo_post: $tipo})
    WHERE toLower(p.titolo) =~ '.*' + toLower(replace($parola, ' ', '.*')) + '.*'
       OR toLower(p.overview) =~ '.*' + toLower(replace($parola, ' ', '.*')) + '.*'
       OR toLower(p.content) =~ '.*' + toLower(replace($parola, ' ', '.*')) + '.*'   
    RETURN p.titolo AS title, p.tipo_post AS tipo, p.overview AS overview
    """
    with neo4j_driver.session() as session:
        result = session.run(query, {"parola": parola, "tipo": tipo_post})
        return [record.data() for record in result]