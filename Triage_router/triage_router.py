from typing import Literal
from langgraph.types import Command
from prompts.prompt_triage import triage_system_prompt, default_triage_instructions, default_background, triage_user_prompt
from State_template import ContentRouterSchema, TriageState
from State_template import llm
from langgraph.graph import  END
from langchain_core.messages import AIMessage,HumanMessage

llm_router = llm.with_structured_output(ContentRouterSchema) 

def triage_router(state: TriageState) -> Command[Literal["clarify_and_write_brief",END]]:
    """Analyze the request content to decide the appropriate topic."""

    blog_request = state.get("query")
    
    system_prompt = triage_system_prompt.format(background=default_background,triage_instructions=default_triage_instructions)

    user_prompt = triage_user_prompt.format(user_query=blog_request)

    result = llm_router.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    primo_messaggio = HumanMessage(content=blog_request)
    print(primo_messaggio)
    if result.classification == "Review":
        goto = "clarify_and_write_brief"
        update = {
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
            "triage_messages": [primo_messaggio]
        }
    elif result.classification == "News":
        goto = "clarify_and_write_brief"
        update = {
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
            "triage_messages": [primo_messaggio]
        }
    elif result.classification == "Suggestion":
        goto = END
        update = {
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
    elif result.classification == "Planning":
        goto = END
        update = {
            "classification_decision": result.classification,
            "reasoning_classification": result.reasoning,
        }
        
    elif result.classification == "Ignore":
        goto = END
        update = {"triage_messages": [AIMessage(content="Richiesta non pertinente...")]}
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update)