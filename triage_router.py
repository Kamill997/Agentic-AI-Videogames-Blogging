import os
from typing import Literal
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from dotenv import load_dotenv
from prompts.prompts import (
    triage_system_prompt, 
    default_triage_instructions, 
    default_background, 
    triage_user_prompt
)
from schema import ContentRouterSchema, AgentState

load_dotenv() 
if not os.environ.get("GROQ_API_KEY"):
    print("Attenzione: GROQ_API_KEY non trovata nel file .env!")

llm = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)
llm_router = llm.with_structured_output(ContentRouterSchema) 

def triage_router(state: AgentState) -> Command[Literal["clarify_with_user", "llm_call"]]:
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
            "messages": [{"role": "user", "content": f"Richiesta di recensione: {blog_request}"}],
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    elif result.classification == "Guide":
        goto = "clarify_with_user"
        update = {
            "messages": [{"role": "user", "content": f"Richiesta di guida: {blog_request}"}],
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    elif result.classification == "Suggestion":
        goto = "llm_call"
        update = {
            "messages": [{"role": "user", "content": f"Richiesta di suggerimento: {blog_request}"}],
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
        
    return Command(goto=goto, update=update)