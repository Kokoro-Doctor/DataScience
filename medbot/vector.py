# vector.py

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm
import os

def create_or_load_vectorstore(persist_directory="chroma_db"):
    all_docs = []

    def load_all_pdfs(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                loader = PyMuPDFLoader(file_path)
                docs = loader.load()
                all_docs.extend(docs)
                print(filename)

    # Load PDFs
    load_all_pdfs("resources/cardiology/Journals")
    print("----------------------journals loaded--------------------------")
    load_all_pdfs("resources/cardiology")
    print("---------------------cardiology loaded-------------------------")
    load_all_pdfs("resources/Cardiology DM books/Cardiology Journals")
    print("---------------------cardiology journals loaded----------------")
    load_all_pdfs("resources/Cardiology DM books/Cardiology Textbooks")
    print("-----------------cardiology text books loaded------------------")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)
    docs = text_splitter.split_documents(all_docs)
    print("splitting done")
    print(len(all_docs))
    print(len(docs))

    # Embedding
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    test_vector = embedding_model.embed_query("What are embeddings?")
    print(test_vector[:5])

    # Load or create vectorstore
    if not os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")):
        print("🚀 Creating new Chroma DB in batches...")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)

        BATCH_SIZE = 32
        for i in tqdm(range(0, len(docs), BATCH_SIZE), desc="🔗 Embedding & Adding"):
            batch_docs = docs[i:i + BATCH_SIZE]
            try:
                vectorstore.add_documents(batch_docs)
                vectorstore.persist()
            except Exception as e:
                print(f"❌ Error in batch {i}-{i + BATCH_SIZE}: {e}")
        print("🎉 All documents embedded and saved in Chroma DB.")
    else:
        print("📦 Loading existing Chroma DB...")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)
        print("✅ Chroma DB loaded.")

    return vectorstore
