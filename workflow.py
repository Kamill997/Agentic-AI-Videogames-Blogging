from langgraph.graph import StateGraph, START, END
from triage_router import triage_router
from State_tameplate import AgentState, AgentInputState
from clarification_user import clarify_with_user, write_research_brief
from llm_call import llm_call,tool_node,route_after_llm
from merge_result import merge_result

workflow = StateGraph(AgentState, input_schema=AgentInputState)

workflow.add_node("triage_router", triage_router)
workflow.add_node("clarify_with_user", clarify_with_user)
workflow.add_node("llm_call", llm_call)
workflow.add_node("tools", tool_node)
workflow.add_node("write_research_brief", write_research_brief)
workflow.add_node("merge_result",merge_result)


workflow.add_edge(START, "triage_router")
workflow.add_edge("write_research_brief", "llm_call")
workflow.add_conditional_edges(
    "llm_call",
    route_after_llm,
    {
        "tools": "tools",
        "merge_result": "merge_result"
    }
)
workflow.add_edge("tools", "llm_call")
workflow.add_edge("merge_result",END)
workflow.add_edge("llm_call",END)

app = workflow.compile()
