# ✅ FILE: app/embeddings.py

import sys
import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Add root to path so `app.doc_processor` can be imported directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def create_or_load_chroma(persist_dir="db"):
    """
    Load Chroma DB if exists, else return None.
    """
    if os.path.exists(persist_dir) and os.path.exists(os.path.join(persist_dir, "chroma-collections.parquet")):
        print("📦 Found existing Chroma DB, loading it...")
        vectordb = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding_model,
        )
        return vectordb
    else:
        print("💾 Creating and saving new vector DB...")
        return None

def create_chroma_index(chunks, persist_dir="db"):
    """
    Create a Chroma vector store from chunks if not already present.
    """
    clean_chunks = []
    for chunk in chunks:
        if not isinstance(chunk, Document):
            continue
        if not isinstance(chunk.metadata, dict):
            chunk.metadata = {}
        clean_chunks.append(chunk)

    vectordb = Chroma.from_documents(
        documents=clean_chunks,
        embedding=embedding_model,
        persist_directory=persist_dir
    )
    print("✅ Vector store ready with", vectordb._collection.count())
    return vectordb


# ✅ Optional test run
if __name__ == "__main__":
    from app.doc_processor import load_and_chunk_pdf

    chunks = load_and_chunk_pdf("data/Synise Handbook.pdf")
    db = create_chroma_index(chunks)
    print("Index created with", db._collection.count())


