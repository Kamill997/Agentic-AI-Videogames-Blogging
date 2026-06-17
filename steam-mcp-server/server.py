import json
import requests
import re
from difflib import SequenceMatcher
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Steam Editorial Server")

def clean_title(text: str) -> str:
    """
    Rimuove simboli speciali (™, ®, ©) e normalizza gli spazi
    per rendere equo il confronto testuale tra stringhe.
    """
    text = text.lower()
    text = re.sub(re.compile(r'[™®©]'), '', text)
    text = re.sub(re.compile(r'\s+'), ' ', text).strip()
    return text

def trova_id_gioco(gioco: str) -> tuple:
    """
    Cerca l'AppID su Steam basandosi SOLO sul nome del gioco.
    Ritorna (appid, nome_gioco) se lo trova con un'affidabilità > 50%.
    Ritorna (None, messaggio_errore) se il gioco non esiste o è un falso positivo.
    """
    url_prendi_id = f"https://store.steampowered.com/api/storesearch/?term={gioco}&l=italian&cc=IT"
    try:
        risultato = requests.get(url_prendi_id, timeout=6).json()
        
        if not risultato.get("items"):
            return None, f"Il gioco '{gioco}' non è stato trovato su Steam"
        
        corrispondenza_gioco= None
        highest_similarity = -1
        
        for item in risultato["items"]:
            nome_ripulito= clean_title(item["name"])
            similarity = SequenceMatcher(None, gioco, nome_ripulito).ratio()
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                corrispondenza_gioco = item
  
        if highest_similarity < 0.5:
            return None, f"Nessuna corrispondenza affidabile trovata su Steam per '{gioco}'"
            
        return corrispondenza_gioco["id"], corrispondenza_gioco["name"]
        
    except Exception as e:
        return None, f"Errore imprevisto durante la comunicazione con i server di Steam: {str(e)}"


@mcp.tool()
def numero_giocatori_attivi(game_name: str) -> str:
    """
    Restituisce il numero di utenti che stanno giocando in questo preciso momento.
    Richiede esclusivamente il nome del gioco (es. 'Elden Ring').
    """
    id_gioco, titolo_gioco = trova_id_gioco(game_name) # Se trova_id_gioco ha restituito None, titolo_gioco contiene la spiegazione dell'errore
    if not id_gioco:
        return json.dumps({"stato": "errore", "dettaglio": titolo_gioco}, ensure_ascii=False)

    url_numero_giocatori = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={id_gioco}"
    try:
        players_res = requests.get(url_numero_giocatori, timeout=6).json()
        n_giocatori_attivi = players_res.get("response", {}).get("player_count", "Dato non disponibile")
        
        return json.dumps({
            "stato": "successo",
            "gioco_rilevato": titolo_gioco,
            "giocatori_attivi_ora": n_giocatori_attivi
        }, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"stato": "errore", "dettaglio": f"Impossibile recuperare i dati in tempo reale: {str(e)}"}, ensure_ascii=False)