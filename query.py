import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Config
CHROMA_PATH = os.getenv("CHROMA_PATH", "chromadb_store")
OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# Custom Prompt
PROMPT_TEMPLATE = """
You are a friendly, caring, and empathetic heart health assistant.
Respond to the user's question in 1–2 sentences with helpful and actionable advice.

Context: {context}
User: {question}
AI Response:
"""

def get_qa_chain():
    embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    llm = ChatOllama(model="llama3", base_url=OLLAMA_API)
    prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )
    return chain

if __name__ == "__main__":
    print("\n🫀 Cardiac Health Chatbot is ready! Type your question (or 'exit' to quit).\n")
    qa_chain = get_qa_chain()

    while True:
        query = input("🧍 You: ")
        if query.lower() in ["exit", "quit"]:
            print("👋 Exiting. Stay heart healthy!")
            break

        result = qa_chain.invoke({"query": query})
        print("\n🤖 AI:", result["result"])

        print("\n📚 Sources:")
        for doc in result["source_documents"]:
            print("-", doc.metadata.get("source", "Unknown"))
