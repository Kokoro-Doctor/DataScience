from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import numpy as np

# Predefined knowledge base documents
knowledge_base_docs = [
    "The stock market closed higher today with technology stocks leading the gains.",
    "The Federal Reserve announced an interest rate hike amid inflation concerns.",
    "Oil prices surged due to supply constraints and geopolitical tensions.",
    "Cryptocurrency markets saw a sharp decline following regulatory crackdowns.",
    "Major banks reported better-than-expected quarterly earnings.",
    "The housing market shows signs of cooling off as mortgage rates rise.",
    "Unemployment rates dropped to a new low, signaling strong economic growth.",
    "Central banks around the world are coordinating policies to stabilize currencies.",
    "The government unveiled new stimulus packages aimed at supporting small businesses.",
    "Trade negotiations between major economies have stalled, impacting global markets.",
]

# Initialize embeddings + FAISS vector store
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
documents = [Document(page_content=doc) for doc in knowledge_base_docs]
vector_store = FAISS.from_documents(documents, embedding_model)

def embed_text(text: str) -> np.ndarray:
    """
    Embed text using Ollama and ensure it's valid for FAISS.
    """
    emb = embedding_model.embed_query(text)  # Returns list[float]
    emb = np.array(emb, dtype=np.float32)

    if emb.ndim != 1:
        raise ValueError(f"Embedding has wrong shape: {emb.shape}")
    
    if np.any(np.isnan(emb)):
        raise ValueError("❌ Embedding contains NaNs!")
    
    return emb.reshape(1, -1)

def retrieve_similar_docs(query_embedding: np.ndarray, top_k: int = 3):
    """
    Retrieve top_k similar documents using FAISS.
    """
    try:
        docs = vector_store.similarity_search_by_vector(query_embedding[0], k=top_k)
        return [doc.page_content for doc in docs]
    except Exception as e:
        print(f"❌ FAISS search failed: {e}")
        return []

'''

def test_rag_pipeline():
    query = "Nvidia's stock price rose after positive analyst reports."
    print(f"Embedding query: {query}")
    
    query_embedding = embed_text(query)
    print(f"Embedding shape: {query_embedding.shape}")
    
    top_docs = retrieve_similar_docs(query_embedding, top_k=3)
    
    if top_docs:
        print("\nTop similar documents:")
        for i, doc in enumerate(top_docs, 1):
            print(f"{i}. {doc}")
    else:
        print("❌ No similar documents retrieved.")

if __name__ == "__main__":
    test_rag_pipeline()

'''      