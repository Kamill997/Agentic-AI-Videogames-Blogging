from typing import Literal
from langgraph.types import Command
from prompts.prompt_triage import (
    triage_system_prompt, 
    default_triage_instructions, 
    default_background, 
    triage_user_prompt
)
from State_tameplate import ContentRouterSchema, AgentState
from State_tameplate import llm_p
from langgraph.graph import StateGraph, START, END

llm_router = llm_p.with_structured_output(ContentRouterSchema) 

def triage_router(state: AgentState) -> Command[Literal["clarify_with_user", "llm_call", END]]:
    """Analyze the request content to decide the appropriate topic."""
    blog_request = state["messages"]
    
    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=default_triage_instructions
    )

    user_prompt = triage_user_prompt.format(
        user_query=blog_request
    )

    result = llm_router.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    if result.classification == "Review":
        goto = "clarify_with_user"
        update = {
            #"messages": [{"role": "user", "content": f"Richiesta di recensione: {blog_request}"}],
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    elif result.classification == "News":
        goto = "clarify_with_user"
        update = {
            #"messages": [{"role": "user", "content": f"Richiesta di news: {blog_request}"}],
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    elif result.classification == "Suggestion":
        goto = "llm_call"
        update = {
            #"messages": [{"role": "user", "content": f"Richiesta di suggerimento: {blog_request}"}],
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    elif result.classification == "Ignore":
        goto = END
        update= {"Richiesta non pertinente ai videogiochi, classificata come 'Ignore'. Nessuna azione ulteriore intrapresa."}
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
        
    return Command(goto=goto, update=update)