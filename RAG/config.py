
from langchain_huggingface import HuggingFaceEmbeddings

percorso_DB_RAG = "./chroma_db"
nome_db_RAG = "recensioni"
modello_embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")