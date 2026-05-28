from schema import AgentState,llm
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from tools import tavily_search
from prompts.prompt_scelta_tool import research_agent_prompt

tools=[tavily_search]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

def llm_call(state: AgentState):
    
    """Analyze current state and decide on next actions.
    LLM decides whether to call a tool or not
    The model analyzes the current conversation state and decides whether to:
    1. Call search tools to gather more information
    2. Provide a final answer based on gathered information
    
    Returns updated state with the model's response.
    """
    return{
        "researcher_messages":[llm_with_tools.invoke([SystemMessage(content=research_agent_prompt), HumanMessage(content=state["research_brief"])])]
        }

def execute_tools(state: AgentState):
    """Execute all tool calls from the previous LLM response.
    
    Executes all tool calls from the previous LLM responses.
    Returns updated state with tool execution results.
    """
    tool_calls = state["researcher_messages"][-1].tool_calls
 
    # Execute all tool calls
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observations.append(tool.invoke(tool_call["args"]))
            
    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],

        ) for observation, tool_call in zip(observations, tool_calls)
    ]
    
    return {"researcher_messages": tool_outputs}