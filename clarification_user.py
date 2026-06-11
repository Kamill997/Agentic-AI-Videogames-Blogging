from langgraph.graph import END

from State_tameplate import TriageState, ClarifyWithUser, ResearchQuestion
from prompts.prompt_chiarificazione_richiesta_utente import clarify_news_instructions,clarify_review_instructions,transform_messages_into_research_topic_prompt
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.types import Command
from typing import Literal
from langgraph.types import interrupt, Command
from State_tameplate import llm_p
from neo4j_connection import neo4j_driver



def clarify_with_user(state: TriageState) -> Command[Literal["clarify_with_user", "write_research_brief"]]:
    """
    Determine if the user's request contains sufficient information to proceed with research.
    
    Uses structured output to make deterministic decisions and avoid hallucination.
    Routes to either research brief generation or ends with a clarification question.
    """
    structured_output_model = llm_p.with_structured_output(ClarifyWithUser)
    classification= state.get("classification_decision")

    if classification == "Review":
        default_prompt=clarify_review_instructions
    if classification == "News":
        default_prompt=clarify_news_instructions


    conversation_history = default_prompt.format(messages=state.get("triage_messages", []))

    message = HumanMessage(content=conversation_history)
    response = structured_output_model.invoke([message])

    if response.need_clarification:
        user_answer = interrupt(response.question)
        return Command(goto="clarify_with_user", update={"triage_messages": [AIMessage(content=response.question),HumanMessage(content=str(user_answer))]} )
    else:
        return Command(goto="write_research_brief")

def write_research_brief(state: TriageState):
    """
    Transform the conversation history into a comprehensive research brief.
    
    Uses structured output to ensure the brief follows the required format
    and contains all necessary details for effective research.
    """
    structured_output_model = llm_p.with_structured_output(ResearchQuestion)
    response = structured_output_model.invoke([
        HumanMessage(content=transform_messages_into_research_topic_prompt.format(
            messages=get_buffer_string(state.get("triage_messages", []))
        ))
    ])
    print(f"QUERY CREATA:{response.research_brief}")
    classificazione = state.get("classification_decision") 
    post_trovati = cerca_post_per_parola(response.game_name, classificazione)
    lista_formattata = "\n".join([f"• **{p['title']}** (Categoria: {p['tipo']})" for p in post_trovati])
    if post_trovati:
       
        request = {
            "action_request": {
                "action": "Verifica Duplicati", 
                "args": {"trovati": post_trovati}},
            "config": {
                "allow_accept": True, 
                "allow_ignore": True},
            "description": (
                f" Ho trovato dei contenuti esistenti per **{response.game_name}**:\n\n"
                f"{lista_formattata}\n\n"
                "Vuoi procedere con la creazione di un nuovo post o annullare?"
            ),
        }
        risposta = interrupt([request])[0]
        if risposta["type"] == "ignore":
            return Command(goto=END, update={"classification_decision": "Ignore"})
    return {
        "query":response.research_brief
    }

def cerca_post_per_parola(parola: str, tipo_post: str):
    """
    Cerca post filtrando per tipo (News o Review) e per parola chiave nel titolo.
    """
    query = """
    MATCH (p:Post {tipo_post: $tipo})
    // Converte il titolo in minuscolo e rimuove i caratteri speciali per il confronto
    WHERE toLower(p.titolo) =~ '.*' + toLower(replace($parola, ' ', '.*')) + '.*'
    RETURN p.titolo AS title, p.tipo_post AS tipo
    """
    with neo4j_driver.session() as session:
        result = session.run(query, {"parola": parola, "tipo": tipo_post})
        return [record.data() for record in result]