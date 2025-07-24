# RAG LLM Assistant - Streamlit Cloud Deployment

This project is deployed on Streamlit Cloud. 

## Live Demo
🚀 **[Access the Live Application](your-app-url-here)**

## Configuration for Streamlit Cloud

### Required Environment Variables
Set these in your Streamlit Cloud app settings:

1. **GEMINI_API_KEY** (Required)
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - This is the only required environment variable

### Optional Environment Variables
```
MODEL_NAME=gemini-2.5-pro
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
RETRIEVAL_K=5
MAX_PAGES_DEFAULT=3
MAX_PAGES_LIMIT=10
REQUEST_TIMEOUT=10
CHAT_HISTORY_ENABLED=true
MAX_CHAT_HISTORY_CONTEXT=5
FEEDBACK_ENABLED=true
FEEDBACK_WEIGHT=0.2
```

## Local Development

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Fill in your API keys in `.env`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `streamlit run app.py`

## Features

- 🌐 Web scraping and content extraction
- 📄 PDF document processing
- 💬 Interactive chat with RAG system
- 🧠 Google Gemini AI integration
- 📊 Vector database with ChromaDB
- 🎨 Modern UI with custom styling

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini AI
- **Framework**: LangChain
- **Vector Database**: ChromaDB
- **Embeddings**: HuggingFace Transformers
- **Document Processing**: PyPDF2, BeautifulSoup4
