import streamlit as st
import time
from langgraph_workflow import app as langgraph_app  # The compiled LangGraph workflow
from vector import create_or_load_vectorstore

# Optional: For showing sources if RAG is used
from rag import build_rag_chain

# ------------------- Streamlit Config -------------------
st.set_page_config(page_title="🫀 MedBot - Cardiology AI Agent", layout="wide")
st.title("🩺 MedBot: Cardiology AI Agent")
st.caption("Ask any cardiology or general knowledge question.")

# ------------------- Initialize Vectorstore for Sources -------------------
@st.cache_resource
def load_retriever():
    vectorstore = create_or_load_vectorstore()
    _, retriever = build_rag_chain(vectorstore)
    return retriever

retriever = load_retriever()

# ------------------- Session State -------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------- Display Chat History -------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------------------- Handle User Query -------------------
if prompt := st.chat_input("🔍 Ask your question:"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking..."):
            try:
                # Invoke LangGraph workflow
                state = {"messages": [prompt]}
                response = langgraph_app.invoke(state)

                answer = response["messages"][-1]
                route = response.get("route", "LLM")  # Which path was used

                # Typing animation
                animated_text = ""
                msg_placeholder = st.empty()
                for char in answer:
                    animated_text += char
                    msg_placeholder.markdown(animated_text + "▌")
                    time.sleep(0.01)
                msg_placeholder.markdown(animated_text)

                # Save assistant message
                st.session_state.messages.append({"role": "assistant", "content": answer})

                # Show RAG sources if route is RAG
                if route == "RAG":
                    retrieved_docs = retriever.invoke(prompt)
                    with st.expander("📚 Sources"):
                        for i, doc in enumerate(retrieved_docs[:3]):
                            st.markdown(f"**Source {i+1}:** `{doc.metadata.get('source', 'Unknown')}`")
                            st.code(doc.page_content[:500])

            except Exception as e:
                st.error(f"⚠️ An error occurred: {e}")
