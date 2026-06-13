from langchain_core.messages import AIMessage
from langgraph.types import Command
from langgraph.graph import END
from neo4j_connection import neo4j_driver 
from State_tameplate import PlanningState,PlanExtraction,llm_p
from prompts.prompt_planner import prompt_estrazione

def executor_node(state: PlanningState):
    azione = state.get("next_action")
    bozza = state.get("pending_proposal", "")
    
    try:
        with neo4j_driver.session() as session:
            
            # ==========================================
            # 1) POP NEXT: Estrae, elimina e manda il segnale per il Triage
            # ==========================================
            if azione == "POP_NEXT":
                result = session.run(
                    """
                    MATCH (p:Pianificazione {stato: 'PENDING'})
                    WITH p ORDER BY COALESCE(p.ordine, 0) ASC LIMIT 1
                    WITH p, p.titolo AS extracted_query
                    DETACH DELETE p
                    RETURN extracted_query
                    """
                )
                record = result.single()
                
                if record and record["extracted_query"]:
                    query_corrente = record["extracted_query"]
                    
                    return Command(
                        goto=END, 
                        update={
                            "query": query_corrente,       # Inietta la query per il triage
                            "next_action": "VAI_AL_TRIAGE", # Segnale per il Grafo Padre
                            "planning_messages": [AIMessage(content=f"POP Eseguita. Task estratto: '{query_corrente}'.")]
                        }
                    )
                else:
                    return Command(
                        goto=END,
                        update={
                            "next_action": "FINISCI",
                            "planning_messages": [AIMessage(content=" Nessun nodo Pianificazione PENDING trovato. Coda vuota.")]
                        }
                    )

            # ==========================================
            # 2) DO_RESEARCH: Piano approvato, spacchetta, popola la coda e va al Triage
            # ==========================================
            elif azione == "DO_RESEARCH":

                llm_extractor = llm_p.with_structured_output(PlanExtraction)
                prompt= prompt_estrazione.format(bozza=bozza)
               
                estrazione = llm_extractor.invoke(prompt)
                queries_pulite = estrazione.queries
                
                if queries_pulite:
                    query_corrente = queries_pulite[0] # Il primo post va subito in esecuzione
                    
                    # Salva i restanti post su Neo4j come PENDING
                    for indice, q in enumerate(queries_pulite[1:], start=1):
                        session.run(
                            """
                            CREATE (p:Pianificazione {
                                titolo: $titolo,
                                ordine: $ordine,
                                stato: 'PENDING'
                            })
                            """,
                            titolo=q, ordine=indice
                        )
                    
                    return Command(
                        goto=END,  # Esce dal sottografo
                        update={
                            "query": query_corrente,
                            "next_action": "VAI_AL_TRIAGE", # Segnale per elaborare subito il primo post
                            "pending_proposal": "",         # Svuota la bozza consumata
                            "planning_messages": [AIMessage(content=f"Piano salvato in coda. Avvio immediato di: '{query_corrente}'.")]
                        }
                    )
                else:
                    return Command(
                        goto=END,
                        update={
                            "next_action": "FINISCI",
                            "planning_messages": [AIMessage(content="❌ Errore: l'LLM non ha estratto query valide dalla bozza.")]
                        }
                    )

            # ==========================================
            # 3) DELETE_EXISTING: Svuota la coda e ferma il flusso
            # ==========================================
            elif azione == "DELETE_EXISTING":
                session.run("MATCH (p:Pianificazione {stato: 'PENDING'}) DETACH DELETE p")
                return Command(
                    goto=END,
                    update={
                        "next_action": "FINISCI", # Segnale di stop per il Grafo Padre
                        "pending_proposal": "",
                        "planning_messages": [AIMessage(content="🗑️ Tutti i nodi Pianificazione PENDING sono stati eliminati.")]
                    }
                )

            # ==========================================
            # 4) INTERACTION: Svuota la coda e rimanda internamente a "research_node"
            # ==========================================
            elif azione == "INTERACTION":
                session.run("MATCH (p:Pianificazione {stato: 'PENDING'}) DETACH DELETE p")
                
                # Questo è l'unico caso che NON esce dal sottografo, 
                # ma devia internamente verso il nodo di ricerca.
                return Command(
                    goto="research_node", 
                    update={
                        "next_action": "DO_RESEARCH", # Cambia l'azione per preparare il terreno alla ricerca
                        "pending_proposal": "",
                        "planning_messages": [AIMessage(content="Vecchio piano rimosso. Avvio della ricerca per il nuovo piano...")]
                    }
                )

    except Exception as e:
        return Command(
            goto=END,
            update={
                "next_action": "FINISCI",
                "planning_messages": [AIMessage(content=f"Errore critico nell'Executor: {str(e)}")]
            }
        )

    # Fallback di sicurezza se l'azione non corrisponde a nessuna delle precedenti
    return Command(
        goto=END, 
        update={"next_action": "FINISCI"}
    )