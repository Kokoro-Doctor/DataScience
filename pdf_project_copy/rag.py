#write rag code here
# loading all required libraries
from dotenv import load_dotenv
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser


 
# loading environment variables
load_dotenv()

# working with pdf
file_path = "book\Introduction.to.Algorithms.4th.Edition.pdf"
loader = PyMuPDFLoader(file_path)
data= loader.load()
# chunking
text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs=text_splitter.split_documents(data)
# embedding
# embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-exp-03-07")
embeddings= embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
# vector = embeddings.embed_query("What are embeddings?")
# print(vector[:5])
# creating vector database
persist_directory = "chroma_db"
# vectorstore=Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory = "chroma_db")
# Check if DB exists
if os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")):
    print("🔄 Loading existing Chroma DB...")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
else:
    print("🆕 Creating new Chroma DB...")
    # Make sure `docs` is defined earlier as your list of Document objects
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectorstore.persist()
    print("✅ Chroma DB created and persisted.")

# creating retriever for retrieving relevant chunks
retriever=vectorstore.as_retriever(search_type="similarity",search_kwargs={"k":6})
retrieved_docs=retriever.invoke("What is this book about?")
print(retrieved_docs)

# llm
llm=ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.3,
    max_retries=2,
    max_tokens=1000,
    timeout=None
)
# prompt template
# Join retrieved document content
context = "\n\n".join([doc.page_content for doc in retrieved_docs])
# Create ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a helpful assistant that answers questions based on academic PDFs. "
     "The content may include paragraphs, tables, and diagram descriptions."),
    ("human", 
     "Here is some extracted content from a PDF:\n\n{context}\n\n"
     "Based on this, answer the question:\n{input}")
])

# chaining
qa_chain=create_stuff_documents_chain(llm,prompt)
# output_parser = StrOutputParser()
rag_chain=create_retrieval_chain(retriever,qa_chain)
# Format the prompt messages
question = "What is this book about?"
# messages = prompt.format_messages(context=context, question=question)
# Run the LLM on the messages
response = rag_chain.invoke({"context":context,"input":question})
print("📘 Answer:\n", response['answer'])