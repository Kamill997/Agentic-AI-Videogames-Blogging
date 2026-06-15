from langgraph.graph import END, StateGraph
from State_tameplate import PlanningState
from Planning.reasoner_plunning import planner_node, router_after_planner,route_after_research,research_node,hitl_planning_node,tool_node_planning
from Planning.executer_planning import executor_node

def build_reasoner_subgraph():

    planning_builder = StateGraph(PlanningState)
    planning_builder.set_entry_point("planner_node")

    planning_builder.add_node("planner_node", planner_node)
    planning_builder.add_node("router_after_planner", router_after_planner)
    planning_builder.add_node("research_node", research_node)
    planning_builder.add_node("tool_node_planning", tool_node_planning)
    planning_builder.add_node("hitl_planning_node", hitl_planning_node)
    planning_builder.add_node("executor_node", executor_node)
    
    planning_builder.add_edge("planner_node", "router_after_planner")
    planning_builder.add_edge("tool_node_planning", "research_node")
    planning_builder.add_conditional_edges("research_node", route_after_research, {
        "tool_node_planning": "tool_node_planning",
        "hitl_planning_node": "hitl_planning_node"
    })
    planning_builder.add_edge("executor_node", END)

    return planning_builder.compile()

compiled_planning_subgraph = build_reasoner_subgraph()





