import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from dotenv import load_dotenv
from prompts.prompts import (
    triage_system_prompt, 
    default_triage_instructions, 
    default_background, 
    triage_user_prompt
)
from schema import ContentRouterSchema, State

load_dotenv() 
if not os.environ.get("GROQ_API_KEY"):
    print("Attenzione: GROQ_API_KEY non trovata nel file .env!")


llm = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)
llm_router = llm.with_structured_output(ContentRouterSchema) 

def triage_router(state: State) -> Command[Literal["agent", "__end__"]]:
    """Analyze the request content to decide the appropriate topic."""
    blog_request = state["Request"]
    
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

    if result.classification == "News":
        print(f"Classification: NEWS - Processing gaming updates or announcements")
        goto = "agent"
        update = {
            "messages": [{"role": "user", "content": f"Handle this gaming News request: \n\n{blog_request}"}],
            "classification_decision": result.classification,
        }
    elif result.classification == "Review":
        print(f"Classification: REVIEW - Processing game or hardware evaluation")
        goto = "agent"
        update = {
            "messages": [{"role": "user", "content": f"Handle this gaming Review request: \n\n{blog_request}"}],
            "classification_decision": result.classification,
        }
    elif result.classification == "Guide":
        print(f"Classification: GUIDE - Processing gameplay help or puzzle solution")
        goto = "agent"
        update = {
            "messages": [{"role": "user", "content": f"Handle this gaming Guide request: \n\n{blog_request}"}],
            "classification_decision": result.classification,
        }
    elif result.classification == "Event":
        print(f"Classification: EVENT - Processing calendar items, showcase or tournament coverage")
        goto = "agent"
        update = {
            "messages": [{"role": "user", "content": f"Handle this gaming Event request: \n\n{blog_request}"}],
            "classification_decision": result.classification,
        }
    elif result.classification == "Advice":
        print(f"Classification: ADVICE - Processing brainstorming or content ideas")
        goto = "agent"
        update = {
            "messages": [{"role": "user", "content": f"Handle this gaming Advice request: \n\n{blog_request}"}],
            "classification_decision": result.classification,
        }
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
        
    return Command(goto=goto, update=update)