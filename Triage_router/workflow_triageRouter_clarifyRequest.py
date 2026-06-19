from langgraph.graph import StateGraph, START, END
from State_template import TriageState
from Triage_router.triage_router import triage_router
from Triage_router.clarification_user import clarify_and_write_brief

def build_TriageRouterClarify_subgraph():

    builder = StateGraph(TriageState)

    builder.add_node("triage_router", triage_router)
    builder.add_node("clarify_and_write_brief", clarify_and_write_brief)

    builder.add_edge(START, "triage_router")
    builder.add_edge("clarify_and_write_brief", END)

    return builder.compile()

TriageRouterClarify_subgraph = build_TriageRouterClarify_subgraph()