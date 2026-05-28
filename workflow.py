from langgraph.graph import StateGraph, START, END
from triage_router import triage_router
from schema import AgentState, AgentInputState
from clarification_user import clarify_with_user, write_research_brief
from llm_call import llm_call, execute_tools

workflow = StateGraph(AgentState, input_schema=AgentInputState)

workflow.add_node("triage_router", triage_router)
workflow.add_node("clarify_with_user", clarify_with_user)
workflow.add_node("llm_call", llm_call)
workflow.add_node("execute_tools", execute_tools)
workflow.add_node("write_research_brief", write_research_brief)

workflow.add_edge(START, "triage_router")
workflow.add_edge("write_research_brief", "llm_call")
workflow.add_edge("llm_call", "execute_tools")
workflow.add_edge("execute_tools", END)
app = workflow.compile()
