
import re
from langchain_core.tools import tool
import json
import requests
from State_tameplate import RisoluzioneGioco,llm_p

def clean_title(text: str) -> str:
    """
    Rimuove simboli speciali (™, ®, ©) e normalizza gli spazi
    per rendere equo il confronto testuale tra stringhe.
    """
    text = text.lower()
    text = re.sub(re.compile(r'[™®©]'), '', text)
    text = re.sub(re.compile(r'\d+'), '', text)
    text = re.sub(re.compile(r'\s+'), ' ', text).strip()
    return text

def trova_id_gioco(gioco_richiesto: str)-> tuple:
    """
    Usa l'API di Steam e l'LLM per ottenere l'AppID del gioco.
    Restituisce l'intero (AppID) se trovato, altrimenti None.
    """
    
    try:
        nome_pulito_base = clean_title(gioco_richiesto)
        url_ricerca = f"https://store.steampowered.com/api/storesearch/?term={nome_pulito_base}&l=italian&cc=IT"
        risultato = requests.get(url_ricerca, timeout=6).json()
        items = risultato.get("items", [])
        
        if not items:
            return  None, f"Nessun risultato trovato su Steam per '{gioco_richiesto}'"
            
        lista_candidati = "\n".join([f"- ID: {item['id']} | Nome: {item['name']}" for item in items[:15]])
            
        prompt = f"""
        Sei un esperto di videogiochi. L'utente cerca: "{gioco_richiesto}".
        Ecco i candidati da Steam:
        {lista_candidati}
        
        Individua il gioco base corretto.
        """
        
        llm_strutturato = llm_p.with_structured_output(RisoluzioneGioco)
        risposta_llm: RisoluzioneGioco = llm_strutturato.invoke(prompt)
        
        if risposta_llm.appid is None:
            return None, f"Non ho trovato il gioco '{gioco_richiesto}'."
            
        return risposta_llm.appid, risposta_llm.nome_ufficiale_steam

    except Exception as e:
        return None, f"Errore tecnico: {str(e)}"
 
def estrai_recensioni(tipo_recensione: str, recensione_url: str) -> tuple:
    """
    Funzione di supporto per interrogare l'API di Steam
    e pulire i testi delle recensioni.
    Restituisce una tupla: (lista_recensioni, punteggio_globale)
    """
    params = {
        "filter": "recent",            
        "language": "italian",       
        "review_type": tipo_recensione, 
        "num_per_page": 3            
    }
    
    try:
        res = requests.get(recensione_url, params=params, timeout=6).json()
        reviews = res.get("reviews", [])
        summary = res.get("query_summary", {})
 
        risultati_formattati = []
        for r in reviews:
            testo = r.get("review", "")
            if len(testo) > 500:
                testo = testo[:497] + "..."
            testo = testo.replace("\n", " ").strip()
            risultati_formattati.append(testo)
        
        if not risultati_formattati:
            risultati_formattati = ["Nessuna recensione rilevante trovata di questo tipo in italiano."]
            
        return {
            "recensioni": risultati_formattati,
        }
        
    except Exception:
        return {
            "recensioni": ["Errore tecnico durante il recupero delle recensioni."],

        }

@tool
def recensioni_utenti_steam(game_name: str, ragionamento: str) -> str:
    """
    Recupera le 3 recensioni utente più utili POSITIVE e NEGATIVE, 
    insieme al conteggio totale dei voti della community.
    ragionamento: DEVI TASSATIVAMENTE scrivere un nuovo pensiero aggiornato OGNI VOLTA che chiami il tool.
    """
    id_gioco, titolo_gioco = trova_id_gioco(game_name)
    if not id_gioco:
        return json.dumps({"stato": "errore", "dettaglio": titolo_gioco}, ensure_ascii=False)

    recensione_url = f"https://store.steampowered.com/appreviews/{id_gioco}?json=1"

    dati_positivi = estrai_recensioni("positive", recensione_url)
    dati_negativi = estrai_recensioni("negative", recensione_url)


    return json.dumps({
        "stato": "successo",
        "gioco_rilevato": titolo_gioco,
        "steam_appid": id_gioco,
        "analisi_community": {
            "top_3_recensioni_positive": dati_positivi["recensioni"],
            "top_3_recensioni_negative": dati_negativi["recensioni"]
        }
    }, indent=2, ensure_ascii=False)

@tool
def ottieni_prezzo_gioco(game_name: str,ragionamento:str) -> str:
    """
    Recupera il prezzo attuale, l'eventuale percentuale di sconto e indica se il gioco 
    è attualmente gratuito (Free to Play) su Steam
    Usa questo tool per valutare il rapporto qualità/prezzo all'interno di una recensione.
    ragionamento: DEVI TASSATIVAMENTE scrivere un nuovo pensiero aggiornato OGNI VOLTA che chiami il tool, spiegando il perchè è stato invocato il tool

    """
    id_gioco, titolo_gioco = trova_id_gioco(game_name)
    if not id_gioco:
        return json.dumps({"stato": "errore", "dettaglio": titolo_gioco}, ensure_ascii=False)

    url_prezzo = f"https://store.steampowered.com/api/appdetails?appids={id_gioco}&l=italian&cc=IT"
    
    try:
        res = requests.get(url_prezzo, timeout=6).json()
        if not res or not res.get(str(id_gioco), {}).get("success"):
            return json.dumps({"stato": "errore", "dettaglio": f"Impossibile recuperare il prezzo per '{titolo_gioco}'"}, ensure_ascii=False)
        data = res[str(id_gioco)]["data"]

        is_free = data.get("is_free", False)
        
        if is_free:
            info_prezzo = {
                "gratuito": True,
                "prezzo_attuale": "Free to Play",
                "prezzo_originale": "0,00€",
                "sconto_percentuale": 0
            }
        else:
            price_overview = data.get("price_overview")
            if not price_overview:
                return json.dumps({
                    "stato": "avviso", 
                    "dettaglio": f"Il gioco '{titolo_gioco}' esiste su Steam ma al momento non ha un prezzo visibile (potrebbe essere in arrivo o rimosso dallo store)."
                }, ensure_ascii=False)
                
            prezzo_attuale = price_overview.get("final_formatted", "")            
            prezzo_originale = price_overview.get("initial_formatted", "")
            sconto = price_overview.get("discount_percent", 0)

            if sconto == 0:
                prezzo_originale = prezzo_attuale

            info_prezzo = {
                "gratuito": False,
                "prezzo_attuale": prezzo_attuale,
                "prezzo_originale": prezzo_originale,
                "sconto_percentuale": sconto
            }
            
        return json.dumps({
            "stato": "successo",
            "gioco_rilevato": titolo_gioco,
            "steam_appid": id_gioco,
            "dati_commerciali": info_prezzo
        }, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"stato": "errore", "dettaglio": f"Errore durante l'estrazione del prezzo: {str(e)}"}, ensure_ascii=False)