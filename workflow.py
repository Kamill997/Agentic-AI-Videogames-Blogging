from langgraph.graph import StateGraph, START, END
from triage_router import triage_router
from State_tameplate import AgentState, AgentInputState
from clarification_user import clarify_with_user, write_research_brief
from reasoner import llm_call,tool_node,route_after_llm
from merge_result import merge_result
from hitl_post import hitl_post, refine_proposal
from workflow_suggestion import compiled_reasoner_subgraph 
from workflow_triageRouter_clarifyRequest import TriageRouterClarify_subgraph
from route_after_triage import router_after_triage
from add_node import create_post_node_in_neo4j

workflow = StateGraph(AgentState, input_schema=AgentInputState)

workflow.add_node("triage_unit", TriageRouterClarify_subgraph)
workflow.add_node("router_after_triage",router_after_triage)
workflow.add_node("llm_call", llm_call)
workflow.add_node("tools", tool_node)
workflow.add_node("merge_result",merge_result)
workflow.add_node("hitl_post", hitl_post)
workflow.add_node("refine_proposal", refine_proposal)  # Nodo di passaggio per il feedback dell'utente
workflow.add_node("reasoner_subgraph", compiled_reasoner_subgraph )
workflow.add_node("create_post_node_in_neo4j",create_post_node_in_neo4j)

workflow.add_edge(START, "triage_unit")
workflow.add_edge("triage_unit","router_after_triage")
workflow.add_conditional_edges(
    "llm_call",
    route_after_llm,
    {
        "tools": "tools",
        "merge_result": "merge_result"
    }
)
workflow.add_edge("tools", "llm_call")
workflow.add_edge("merge_result","hitl_post")
workflow.add_edge("reasoner_subgraph", "hitl_post")

app = workflow.compile()
