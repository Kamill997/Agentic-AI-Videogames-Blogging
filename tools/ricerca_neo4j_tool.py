from langchain_core.tools import tool

@tool
def get_recent_posts_tool(ragionamento:str) -> str:

    """
    Usa questo tool esclusivamente quando devi suggerire un post, no quando l'utente chiede di fare una news o una recensione esplicitamente.
    Usa questo tool SOLO QUANDO DEVI SUGGERIRE un post all'utente basandoti sullo storico per evitare di suggerire argomenti ridondanti già pubblicati.
    Questo tool interroga il database Neo4j per recuperare i post più recenti pubblicati sul blog, al fine di evitare di suggerire argomenti simili o identici a quelli già trattati di recente.
    ragionamento: è la spiegazione del motivo per cui stai chiamando questo tool, spiega il perchè della chiamata e cosa stai cercando di ottenere.
    """
    mock_data = """
            [
        {
            "id": 1,
            "titolo": "Top 10 Indie Games 2026",
            "topic": "News",
            "data": "28/05/2026"
        },
        {
            "id": 2,
            "titolo": "Rimandata l'uscita di GTA 6",
            "topic": "News",
            "data": "28/05/2026"
        },
        {
            "id": 3,
            "titolo": "Top 5 giochi più giocati al mondo",
            "topic": "News",
            "data": "25/05/2026"
        },

    """
    return mock_data
