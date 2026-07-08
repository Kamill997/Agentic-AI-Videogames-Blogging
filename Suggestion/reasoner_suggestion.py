from datetime import datetime
import re
from langgraph.graph import END
from langgraph.prebuilt import ToolNode
from State_template import StateSuggestion,llm_x
from langchain_core.messages import SystemMessage
from prompts.prompt_suggetion import research_agent_prompt_suggestion
from tools.tavily_search_tool_vecchio import tavily_search_tool
from tools.neo4j_tool import get_planning_context_tool,check_game_already_reviewed_tool,check_news_already_published_tool,get_unreviewed_released_games_tool

tools=[tavily_search_tool,get_planning_context_tool,check_game_already_reviewed_tool,check_news_already_published_tool,get_unreviewed_released_games_tool]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm_x.bind_tools(tools,parallel_tool_calls=False)

def reasoning_suggestion_node(state: StateSuggestion):
    """
    Nodo di ragionamento per la generazione e validazione di nuovi suggerimenti editoriali.
    Gestisce autonomamente il loop di ricerca e bilanciamento storico.
    """
    messages = state.get("suggestion_messages", [])

    data_di_oggi = datetime.now().strftime("%d %B %Y") 
    prompt = research_agent_prompt_suggestion.format(data=data_di_oggi, richiesta=state.get("query", ""))
    invoke_messages = [SystemMessage(content=prompt)] + messages
    response = llm_with_tools.invoke(invoke_messages)
    update = {
        "suggestion_messages": [response]
    }

    if not (hasattr(response, "tool_calls") and response.tool_calls):
        match = re.search(r"<FINAL_QUERY>(.*?)</FINAL_QUERY>", response.content, re.IGNORECASE)
        if match:
            update["merge_result"] = match.group(1).strip()
        else:
            update["merge_result"] = "Query non trovata nel formato richiesto"

    return update

tool_node_suggestion = ToolNode(tools, messages_key="suggestion_messages")

def route_after_suggestion(state: StateSuggestion):
    last_message = state["suggestion_messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node_suggestion"
    return END

