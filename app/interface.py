import streamlit as st

def pdf_uploader():
    uploaded_files = st.file_uploader(
        "Upload Policy PDFs", type=["pdf"], accept_multiple_files=True
    )
    return uploaded_files

def chat_input():
    return st.text_input("Enter your policy question:")

def display_chat(messages):
    for msg in messages:
        with st.chat_message("user"):
            st.markdown(msg['user'])

        with st.chat_message("assistant"):
            st.markdown(msg['bot'])
            if msg['sources']:
                with st.expander("📚 Sources", expanded=False):
                    for src in msg['sources']:
                        st.markdown(f"- {src}")

def clear_chat_button():
    if st.button("Clear chat history"):
        return True
    return False

