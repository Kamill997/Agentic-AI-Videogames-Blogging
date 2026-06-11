from datetime import datetime
from typing import Annotated, List, TypedDict
from pydantic import BaseModel, Field
from typing_extensions import Literal
from langgraph.graph import MessagesState
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from typing_extensions import Optional
from langgraph.graph import MessagesState
from langgraph.graph.message import BaseMessage, add_messages
from pydantic import BaseModel, Field
import os
from tavily import TavilyClient

load_dotenv() 
if not os.environ.get("OPENAI_API_KEY"):
    print("Attenzione: OPENAI_API_KEY non trovata nel file .env!")
if not os.environ.get("TAVILY_API_KEY"):
    print("Attenzione: TAVILY_API_KEY non trovata nel file .env!")

llm_p = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)
llm = init_chat_model("groq:llama-3.1-8b-instant", temperature=0)
llm_x=init_chat_model("groq:openai/gpt-oss-120b", temperature=0)

tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

class AgentInputState(TypedDict):
    """Input state for the full agent - only contains messages from user input."""
    query:str

class AgentState(MessagesState):
    """
    Main state for the full multi-agent research system.

    Extends MessagesState with additional fields for research coordination.
    Note: Some fields are duplicated across different state classes for proper
    state management between subgraphs and the main workflow.
    """
    query:str
    classification_decision: Literal["Review", "News", "Suggestion"] #classificazione
    merge_result: str #Risultato finale dopo merge
    user_feedback: Optional[str] #Feedback testuale dell'utente (se fornito)
    link_source: List[str] # link estratti da Tavily nel nodo merge
        
class TriageState(MessagesState):
    query: str #Query 
    classification_decision: Literal["Review", "News", "Suggestion"] #classificazione
    reasoning_classification: Optional[str] #pensiero di classificazione
    triage_messages: Annotated[list, add_messages] 

class StateSuggestion(MessagesState):
    query: str #Query scritta dall'utente
    suggestion_messages: Annotated[list, add_messages]
    merge_result: Optional[str]
    
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

class ClarifyWithUser(BaseModel): #usato da clarify_with_user
    """Schema for user clarification decision and questions."""
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )

class ResearchQuestion(BaseModel): #usato da write_research_brief
    """Schema for structured research brief generation."""
    game_name: str = Field(description="Il nome del videogioco principale oggetto della ricerca.")
    research_brief: str = Field(description="La query di ricerca completa generata",)

class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(description="Concise summary of the webpage content")

class InfoPostReview(BaseModel): #usato per estrarre info per aggiungere il nodo review
    titolo: str = Field(description="Un titolo estratto o generato per il post")
    gioco: str = Field(description="Il nome del videogioco principale recensito")
    case_editrici: List[str] = Field(description="Lista separata di ogni casa editrice o software house trovata.")
    genere: List[str] = Field(default=[],description="Lista dei generi del gioco. REGOLA TASSATIVA: Separa SEMPRE i generi composti in elementi singoli. Es: se il testo dice 'Action-Avventura' o 'Action/RPG', tu devi restituire ['Action', 'Avventura'] o ['Action', 'RPG']. Usa l'iniziale maiuscola.")
class InfoPostNews(BaseModel): #usato per estrarre info per aggiungere il nodo news
    titolo: str = Field(description="Un titolo estratto o generato per il post")
    titoli_interessati: List[str] = Field(default_factory=list, description="Lista dei titoli di giochi o franchise menzionati nella news")
    case_editrici: List[str] = Field(description="Lista separata di ogni casa editrice o software house trovata.")

