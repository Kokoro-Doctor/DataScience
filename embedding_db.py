import os
import uuid
from chromadb import PersistentClient
from langchain_community.embeddings import OllamaEmbeddings

persist_dir = os.path.abspath("chroma_db")
chroma_client = PersistentClient(path=persist_dir)

def get_chroma_collection():
    return chroma_client.get_or_create_collection(
        name="financial_news",
        metadata={"hnsw:space": "cosine"}
    )

collection = get_chroma_collection()

embedder = OllamaEmbeddings(model="mistral")  
def store_chunks(chunks, metadatas=None):
    if not chunks:
        print("⚠️ No chunks to store.")
        return 0, collection.count()

    ids = [str(uuid.uuid4()) for _ in chunks]
    embeddings = embedder.embed_documents(chunks)

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    stored_count = len(chunks)
    total_count = collection.count()
    print(f"✅ Stored {stored_count} chunks. Total in DB: {total_count}")
    return stored_count, total_count

def retrieve_similar_chunks(query_text, top_k=5):
    query_embedding = embedder.embed_query(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results["documents"][0] if results["documents"] else []

def get_all_documents():
    results = collection.peek()
    count = len(results["ids"])
    return count, None
