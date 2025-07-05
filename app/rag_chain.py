import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import numpy as np
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain_huggingface import HuggingFacePipeline
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from operator import itemgetter
import torch

from app.embeddings import embedding_model

persist_dir = "db"

def load_vector_db():
    return Chroma(persist_directory=persist_dir, embedding_function=embedding_model)

def load_llm():
    model_name = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    hf_pipeline = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        device=0 if torch.cuda.is_available() else -1,
    )
    return HuggingFacePipeline(pipeline=hf_pipeline)

llm = load_llm()

prompt_template = PromptTemplate.from_template(
    """
    You are a professional HR policy assistant.

    Use the context below to answer the user's question.
    If no context is relevant, say: "I could not find this information in the uploaded policy documents."

    Question: {question}

    Context:
    {context}

    Answer:
    """
)

def search_with_scores(vector_db, query, k=7):
    return vector_db.similarity_search_with_score(query, k=k)

def retrieve_context(question, vector_db, threshold=0.45, k=7):
    results = search_with_scores(vector_db, question, k=k)

    unique_docs = {}
    for doc, score in results:
        key = (doc.page_content.strip(), doc.metadata.get("page"))
        if key not in unique_docs or score < unique_docs[key][1]:
            unique_docs[key] = (doc, score)

    # improved fallback: allow up to 0.7 max, reject worse
    filtered = [(doc, score) for (doc, score) in unique_docs.values() if score <= threshold]
    if not filtered:
        filtered = [(doc, score) for (doc, score) in unique_docs.values() if score <= 0.7]

    context_docs = [doc.page_content for doc, _ in filtered]
    metadata = [doc.metadata for doc, _ in filtered]
    scores = [score for _, score in filtered]

    avg_score = np.mean(scores) if scores else 1.0
    confidence = "High" if avg_score <= 0.2 else "Medium" if avg_score <= 0.4 else "Low"

    return {
        "question": question,
        "context": "\n".join(context_docs),
        "sources": metadata,
        "scores": scores,
        "confidence": confidence
    }

def build_rag_chain(vector_db, threshold=0.45):
    def context_fn(question):
        return retrieve_context(question, vector_db=vector_db, threshold=threshold)

    chain = (
        RunnableLambda(context_fn)
        | RunnableMap({"question": itemgetter("question"), "context": itemgetter("context")})
        | prompt_template
        | llm
        | StrOutputParser()
    )
    return chain, context_fn


if __name__ == "__main__":
    print("🔁 Loading vector DB…")
    vector_db = load_vector_db()

    if vector_db._collection.count() == 0:
        print("❌ Vector DB is empty. Please upload and index PDFs first.")
        exit(1)

    rag_chain, retrieve_context_fn = build_rag_chain(vector_db, threshold=0.45)

    print("✅ Ready! Type a question or type 'exit' to quit.")
    while True:
        user_q = input("\n❓ Ask a policy question: ")
        if user_q.lower().strip() in ["exit", "quit"]:
            break

        result = retrieve_context_fn(user_q)

        print("\n🎯 Confidence level:", result["confidence"])

        if not result["context"]:
            print("⚠️ No relevant chunks found (context empty).")

        print("\n📚 Sources & Scores:")
        for meta, score in zip(result["sources"], result["scores"]):
            print(f"- File: {meta.get('source')} | Page: {meta.get('page')} | Cosine Score: {round(score,4)}")

        print("\n🤖 Answer:")
        answer = rag_chain.invoke(user_q)
        print(answer)

