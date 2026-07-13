import asyncio
import logging
import os
import socket
import subprocess
import sys
import time
import concurrent.futures
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import tool

logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("mcp").setLevel(logging.CRITICAL)

MCP_HOST = "127.0.0.1"
MCP_PORT = 8765
MCP_SERVER_URL = f"http://{MCP_HOST}:{MCP_PORT}/mcp"
MCP_TIMEOUT_SECONDS = 90
SERVER_BOOT_TIMEOUT_SECONDS = 30

MCP_CONFIG = {
    "gaming_search": {
        "url": MCP_SERVER_URL,
        "transport": "streamable_http",
    }
}

_client = None
_server_process = None 


def _find_project_root(start: str, marker: str = "State_template.py") -> str:
    """Risale le cartelle da `start` finché non trova `marker` (root del progetto)."""
    path = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(path, marker)):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError(
                f"Impossibile trovare '{marker}' risalendo da {start}. "
                "Verifica la struttura del progetto."
            )
        path = parent


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ensure_server_running() -> None:
    """
    Avvia automaticamente il server MCP (mcp_server/search_server.py) come
    sottoprocesso in background SE non è già in ascolto su MCP_PORT.
    """
    global _server_process

    if _is_port_open(MCP_HOST, MCP_PORT):
        return 

    if _server_process is None or _server_process.poll() is not None:
        project_root = _find_project_root(os.path.dirname(os.path.abspath(__file__)))

        popen_kwargs = dict(
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            popen_kwargs["start_new_session"] = True 

        _server_process = subprocess.Popen(
            [sys.executable, "-m", "mcp_server.search_server"],
            **popen_kwargs,
        )
    deadline = time.monotonic() + SERVER_BOOT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if _is_port_open(MCP_HOST, MCP_PORT):
            return
        time.sleep(0.5)

    raise RuntimeError(
        f"Il server MCP non ha risposto entro {SERVER_BOOT_TIMEOUT_SECONDS}s "
        "dall'avvio automatico. Controlla i log avviandolo manualmente con "
        "'python -m mcp_server.search_server' per vedere l'errore."
    )


def _get_mcp_client() -> MultiServerMCPClient:
    global _client
    if _client is None:
        _client = MultiServerMCPClient(MCP_CONFIG)
    return _client


def _extract_text(result) -> str:
    if result is None:
        return ""
    if isinstance(result, tuple) and result:
        result = result[0]
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts = []
        for block in result:
            if isinstance(block, dict):
                parts.append(block.get("text", "") or block.get("content", "") or "")
            elif isinstance(block, str):
                parts.append(block)
            else:
                parts.append(getattr(block, "text", "") or "")
        return "\n".join(p for p in parts if p)
    if hasattr(result, "text"):
        return result.text or ""
    if hasattr(result, "content"):
        c = result.content
        return c if isinstance(c, str) else _extract_text(c)
    return str(result)

async def _run_mcp_search(query: str, ragionamento: str) -> str:
    client = _get_mcp_client()
    mcp_tools = await client.get_tools()
    
    search_tool = next((t for t in mcp_tools if t.name == "tavily_search_tool"), None)
    if search_tool is None:
        return "Il server MCP non espone il tool 'tavily_search_tool'."
        
    result = await search_tool.ainvoke({"query": query, "ragionamento": ragionamento})
    text = _extract_text(result).strip()
    return text if text else "Il server MCP non ha restituito alcun testo."

def _run_in_dedicated_loop(query: str, ragionamento: str) -> str:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            asyncio.wait_for(_run_mcp_search(query, ragionamento), timeout=MCP_TIMEOUT_SECONDS)
        )
    finally:
        loop.close()

@tool
def tavily_search_tool(query: str,ragionamento:str) -> str:
    """
    Effettua ricerche sul web per raccogliere informazioni aggiornate.
    Args:
        query: Le parole chiave reali da cercare su internet in ITALIANO.
        ragionamento: DEVI TASSATIVAMENTE scrivere un nuovo pensiero aggiornato OGNI VOLTA che chiami il tool, spiegando il perchè è stato invocato il tool
    """
    try:
        _ensure_server_running()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_dedicated_loop, query, ragionamento)
            return future.result(timeout=MCP_TIMEOUT_SECONDS + 10)
    except concurrent.futures.TimeoutError:
        return (f"La ricerca web non ha risposto entro {MCP_TIMEOUT_SECONDS}s. Procedo senza fonti web.")
    except Exception as e:
        return (f"Errore di comunicazione col Server MCP ({str(e)}). Procedo senza fonti web.")
