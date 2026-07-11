from datetime import datetime
from langgraph.prebuilt import ToolNode
from State_template import AgentState,llm_p
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from prompts.prompt_scelta_tool import research_agent_prompt_review,research_agent_prompt_News
from tools.tavily_search_tool import tavily_search_tool
from tools.RAG_tool import RAG_tool
from tools.steam_tool import recensioni_utenti_steam,ottieni_prezzo_gioco
from tools.neo4j_tool import cerca_post_gioco

tools=[tavily_search_tool,RAG_tool,recensioni_utenti_steam,ottieni_prezzo_gioco,cerca_post_gioco]
llm_with_tools = llm_p.bind_tools(tools,parallel_tool_calls=False)

def llm_call(state: AgentState):
    """Analizza lo stato attuale e decidi le azioni successive.
    LLM decide se utilizzare uno strumento di ricerca o meno.
    Il modello analizza lo stato attuale della conversazione e decide se:
    1. Utilizzare strumenti di ricerca per raccogliere ulteriori informazioni.
    2. Fornire una risposta definitiva basata sulle informazioni raccolte.
    """    
    messages = state.get("messages", [])
    data_di_oggi = datetime.now().strftime("%d %B %Y") 
    richiesta_utente = state.get("query")

    if state["classification_decision"] == "News":
        system_prompt = research_agent_prompt_News.format(data=data_di_oggi,richiesta=richiesta_utente)
    else:
        system_prompt = research_agent_prompt_review.format(richiesta=richiesta_utente,data=data_di_oggi)

    invoke_messages = [SystemMessage(content=system_prompt)] + messages

    return {"messages": [llm_with_tools.invoke(invoke_messages)]}

tool_node = ToolNode(tools)

def route_after_llm(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "merge_result"