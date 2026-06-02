from datetime import datetime

from langgraph.prebuilt import ToolNode
from State_tameplate import AgentState,llm_p
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from prompts.prompt_ricerca_tavily import research_agent_prompt_review,research_agent_prompt_News
from tools.tavily_search_tool import tavily_search_tool
from tools.RAG_tool import RAG_tool

#tools=[tavily_search]
tools=[tavily_search_tool,RAG_tool]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm_p.bind_tools(tools,parallel_tool_calls=False)

def llm_call(state: AgentState):
    """Analyze current state and decide on next actions.
    LLM decides whether to call a tool or not
    The model analyzes the current conversation state and decides whether to:
    1. Call search tools to gather more information
    2. Provide a final answer based on gathered information
    
    Returns updated state with the model's response.
    """    
    messages = state.get("messages", [])
    
    if state["classification_decision"] == "News":
        data_di_oggi = datetime.now().strftime("%d %B %Y") 
        system_prompt = research_agent_prompt_News.format(data=data_di_oggi)
    else:
        # Per "Review" o "Suggestion" usiamo il prompt standard pulito
        system_prompt = research_agent_prompt_review

    invoke_messages = [SystemMessage(content=system_prompt)] + messages
    
    # 4. Ora l'LLM può leggere i risultati del tool e rispondere!
    return {
        "messages": [llm_with_tools.invoke(invoke_messages)]
    }

tool_node = ToolNode(tools)

def route_after_llm(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "merge_result"