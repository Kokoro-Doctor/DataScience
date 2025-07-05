import streamlit as st
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()
CHROMA_PATH = os.getenv("CHROMA_PATH", "chromadb_store")
OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# Prompt template
CUSTOM_PROMPT = """
You are a friendly, caring, and empathetic heart health assistant.
Respond to the user's question in 1–2 sentences with helpful and actionable advice.

Context: {context}
User: {question}
AI Response:
"""

@st.cache_resource
def load_chain():
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model="llama3", base_url=OLLAMA_API)
    prompt = PromptTemplate(template=CUSTOM_PROMPT, input_variables=["context", "question"])

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )
    return chain

# Streamlit UI
st.set_page_config(page_title="Cardiac Care Chatbot", layout="centered")
st.title("🫀 Cardiac Health Assistant")
st.write("Ask any question related to heart health, symptoms, lifestyle, or medication.")

qa_chain = load_chain()

# Chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Input form
with st.form(key="chat_form", clear_on_submit=True):
    user_query = st.text_input("💬 Your Question:", placeholder="e.g. How to control blood pressure naturally?")
    submit_button = st.form_submit_button(label="Send")

# Handle form submission
if submit_button and user_query:
    with st.spinner("Thinking..."):
        result = qa_chain.invoke({"query": user_query})
        st.session_state.chat_history.append({
            "question": user_query,
            "answer": result["result"],
            "sources": [doc.metadata.get("source", "Unknown") for doc in result["source_documents"]]
        })

# Display chat history
for entry in reversed(st.session_state.chat_history):
    st.markdown("### 🧍 Your Question:")
    st.info(entry["question"])

    st.markdown("### 🤖 AI Response")
    st.success(entry["answer"])

    st.markdown("### 📚 Source Documents")
    for src in entry["sources"]:
        st.markdown(f"- `{src}`")
