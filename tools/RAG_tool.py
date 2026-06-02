from State_tameplate import tavily_client
from langchain_core.tools import tool

@tool
def RAG_tool(query:str)->str:
    """
    Interroga il database vettoriale privato per recuperare informazioni ESCLUSIVAMENTE su giochi ed eventi fino al 2023 incluso.
     ATTENZIONE - REGOLA TASSATIVA DI ESCLUSIONE: 
    NON USARE MAI questo strumento se il gioco, la news o l'evento sono successive al 2023. 
    Questo database NON contiene dati recenti. Per qualsiasi gioco uscito dal 2024 in poi, usa solo tavily_search.
    """
    return