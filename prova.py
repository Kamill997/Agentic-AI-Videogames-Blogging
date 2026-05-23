from langchain.chat_models import init_chat_model
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model("groq:llama-3.3-70b-versatile", temperature=0)
search = TavilySearchResults()

# =========================
# STEP 1: scegli gioco
# =========================
step1_prompt = """
Scegli UN solo videogioco recente (2024-2026) molto interessante per fare una recensione, di genere Sparatutto.

Regole:
- deve esistere davvero
- deve essere già rilasciato (non solo annunciato)
- preferibilmente AAA o molto discusso
- rispondi SOLO con il nome del gioco
"""

game = llm.invoke(step1_prompt).content.strip()

print("🎮 Gioco scelto:", game)

# =========================
# STEP 2: ricerca web
# =========================
query = f"{game} recensione meccaniche del gameplay e caratteristiche principali"
results = search.invoke(query)

context = "\n".join(r.get("content", "") for r in results)

# =========================
# STEP 3: review finale
# =========================
final_prompt = f"""
Consigliami a parole tue come iniziare una review del videogioco e indicami i punti pro e contro da attenzionare: {game}
Usa SOLO le informazioni sotto.
Regole:
- Dimmi solo l'incipits della recensione ed i punti forti e deboli del gioco
- Usa parole tue senza copiare frasi di recensioni già fatte
- massimo 2 righe di incipits
- non inventare nulla
- i pro e contro devono essere basati SOLO sulle informazioni fornite, non aggiungere nulla di tuo
- i pro e contro devono essere specifici, non generici (es. "buona grafica" è troppo generico, meglio "grafica con ottimo uso dei colori ma modelli poligonali poco dettagliati")
- DIchiara la data di rilascio e delle piattaforme
- Forniscimi informazioni sulle prestazioni e ottimizzazione su PC, ma SOLO se disponibili
INFORMAZIONI:
{context}

"""

response = llm.invoke(final_prompt)

print("\n📝 REVIEW:\n")
print(response.content)