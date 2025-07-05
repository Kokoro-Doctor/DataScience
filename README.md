# DataScience
**Financial News Summarizer & Analyzer**
A Streamlit-based NLP application that scrapes Yahoo Finance news, generates concise summaries using LLaMA + RAG, performs sentiment and political bias analysis, retrieves contextually similar documents, and allows evaluation via cosine similarity against reference summaries.

**Features**
Yahoo Finance Article Scraper
Scrapes headlines and full article content from provided Yahoo Finance URLs.

**Summarization via LLaMA 3.2 + RAG**
Uses Retrieval-Augmented Generation with a local LLaMA 3.2 model to generate concise bullet-point summaries enriched with relevant context.

**Sentiment Analysis (FinBERT)**
Classifies the generated summary as Positive, Negative, or Neutral using a fine-tuned BERT model on financial text.

**Political Bias Detection**
Uses cosine similarity between the summary and pre-defined Left/Right keyword sets (TF-IDF based) to infer bias as Left, Right, or Center.

**Knowledge Base Integration**
Retrieves the top 3 semantically similar financial documents from a custom-built FAISS vector store using SentenceTransformer embeddings.

**Evaluation via Cosine Similarity**
Allows users to paste a ground-truth summary and computes cosine similarity between it and the generated summary using MiniLM embeddings.

**Tech Stack**
Frontend: Streamlit

LLM & Embeddings: LLaMA 3.2 via Ollama, SentenceTransformers (MiniLM), LangChain

NLP Models: FinBERT (yiyanghkust/finbert-tone), TF-IDF (Sklearn)

Backend: Python, PyTorch, FAISS

Scraping: BeautifulSoup, Requests
