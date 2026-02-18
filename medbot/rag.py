# rag.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from dotenv import load_dotenv
from langchain_community.llms import HuggingFaceHub

load_dotenv()

def build_rag_chain(vectorstore):
    llm_model_name = "gemini-2.5-pro"
    llm = ChatGoogleGenerativeAI(
        model=llm_model_name,
        temperature=0.3,
        max_retries=2,
    )

    # llm = HuggingFaceHub(
    #     repo_id="mistralai/Mistral-7B-Instruct-v0.1",  # or any other model
    #     model_kwargs={
    #         "temperature": 0.3,
    #         "max_new_tokens": 512
    #     }
    # )  

    prompt = ChatPromptTemplate.from_messages([
        ("system", 
        """You are MedBot, a smart, reliable AI agent specialized in cardiology. 
        You help doctors, students, and patients understand complex cardiology topics clearly and accurately. 
        Use the provided medical content to answer questions concisely but informatively. 
        Include clinical signs, definitions, diagnostic steps, use-cases, and standard treatments when relevant. 
        If the context doesn’t have an answer, say so honestly. Don’t hallucinate or assume."""
        ),
        ("human", 
        """Medical Content:\n\n{context}\n\n
        User Question:\n{input}""")
    ])

    qa_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6}), qa_chain)

    return rag_chain, vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
