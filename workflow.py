from langgraph.graph import StateGraph, START, END
from schema import State
from triage_router import triage_router

workflow = StateGraph(State)
def agent_node(state: State) -> dict:
    # Non fa assolutamente nulla e lascia passare il flusso
    return {}

workflow.add_node("triage_router", triage_router)
workflow.add_node("agent", agent_node)

workflow.add_edge(START, "triage_router")
workflow.add_edge("agent", END)

app = workflow.compile()

if __name__ == "__main__":
    input_test = {
        "Request": "Puoi scrivermi una guida passo passo su come battere il primo boss su elden ring?",
        "messages": []
    }
    stato_finale = app.invoke(input_test)
    print(f"Decisione del Router: {stato_finale.get('classification_decision')}")
    print(f"Risposta finale: {stato_finale['messages'][-1].content}")