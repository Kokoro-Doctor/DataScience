import os
import shutil
import streamlit as st
from app.doc_processor import load_and_chunk_pdf, create_chroma_index
from app.embeddings import embedding_model
from app.rag_chain import build_rag_chain
from langchain_community.vectorstores import Chroma

DATA_DIR = "data"
DB_DIR = "db"

os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="📄 Policy QA Chatbot", layout="wide")
st.title("🤖 Policy QA Chatbot")

# Sidebar for admin actions
st.sidebar.header("📂 Admin Panel")
if st.sidebar.button("🗑️ Reset Data"):
    shutil.rmtree(DB_DIR, ignore_errors=True)
    shutil.rmtree(DATA_DIR, ignore_errors=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    st.sidebar.success("✅ Data cleared. Please upload PDF(s) again.")
    st.stop()

uploaded_files = st.sidebar.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)
if uploaded_files:
    for pdf in uploaded_files:
        path = os.path.join(DATA_DIR, pdf.name)
        with open(path, "wb") as f:
            f.write(pdf.read())
    st.sidebar.info("⏳ Processing...")
    chunks = load_and_chunk_pdf(DATA_DIR)
    create_chroma_index(chunks)
    st.sidebar.success("✅ Documents indexed.")

# Main chat
st.header("💬 Chat")

if not os.path.exists(DB_DIR) or not os.listdir(DB_DIR):
    st.warning("⚠️ Please upload and index PDF(s) first.")
    st.stop()

vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_model)
rag_chain, retrieve_context_fn = build_rag_chain(vector_db, threshold=0.45)

if "history" not in st.session_state:
    st.session_state.history = []

question = st.text_input("Your Question:")
if st.button("Ask") and question:
    result = retrieve_context_fn(question)
    answer = rag_chain.invoke(question)

    st.session_state.history.append({
        "question": question,
        "answer": answer,
        "confidence": result["confidence"],
        "sources": [
            f"{meta.get('source', 'unknown')} | Page: {meta.get('page', '?')} | Cosine: {round(score,4)}"
            for meta, score in zip(result["sources"], result["scores"])
        ]
    })

if st.session_state.history:
    for i, msg in enumerate(reversed(st.session_state.history)):
        st.markdown(f"### ❓ Q{i+1}: {msg['question']}")
        st.markdown(f"🤖 **Answer:** {msg['answer']}")
        st.markdown(f"🎯 **Confidence:** {msg['confidence']}")
        if msg["sources"]:
            with st.expander("📚 Sources & Scores"):
                for src in msg["sources"]:
                    st.markdown(f"- {src}")


