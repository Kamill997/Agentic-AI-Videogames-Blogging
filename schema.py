from pydantic import BaseModel, Field
from typing_extensions import Literal
from langgraph.graph import MessagesState
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from typing_extensions import Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
import os
from tavily import TavilyClient
import operator

load_dotenv() 
if not os.environ.get("GROQ_API_KEY"):
    print("Attenzione: GROQ_API_KEY non trovata nel file .env!")
if not os.environ.get("TAVILY_API_KEY"):
    print("Attenzione: TAVILY_API_KEY non trovata nel file .env!")

llm = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)
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
    Request: str
    classification_decision: Literal["Review", "Guide", "Suggestion"]
    reasoning_classification: Optional[str]
    research_brief: Optional[str]
    researcher_messages: list[BaseMessage]
    # Messages exchanged with the supervisor agent for coordination
    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages]
    # Raw unprocessed research notes collected during the research phase
    #raw_notes: Annotated[list[str], operator.add] = []
    # Processed and structured notes ready for report generation
    # Final formatted research report
    #final_report: str

load_dotenv() 
if not os.environ.get("GROQ_API_KEY"):
    print("Attenzione: GROQ_API_KEY non trovata nel file .env!")

llm = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)

class ContentRouterSchema(BaseModel):
    """Classifies and routes user requests based on intent."""

    reasoning: str = Field(
        description="Short justification for the classification."
    )

    classification: Literal["Review", "Guide", "Suggestion", "Ignore"] = Field(
    description=(
            "The classification of the request content: "
            "'Review' for detailed evaluations, scores, opinions, or pros/cons about video games or hardware; "
            "'Guide' for functional step-by-step instructions, walkthroughs, gameplay help, puzzles, or unlock mechanics; "
            "'Suggestion' for creative brainstorming, future topic ideas, editorials, or strategic content guidance."
            "Ignore' for requests that do notdirectly pertain to the world of video games, which should be deprioritized and not processed further."    
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
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )

class ResearchQuestion(BaseModel):
    """Schema for structured research brief generation."""

    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )

class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(description="Concise summary of the webpage content")

    
