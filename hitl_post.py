from typing import Literal
from langgraph.graph import END
from State_tameplate import AgentState
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command, interrupt
from prompts.prompt_rifinitura_bozza import prompt_rifinitura
from State_tameplate import llm

def hitl_post(state: AgentState) -> Command[Literal["refine_proposal",END,"triage_unit"]]:
    """
    Post-process the merged result for human-in-the-loop review.
    This function can be used to format the final output, add any necessary
    metadata, or prepare it for presentation to a human reviewer.
    Args:
        state (AgentState): The current state of the agent, which includes the merged result.
    """
    proposta = state.get("merge_result")
    decision = state.get("classification_decision")
    if decision in ["Review", "News"]:
        request = { 
            "action_request": {
                "action": "Revisione Editoriale",
                "args": {"bozza": proposta}
            },
            "config": {
                "allow_accept": True,   # Crea il tasto "Mark as Resolved" (Approva)
                "allow_ignore": True,   # Crea il tasto "Ignore" (Rifiuta/Annulla)
                "allow_respond": True,  # Mantiene sotto il box di testo per scrivere modifiche
                "allow_edit": True,    # Permette di modificare il testo prima di approvare
            },
            # Il testo della bozza apparirà nel corpo principale della pagina (Agent Inbox)
            "description": f"### Bozza della Recensione/News corrente:\n\n{proposta}",
        }
        response = interrupt([request])[0]
        tipo_risposta = response["type"]

        if tipo_risposta == "accept" :
            return Command(goto=END, update={"final_proposal": proposta})
        
        elif tipo_risposta == "ignore":
            return Command(goto=END)
        
        elif tipo_risposta == "edit":
            # Estraiamo il testo NUOVO che hai scritto tu direttamente sullo schermo
            testo_modificato_da_utente = response["args"].get("bozza", proposta)
            # Aggiorniamo lo stato con il TUO testo definitivo e mandiamo il grafo a END.
            # Non serve far lavorare l'LLM, visto che lo hai già corretto tu a mano!
            messaggio_edit = (
                "Il testo della bozza è stato corretto direttamente dall'utente nell'editor:\n\n"
                f"{testo_modificato_da_utente}"
            )
            return Command(
                goto=END,
                update={"final_proposal": testo_modificato_da_utente,
                        "messages":[AIMessage(content=messaggio_edit)]}
            )
        # Casistica C: Hai scritto un commento nel box in basso (es: "Rendilo più corto")
        elif tipo_risposta == "response":
            feedback_utente = response.get("args", "")
            messaggio_response = f"💬 **Richiesta dell'utente:**\n> {feedback_utente}"
            return Command(
                goto="refine_proposal",
                update={
                    "user_feedback": feedback_utente,
                    "messages": [HumanMessage(content=messaggio_response)] 
                }
            )
        else:
            raise ValueError(f"Azione UI non riconosciuta: {tipo_risposta}")
    
    elif decision == "Suggestion":
        request = { 
            "action_request": {
                "action": "Valutazione Suggerimento Editoriale",
                "args": {"suggerimento": proposta}
            },
            "config": {
                "allow_accept": True,   # Crea il tasto "Mark as Resolved" (Approva)
                "allow_ignore": True,   # Crea il tasto "Ignore" (Rifiuta/Annulla)
                "allow_edit": True,    # Permette di modificare il testo prima di approvare
            },
            # Il testo della bozza apparirà nel corpo principale della pagina (Agent Inbox)
            "description": f"### Suggerimento pubblicazione post:\n\n{proposta}",
        }
        response = interrupt([request])[0]
        tipo_risposta = response["type"]

        if tipo_risposta == "accept" :
            return Command(goto="triage_unit", update={"query":proposta,"classification_decision": None,"merge_result": None,"user_feedback":None})
        elif tipo_risposta == "ignore":
            return Command(goto=END)
        
        elif tipo_risposta == "edit":
            testo_modificato_da_utente = response["args"].get("bozza", proposta)
            return Command(
                goto="triage_unit",
                update={"query":testo_modificato_da_utente,"classification_decision": None,"merge_result": None,"reasoning_classification": None})

    
def refine_proposal(state: AgentState) -> Command[Literal["hitl_post"]]:
    
    richiesta_utente = state.get("user_feedback", "")
    bozza_da_modificare = state.get("merge_result")  
    system_prompt = prompt_rifinitura.format(bozza_attuale=bozza_da_modificare, feedback_utente=richiesta_utente)
    rielaborazione= llm.invoke([HumanMessage(content=system_prompt)] )

    bozza_rielaborata= rielaborazione.content
    messaggio_visuale = (
        " **[BOZZA AGGIORNATA DALL'AGENTE]\n**"
        " Ho applicato le modifiche richieste. Ecco la nuova versione della recensione:\n\n"
        f"{bozza_rielaborata}"
    )
    return Command(
        goto="hitl_post",
        update={
            "merge_result": bozza_rielaborata,
            "user_feedback": "", 
            "messages": [AIMessage(content=messaggio_visuale)]
        }
    )


    