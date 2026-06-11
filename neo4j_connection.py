import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

class Neo4jConnectionManager:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(URI, auth=AUTH)
                cls._driver.verify_connectivity()
                print("[NEO4J] Connessione globale inizializzata con successo.")
            except Exception as e:
                print(f"[NEO4J] Errore critico di connessione all'avvio: {e}")
                cls._driver = None
        return cls._driver

# Questa riga espone la connessione pronta per gli altri file
neo4j_driver = Neo4jConnectionManager.get_driver()