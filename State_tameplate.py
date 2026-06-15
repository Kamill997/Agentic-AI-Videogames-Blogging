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

class AgentState(MessagesState): #Stato principale 
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
        
class TriageState(MessagesState): #stato del sottografo del triage 
    query: str #Query 
    classification_decision: Literal["Review", "News", "Suggestion","Planning"] #classificazione
    reasoning_classification: Optional[str] #pensiero di classificazione
    triage_messages: Annotated[list, add_messages] 

class StateSuggestion(MessagesState): #stato del sottografo suggestion
    query: str #Query scritta dall'utente
    suggestion_messages: Annotated[list, add_messages]
    merge_result: Optional[str]

class PlanningState(MessagesState): #Stato del planning node 
    query: str 
    planning_messages: Annotated[list, add_messages]
    active_plan: Optional[str] 
    pending_proposal: str  
    next_action: Optional[str] 
    message: Optional[str] 

class PlanningCommand(BaseModel): #uscita del planner_node 
    action: Literal["SHOW_MESSAGE", "DO_RESEARCH", "DELETE_EXISTING", "POP_NEXT","INTERACTION", "NONE"]
    message: str

class PlanExtraction(BaseModel): #uscita strutturata dell'executer node per estrarre le query del Planning 
    """Schema per l'estrazione delle query dal piano editoriale."""
    queries: List[str] = Field(
        description="La lista delle singole query/post estratti dalla bozza. Devono essere pulite da numeri (1, 2) o bullet points."
    )
    

class ContentRouterSchema(BaseModel): #uscita del triage router
    """Classifica e instrada le richieste degli utenti in base all'intento"""
    reasoning: str = Field(
        description="Breve giustificazione per la classificazione fatta"
    )
    classification: Literal["Review", "News", "Suggestion", "Ignore","Planning"] = Field(
   description=(
    "La classificazione del contenuto della richiesta: "
    "'Review' per valutazioni dettagliate, voti, opinioni o pro/contro su videogiochi o hardware; "
    "'News' per eventi d'attualità, aggiornamenti o annunci relativi ai videogiochi; "
    "'Suggestion' per brainstorming creativo, idee per argomenti futuri, editoriali o guida strategica ai contenuti; "
    "'Planning' per richieste di creazione, gestione, approvazione o avanzamento di un calendario editoriale giornaliero o di un piano di pubblicazione; "
    "'Ignore' per richieste che non riguardano direttamente il mondo dei videogiochi, le quali dovrebbero essere deprioritizzate e non ulteriormente elaborate."    ),
    )

class ClarifyWithUser(BaseModel): #uscita del clarify_with_user  
    """Output strutturato per la decisione di chiarimenti ed eventuali domande di chiarimento dell'utente."""
    need_clarification: bool = Field(description="Indica se all'utente deve essere posta una domanda di chiarimento",)
    question: str = Field(description="Domanda di chiarimento da sottoporre all'utente",)

class ResearchQuestion(BaseModel): #uscite del write_research_brief
    """Uscita strutturata della query completa includendo tutte le chiarificazioni utente"""
    game_name: str = Field(description="Il nome del videogioco principale oggetto della ricerca.")
    research_brief: str = Field(description="La query di ricerca completa generata",)


class InfoPostReview(BaseModel): #usato per estrarre info per aggiungere il nodo review 
    titolo: str = Field(description="Un titolo estratto o generato per il post MA che permetta di capire che è una recensione il gioco che si sta recensendo")
    gioco: str = Field(description="Il nome del videogioco principale recensito")
    case_editrici: List[str] = Field(description="Lista separata di ogni casa editrice o software house trovata.")
    genere: List[str] = Field(default=[],description="Lista dei generi del gioco. REGOLA TASSATIVA: Separa SEMPRE i generi composti in elementi singoli. Es: se il testo dice 'Action-Avventura' o 'Action/RPG', tu devi restituire ['Action', 'Avventura'] o ['Action', 'RPG']. Usa l'iniziale maiuscola.")
    overview: str = Field(description="Un riassunto conciso di tutto ciò di cui si parla nel post, in modo da avere una panormaica COMPLETA del contenuto")

class InfoPostNews(BaseModel): #usato per estrarre info per aggiungere il nodo news
    titolo: str = Field(description="Un titolo estratto o generato per il post")
    titoli_interessati: List[str] = Field(default_factory=list, description="Lista dei titoli di giochi o franchise menzionati nella news")
    case_editrici: List[str] = Field(description="Lista separata di ogni casa editrice o software house trovata.")
    overview: str = Field(description="Un riassunto conciso di tutto ciò di cui si parla nel post, in modo da avere una panormaica COMPLETA del contenuto")
