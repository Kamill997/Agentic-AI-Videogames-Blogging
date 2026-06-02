from State_tameplate import tavily_client
from langchain_core.tools import tool

@tool
def tavily_search_tool(query:str,ragionamento: str)->str:
    """
    Effettua ricerche sul web per raccogliere informazioni aggiornate.
    Args:
        query: Le parole chiave reali da cercare su internet.
        ragionamento: Motivo del perchè è stato invocato il tool, e cosa pensi di ottenere
        DEVI scrivere un nuovo pensiero aggiornato OGNI VOLTA che chiami il tool.

    """
    result=tavily_client.search(query,include_images=False, max_results=1,exclude_domains=["reddit.com","Instagram.com", "youtube.com"])
    # Format output for consumption
    return result

