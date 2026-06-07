from typing import Literal
from langgraph.graph import END
from State_tameplate import AgentState
from langgraph.types import Command
from langchain_core.messages import HumanMessage

def router_after_triage(state: AgentState) -> Command[Literal["reasoner_subgraph","llm_call", END]]:
    decision = state.get("classification_decision")
    query = state.get("query")
    
    # Prepariamo il dizionario di update. 
    # Specifichiamo che vogliamo aggiornare la chiave "messages"
    query_message = HumanMessage(content=query)

    if decision == "Suggestion":
        return Command(goto="reasoner_subgraph", update={"suggestion_messages": [query_message]})
    elif decision in ["News", "Review"]:
        return Command(goto="llm_call", update={"messages": [HumanMessage(content=query)]})
    else:
        return Command(goto=END)