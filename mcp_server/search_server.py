
import os
import sys
import warnings
warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
from mcp.server.fastmcp import FastMCP
from State_template import tavily_client

mcp_server = FastMCP("GamingSearchServer", host="127.0.0.1", port=8765)

@mcp_server.tool()
def tavily_search_tool(query: str, ragionamento: str) -> str:
    """
    Effettua ricerche sul web per raccogliere informazioni aggiornate.
    Args:
        query: Le parole chiave reali da cercare su internet in ITALIANO.
        ragionamento: DEVI TASSATIVAMENTE scrivere un nuovo pensiero aggiornato OGNI VOLTA che chiami il tool, spiegando il perchè è stato invocato il tool
    """
    try:
        result = tavily_client.search(query,include_images=False,max_results=1,exclude_domains=["reddit.com","Instagram.com","threads.com", "youtube.com","facebook.com","ebay.com","tiktok.com", "www.dailymotion.com"])
        return str(result)
    except Exception as e:
        return f"Errore durante la ricerca su Tavily: {str(e)}"


if __name__ == "__main__":
    print("Server MCP avviato su http://127.0.0.1:8765/mcp", file=sys.stderr)
    mcp_server.run(transport="streamable-http")
