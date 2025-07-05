# app/interface.py

import streamlit as st

def pdf_uploader():
    uploaded_files = st.file_uploader(
        "Upload Policy PDFs", type=["pdf"], accept_multiple_files=True
    )
    return uploaded_files

def chat_input():
    return st.text_input("Enter your policy question:")

def display_chat(messages):
    # messages = list of dicts { "user": str, "bot": str, "sources": list[str] }
    for msg in messages:
        st.markdown(f"**You:** {msg['user']}")
        st.markdown(f"**Bot:** {msg['bot']}")
        if msg['sources']:
            st.markdown("**Sources:**")
            for src in msg['sources']:
                st.markdown(f"- {src}")
        st.markdown("---")

def clear_chat_button():
    if st.button("Clear chat history"):
        return True
    return False

