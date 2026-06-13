from langgraph.graph import END, StateGraph
from State_tameplate import StateSuggestion
from reasoner_suggestion import reasoning_suggestion_node, tool_node_suggestion,route_after_suggestion

def build_suggestion_subgraph():

    builder = StateGraph(StateSuggestion)
    builder.set_entry_point("reasoning_suggestion_node")

    builder.add_node("reasoning_suggestion_node", reasoning_suggestion_node)
    builder.add_node("tool_node_suggestion", tool_node_suggestion)
    
    builder.add_conditional_edges("reasoning_suggestion_node", route_after_suggestion, {
        "tool_node_suggestion": "tool_node_suggestion",
        END: END
    })
    builder.add_edge("tool_node_suggestion", "reasoning_suggestion_node")
    
    return builder.compile()

compiled_suggestion_subgraph= build_suggestion_subgraph()
