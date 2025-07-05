import os
import time
import hashlib
import logging
from multiprocessing import Pool, cpu_count
from dotenv import load_dotenv
from tqdm import tqdm

from langchain_community.document_loaders import PDFMinerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Config
DATA_PATH = os.getenv("DATA_PATH", "data")
CHROMA_PATH = os.getenv("CHROMA_PATH", "chromadb_store")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 64))

# Setup logging
logging.basicConfig(filename='ingest.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Helper to filter pages
def is_valid_page(content: str) -> bool:
    content = content.strip()
    if len(content) < 100:
        return False
    ascii_ratio = sum(c.isascii() for c in content) / len(content)
    text_ratio = sum(c.isalnum() for c in content) / len(content)
    if ascii_ratio < 0.7 or text_ratio < 0.2:
        return False
    return True

# Process one PDF file
def process_pdf(file_path: str):
    try:
        loader = PDFMinerLoader(file_path)
        docs = loader.load()
        filtered_docs = [doc for doc in docs if is_valid_page(doc.page_content)]

        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = splitter.split_documents(filtered_docs)

        logging.info(f"{file_path} => Pages: {len(docs)}, Valid: {len(filtered_docs)}, Chunks: {len(chunks)}")
        return chunks
    except Exception as e:
        logging.error(f"Failed to process {file_path}: {e}")
        return []

# Deduplication based on file hash
def hash_file(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_all_pdf_paths(data_path):
    pdfs = []
    for root, _, files in os.walk(data_path):
        for file in files:
            if file.endswith('.pdf'):
                pdfs.append(os.path.join(root, file))
    return pdfs

if __name__ == "__main__":
    start = time.time()
    print("📥 Starting optimized ingestion pipeline...")

    pdf_paths = get_all_pdf_paths(DATA_PATH)
    print(f"🔎 Found {len(pdf_paths)} PDFs.")

    with Pool(cpu_count()) as pool:
        all_chunks = list(tqdm(pool.imap_unordered(process_pdf, pdf_paths), total=len(pdf_paths)))

    # Flatten
    all_chunks = [chunk for doc_chunks in all_chunks for chunk in doc_chunks if chunk.page_content.strip()]
    print(f"🧩 Total chunks after filtering: {len(all_chunks)}")

    if len(all_chunks) == 0:
        print("⚠️ No valid content found to embed. Exiting.")
        exit()

    # Load fast embedding model
    print("🔗 Loading embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name=EMBED_MODEL, encode_kwargs={"batch_size": 32})

    # Create and persist ChromaDB
    print("💾 Storing in ChromaDB...")
    db = None
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        if db is None:
            db = Chroma.from_documents(batch, embedding_model, persist_directory=CHROMA_PATH)
        else:
            db.add_documents(batch)

    db.persist()
    print(f"✅ Done. Time taken: {time.time() - start:.2f}s")
