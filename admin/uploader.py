# admin/uploader.py


import streamlit as st
import os
from app.doc_processor import load_and_chunk_pdf
from app.embeddings import create_chroma_index

st.title("📂 Admin - Upload Policy Document")

uploaded = st.file_uploader("Upload PDF", type="pdf")
if uploaded:
    save_path = os.path.join("data", uploaded.name)
    with open(save_path, "wb") as f:
        f.write(uploaded.read())

    st.info("⏳ Chunking and indexing...")
    chunks = load_and_chunk_pdf(save_path)
    create_chroma_index(chunks)
    st.success("✅ Document indexed successfully.")