from typing import Literal
from langgraph.graph import END
from State_template import AgentState
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command, interrupt
from prompts.prompt_rifinitura_bozza import prompt_rifinitura
from State_template import llm

def hitl_post(state: AgentState) -> Command[Literal["refine_proposal","create_post_node_in_neo4j","triage_unit"]]:
    """
    Elabora il risultato unito per la revisione umana.
    Questa funzione può essere utilizzata per formattare l'output finale, aggiungere eventuali dati necessari
    Argomenti:
    state (AgentState): Lo stato corrente dell'agente, che include il risultato unito.
    """
    proposta = state.get("merge_result")
    decision = state.get("classification_decision")

    warning_rag = state.get("fact_check_warning") # Recuperiamo il warning
    descrizione_ui = f"### Bozza della Recensione/News corrente:\n\n{proposta}"
    if warning_rag:
        descrizione_ui = f"### {warning_rag}\n\n---\n\n" + descrizione_ui


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
            #"description": f"### Bozza della Recensione/News corrente:\n\n{proposta}",
            "description": descrizione_ui,

        }
        response = interrupt([request])[0]
        tipo_risposta = response["type"]

        if tipo_risposta == "accept" :
            print(response)
            return Command(goto="create_post_node_in_neo4j", update={"merge_result": proposta})

        
        elif tipo_risposta == "ignore":
            return Command(goto=END)
        
        elif tipo_risposta == "edit":
            dati_ricevuti = response.get("args", {})
            testo_modificato = response["args"]["args"]["bozza"]            
            messaggio_edit = (
                "*Il testo è stato corretto manualmente nell'editor:*\n\n"
                f"{testo_modificato}"
            )
            return Command(
                goto="create_post_node_in_neo4j",
                update={
                    "merge_result": testo_modificato,
                    "messages": [AIMessage(content=messaggio_edit)]
                }
            )
        elif tipo_risposta == "response":
            feedback_utente = response.get("args", "")
            messaggio_response = f"**Richiesta dell'utente:**\n> {feedback_utente}"
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
                "description": f"### Suggerimento pubblicazione post:\n\n{proposta}",
        }
        response = interrupt([request])[0]
        tipo_risposta = response["type"]

        if tipo_risposta == "accept" :
            return Command(goto="triage_unit", update={"query":proposta,"classification_decision": None,"merge_result": None,"user_feedback":None})
        elif tipo_risposta == "ignore":
            return Command(goto=END)
        
        elif tipo_risposta == "edit":
            dati_ricevuti = response.get("args", {})
            testo_modificato = response["args"]["args"]["suggerimento"]
            return Command(
                goto="triage_unit",
                update={"query": testo_modificato, "classification_decision": None, "merge_result": None, "reasoning_classification": None}
            )
    
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
