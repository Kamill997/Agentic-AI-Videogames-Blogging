from langgraph.graph import StateGraph, START, END
from State_tameplate import TriageState
from triage_router import triage_router
from clarification_user import clarify_with_user,write_research_brief

def build_TriageRouterClarify_subgraph():

    builder = StateGraph(TriageState)

    builder.add_node("triage_router", triage_router)
    builder.add_node("clarify_with_user", clarify_with_user)
    builder.add_node("write_research_brief", write_research_brief)

    builder.add_edge(START, "triage_router")
    builder.add_edge("write_research_brief", END)

    return builder.compile()

TriageRouterClarify_subgraph = build_TriageRouterClarify_subgraph()