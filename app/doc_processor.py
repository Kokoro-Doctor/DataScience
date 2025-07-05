import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from app.embeddings import embedding_model

persist_dir = "db"

def load_and_chunk_pdf(data_dir):
    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200
    )

    for filename in os.listdir(data_dir):
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(data_dir, filename))
            docs = loader.load()
            chunks = splitter.split_documents(docs)

            for chunk in chunks:
                chunk.metadata["source"] = filename
            all_chunks.extend(chunks)

    return all_chunks

def create_chroma_index(chunks, persist_directory=persist_dir):
    if not chunks:
        raise ValueError("No chunks provided for indexing.")
    db = Chroma.from_documents(
        chunks,
        embedding_model,
        persist_directory=persist_directory
    )
    db.persist()
    return db

if __name__ == "__main__":
    # test script
    DATA_DIR = "data"
    chunks = load_and_chunk_pdf(DATA_DIR)
    print(f"✅ Loaded and chunked: {len(chunks)} chunks.")
    create_chroma_index(chunks)
    print("✅ Chroma DB created.")
