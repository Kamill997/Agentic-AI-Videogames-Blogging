from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "cognitive"

driver = GraphDatabase.driver(uri, auth=(user, password))

def test():
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j OK' AS msg")
        print(result.single()["msg"])

test()
def create_post():
    with driver.session() as session:
        result = session.run("""
            CREATE (p:Post {title: $title, content: $content})
            RETURN p
        """, {
            "title": "Primo post",
            "content": "Ciao Neo4j!"
        })

        record = result.single()
        print(record["p"])

create_post()