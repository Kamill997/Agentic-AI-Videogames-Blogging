from langgraph.graph import StateGraph, START, END
from State_tameplate import AgentState, AgentInputState
from reasoner import llm_call,tool_node,route_after_llm
from merge_result import merge_result
from hitl_post import hitl_post, refine_proposal
from Suggestion.workflow_suggestion import compiled_suggestion_subgraph 
from route_after_triage import router_after_triage
from add_node import create_post_node_in_neo4j
from Planning.workflow_planning import compiled_planning_subgraph
from Triage_router.triage_router import triage_router
from Triage_router.workflow_triageRouter_clarifyRequest import TriageRouterClarify_subgraph



workflow = StateGraph(AgentState, input_schema=AgentInputState)

workflow.add_node("triage_unit", TriageRouterClarify_subgraph)
workflow.add_node("router_after_triage",router_after_triage)
workflow.add_node("llm_call", llm_call)
workflow.add_node("tools", tool_node)
workflow.add_node("merge_result",merge_result)
workflow.add_node("hitl_post", hitl_post)
workflow.add_node("refine_proposal", refine_proposal) 
workflow.add_node("suggestion_subgraph", compiled_suggestion_subgraph )
workflow.add_node("create_post_node_in_neo4j",create_post_node_in_neo4j)
workflow.add_node("planning_subgraph",compiled_planning_subgraph)

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
workflow.add_edge("suggestion_subgraph", "hitl_post")
workflow.add_conditional_edges(
    "planning_subgraph",
    lambda state: "triage_unit" if state.get("next_action") == "VAI_AL_TRIAGE" else END,
    {
        "triage_unit": "triage_unit",
        END: END
    }
)

app = workflow.compile()
