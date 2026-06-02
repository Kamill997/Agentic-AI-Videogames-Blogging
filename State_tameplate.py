from pydantic import BaseModel, Field
from typing_extensions import Literal
from langgraph.graph import MessagesState
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from typing_extensions import Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import Any, add_messages
from pydantic import BaseModel, Field
import os
from tavily import TavilyClient
import operator


load_dotenv() 
if not os.environ.get("OPENAI_API_KEY"):
    print("Attenzione: OPENAI_API_KEY non trovata nel file .env!")
if not os.environ.get("TAVILY_API_KEY"):
    print("Attenzione: TAVILY_API_KEY non trovata nel file .env!")

llm = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)
#llm_p = init_chat_model("groq:llama-3.1-8b-instant", temperature=0)
llm_p = init_chat_model("groq:llama-3.1-8b-instant", temperature=0)
#llm = init_chat_model("groq:llama-3.1-8b-instant", temperature=0)
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

class AgentInputState(MessagesState):
    """Input state for the full agent - only contains messages from user input."""
    pass

class AgentState(MessagesState):
    """
    Main state for the full multi-agent research system.

    Extends MessagesState with additional fields for research coordination.
    Note: Some fields are duplicated across different state classes for proper
    state management between subgraphs and the main workflow.
    """
    Request: str  #Richiesta iniziale
    classification_decision: Literal["Review", "News", "Suggestion"] #classificazione
    reasoning_classification: Optional[str] #Motivazione della classificazione
    research_brief: Optional[str] #Query dopo chiarificazione
    compose_res: str #Risultato finale


class ContentRouterSchema(BaseModel):
    """Classifies and routes user requests based on intent."""

    reasoning: str = Field(
        description="Short justification for the classification."
    )

    classification: Literal["Review", "News", "Suggestion", "Ignore"] = Field(
    description=(
            "The classification of the request content: "
            "'Review' for detailed evaluations, scores, opinions, or pros/cons about video games or hardware; "
            "'News' for current events, updates, or announcements related to video games; "
            "'Suggestion' for creative brainstorming, future topic ideas, editorials, or strategic content guidance."
            "'Ignore' for requests that do notdirectly pertain to the world of video games, which should be deprioritized and not processed further."    
        ),
    )

class ClarifyWithUser(BaseModel):
    """Schema for user clarification decision and questions."""
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )


class ResearchQuestion(BaseModel):
    """Schema for structured research brief generation."""

    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )

class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(description="Concise summary of the webpage content")

    
