from State_tameplate import AgentState, ClarifyWithUser, ResearchQuestion
from prompts.prompt_chiarificazione_richiesta_utente import clarify_news_instructions,clarify_review_instructions,transform_messages_into_research_topic_prompt
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.types import Command
from typing import Literal
from langgraph.types import interrupt, Command
from State_tameplate import llm


def clarify_with_user(state: AgentState) -> Command[Literal["clarify_with_user", "write_research_brief"]]:
    """
    Determine if the user's request contains sufficient information to proceed with research.
    
    Uses structured output to make deterministic decisions and avoid hallucination.
    Routes to either research brief generation or ends with a clarification question.
    """
    structured_output_model = llm.with_structured_output(ClarifyWithUser)
    classification= state.get("classification_decision")
    if classification == "Review":
        default_prompt=clarify_review_instructions
    if classification == "News":
        default_prompt=clarify_news_instructions

   # prompt_text = default_prompt.format(messages=state.get("Request", ""))
    #prompt_text = default_prompt.format(messages=state.get("Request", ""))
    conversation_history = default_prompt.format(messages=state.get("messages", []))
    message = HumanMessage(content=conversation_history)
    response = structured_output_model.invoke([message])

    if response.need_clarification:
        user_answer = interrupt(response.question)
        return Command(goto="clarify_with_user", update={"messages": [AIMessage(content=response.question),HumanMessage(content=str(user_answer))]} )
    else:
        return Command(goto="write_research_brief")

def write_research_brief(state: AgentState):
    """
    Transform the conversation history into a comprehensive research brief.
    
    Uses structured output to ensure the brief follows the required format
    and contains all necessary details for effective research.
    """
    structured_output_model = llm.with_structured_output(ResearchQuestion)
    response = structured_output_model.invoke([
        HumanMessage(content=transform_messages_into_research_topic_prompt.format(
            messages=get_buffer_string(state.get("messages", []))
        ))
    ])
    return {
        "messages": response.research_brief
    }