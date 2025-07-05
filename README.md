#  Financial News & Report Analyzer (RAG + LangChain + Ollama + Mistral)

This project has **two powerful functionalities** built using **RAG (Retrieval-Augmented Generation)**, **LangChain**, **Ollama**, and **Mistral AI**, with embeddings managed through **ChromaDB** and **Ollama embeddings**.

##  Functionality 1: News Analysis from Yahoo Finance

* Users can **enter the name of any company** in the app interface.
* The system will:
  * **Scrape 5 latest Yahoo Finance news articles** about that company via Bing News search.
  * Use an LLM to:
    * Generate a **summary** of each article
    * Determine the **sentiment** of each article (Positive / Negative / Neutral)
    * Detect **bias** in each article (Left / Right / Center)
    * Calculate:
      * **ROUGE-L score** (to evaluate summary quality)
      * **Cosine similarity** (to measure semantic similarity)
* After analyzing all articles individually, the system will:
  * Provide an **overall combined summary**
  * Compute **overall sentiment and bias**
  * Report **aggregate performance metrics** across all 5 articles

##  Functionality 2: 5-Year Financial Report Analysis

* Users can **upload 5 financial reports (PDFs)** of any company.
* The system:
  * Extracts and chunks the content
  * Analyzes it using the LLM to provide:
    * A recommendation on **whether to invest or not**
    * Analysis of the company's **profit trend**
    * Analysis of the **debt trend**
* This functionality enables **long-term financial evaluation** and investment advice based on real data.

##  Technologies Used

* **RAG (Retrieval-Augmented Generation)** for grounded, accurate answers
* **LangChain** for chaining and orchestration
* **Ollama** to run **Mistral AI** locally (lightweight, efficient LLM)
* **Ollama Embeddings** + **ChromaDB** for vector search and semantic retrieval
* **Streamlit** for the interactive web dashboard
* **BeautifulSoup** and **Requests** for web scraping
* **PyMuPDF (fitz)** for PDF text extraction
* **scikit-learn** and **ROUGE** for evaluation metrics

##  Get Started

Clone the repo and follow the instructions to install dependencies and run the app.
