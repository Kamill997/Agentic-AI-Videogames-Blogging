from typing import Literal
from langgraph.graph import END
from State_tameplate import AgentState
from langgraph.types import Command
from langchain_core.messages import HumanMessage

def router_after_triage(state: AgentState) -> Command[Literal["suggestion_subgraph","llm_call","planning_subgraph", END]]:
    decision = state.get("classification_decision")
    query = state.get("query")
    
    # Prepariamo il dizionario di update. 
    # Specifichiamo che vogliamo aggiornare la chiave "messages"
    query_message = HumanMessage(content=query)
    if decision == "Suggestion":
        return Command(goto="suggestion_subgraph")
    elif decision in ["News", "Review"]:
        return Command(goto="llm_call", update={"messages": [HumanMessage(content=query)]})
    elif decision=="Planning":
        return Command(goto="planning_subgraph")
    else:
        return Command(goto=END)