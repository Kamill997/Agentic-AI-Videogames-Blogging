from datetime import datetime
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from typing_extensions import Literal
from langgraph.graph import END
from State_tameplate import PlanningState,llm_x,PlanningCommand
from prompts.prompt_planner import prompt_planner,research_agent_prompt
from tools.neo4j_tool import check_active_plan_tool,get_planning_context_tool,check_game_already_reviewed_tool,check_news_already_published_tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from tools.tavily_search_tool import tavily_search_tool


tools=[tavily_search_tool,get_planning_context_tool,check_game_already_reviewed_tool,check_news_already_published_tool]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm_x.bind_tools(tools,parallel_tool_calls=False)

def planner_node(state: PlanningState) -> dict:

    richiesta=state.get("query")    
    active_plan = check_active_plan_tool.invoke({})
    prompt = prompt_planner.format(query=richiesta,active_plan=active_plan)
    model = llm_x.with_structured_output(PlanningCommand)
    decision = model.invoke(prompt)
    return {
        "active_plan": active_plan,
        "next_action": decision.action,
        "message": decision.message,
        "planning_messages":[HumanMessage(content=richiesta)]
    }

def router_after_planner(state: PlanningState)->Command[Literal["research_node","hitl_planning_node","executor_node",END]]:
    azione = state.get("next_action")
    
    if azione == "DO_RESEARCH":
        return Command(goto="research_node")  
          
    elif azione in ["SHOW_MESSAGE"]:
        return Command(goto="hitl_planning_node")
    
    elif azione in ["INTERACTION"]:
        return Command(goto="hitl_planning_node")
    
    elif azione in ["DELETE_EXISTING", "POP_NEXT", "COMMIT_TO_DB"]:
        return Command(goto="executor_node")
        
    else:
        return Command(goto=END)
    

def research_node(state: PlanningState):
    """
    Il Reasoner: Analizza lo stato, usa i tool per raccogliere info,
    ragiona e alla fine produce la proposta di piano.
    """
    data_di_oggi = datetime.now().strftime("%d %B %Y")
    system_prompt = research_agent_prompt.format(data=data_di_oggi)
    
    messages = [SystemMessage(content=system_prompt)] + state.get("planning_messages", [])

    response = llm_with_tools.invoke(messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"planning_messages": [response]}
    else:
        return {
            "planning_messages": [response],
            "pending_proposal": response.content
        }

tool_node_planning = ToolNode(tools, messages_key="planning_messages")


def route_after_research(state: PlanningState):
    last_message = state["planning_messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node_planning"
    return "hitl_planning_node"


def hitl_planning_node(state: PlanningState) -> Command:
    """Nodo centralizzato per tutte le interruzioni e i messaggi all'utente."""
    azione = state.get("next_action")
    
    # ==========================================
    # CASO 1: Azione a vuoto / Informativa (chiede di eliminare un piano o di andare avanti ma non esiste il piano)
    # ==========================================
    if azione == "SHOW_MESSAGE":
        messaggio= state.get("message", "Non è presente nessun plunning")    
        request = {
            "action_request": {
                "action": "Avviso di Sistema",
                "args": {"messaggio": messaggio}
            },
            "config": {
                "allow_accept": True,   
                "allow_ignore": False, 
                "allow_respond": False, 
                "allow_edit": False     
            },
            "description": f"### {messaggio}",
        }
        interrupt([request])
        return Command(
            goto=END,
            update={"planning_messages": [AIMessage(content=messaggio)],
                    "next_action": "FINISCI"}
        )
        
    # ==========================================
    #  Revisione della Bozza (Dopo DO_RESEARCH)
    # ==========================================

    elif azione == "DO_RESEARCH":
        bozza_attuale = state.get("pending_proposal", "Nessuna proposta disponibile.")
        
        request = { 
            "action_request": {
                "action": "Revisione Editoriale",
                "args": {"bozza": bozza_attuale}
            },
            "config": {
                "allow_accept": True,
                "allow_ignore": True,
                "allow_respond": False,
                "allow_edit": True,
            },
            "description": f"Pianificazione del piano editoriale:\n\n{bozza_attuale}\n",
        }
        
        response = interrupt([request])[0]
        tipo_risposta = response["type"]

        if tipo_risposta == "accept":
            return Command(goto="executor_node")            
        elif tipo_risposta == "ignore":
            return Command(goto=END,update={"next_action": "FINISCI"})
            
        elif tipo_risposta == "edit":
            nuova_bozza = response["args"]["args"]["bozza"]
            return Command( goto="executor_node", update={"pending_proposal": nuova_bozza, "planning_messages": [AIMessage(content="Piano revisionato manualmente.")]})
   
    
    # ==========================================
    # CASO 3: Richiesta di interazione "Vuoi prima eliminarlo?"
    # ==========================================
    elif azione == "INTERACTION":
        piano_attuale = state.get("active_plan")
        messaggio = (f"È presente un planning esistente:\n"
                f"--- PIANO ATTUALE ---\n{piano_attuale}\n---------------------\n"
                "Vuoi eliminare il piano esistente?")        
        request = {
            "action_request": {
                "action": "Plunning esistente, vuoi sovrasciverlo?",
                "args": {"domanda": messaggio}
            },
            "config": {
                "allow_accept": True, 
                "allow_ignore": True,   
                "allow_respond": False,  
                "allow_edit": False
            },
            "description": f"{messaggio}",
        }
        
        response = interrupt([request])[0]
        tipo_risposta = response["type"]
        
        if tipo_risposta == "accept":
            messaggio_ai = AIMessage(content=messaggio)
            messaggio_umano = HumanMessage(content="Sì, voglio eliminare il piano.")
            return Command(goto="executor_node", update={"planning_messages": [messaggio_ai, messaggio_umano]})
        
        elif tipo_risposta == "ignore": 
            return Command(goto=END, update={"next_action": "FINISCI"})
        
        else: 
            return Command(goto=END, update={"next_action": "FINISCI"})
        
    return Command(goto=END, update={"next_action": "FINISCI"})

  