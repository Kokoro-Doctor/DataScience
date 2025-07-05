import requests
from rag_utils_1 import embed_text, retrieve_similar_docs  

def call_llama(prompt: str) -> str:
    """
    Call the LLaMA 3.2 model via local Ollama API to generate a summary.w
    """
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
    )
    response.raise_for_status()
    return response.json()["message"]["content"]

def summarize_with_ollama(article_text: str) -> str:
    """
    Summarize the given article text using RAG (retrieval-augmented generation).
    """
    # Step 1: Embed article text
    query_embedding = embed_text(article_text)

    # Step 2: Retrieve similar docs
    top_docs = retrieve_similar_docs(query_embedding, top_k=3)
    context = "\n".join(top_docs)

    # Step 3: Create prompt with retrieved context
    prompt = (
        "You are a financial news summarization assistant.\n"
        "Below is some background knowledge that may help you:\n\n"
        f"{context}\n\n"
        "And here's the news article:\n"
        f"{article_text}\n\n"
        "Please summarize the article in 3-4 bullet points and note any potential financial implications."
    )

    # Step 4: Get summary from LLaMA 3.2 via Ollama API
    return call_llama(prompt)

'''

def test_summarizer():
    """
    Run a test of the summarizer with a sample article.
    """
    sample_article = (
        "The Federal Reserve announced an interest rate hike on Wednesday, "
        "citing ongoing concerns about inflation. Markets reacted with volatility, "
        "as investors weighed the implications for economic growth. "
        "The move was widely expected by analysts."
    )

    print("📝 Running summarizer on sample article...")
    summary = summarize_with_ollama(sample_article)
    print("\n📃 Summary Generated:")
    print(summary)

if __name__ == "__main__":
    test_summarizer()

'''