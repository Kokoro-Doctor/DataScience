# Streamlit Cloud Deployment Guide

## Steps to Deploy Your RAG-LLM Assistant to Streamlit Cloud

### 1. **Prepare Your Repository**

Ensure your project is in a public GitHub repository with all the necessary files:

- ✅ `app.py` (main application file)
- ✅ `requirements.txt` (dependencies with protobuf compatibility)
- ✅ `.streamlit/config.toml` (Streamlit configuration)
- ✅ `.env.example` (environment variables template)
- ✅ All source code in `src/` directory
- ✅ **Fixed protobuf compatibility** (automatically handled in `src/config.py`)

### 2. **Create Streamlit Cloud Account**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Authorize Streamlit to access your repositories

### 3. **Deploy Your App**

1. Click "New app" on your Streamlit Cloud dashboard
2. Select your GitHub repository: `RAG-LLM-Assistant-with-Gemini`
3. Choose the main branch (usually `main` or `master`)
4. Set the main file path: `app.py`
5. Click "Deploy!"

### 4. **Configure Environment Variables**

After deployment, you need to add your API keys and configuration:

1. In the Streamlit Cloud dashboard, click on your app
2. Click the "Settings" (gear icon) in the top right
3. Go to "Secrets" tab
4. Add your environment variables in TOML format:

```toml
# Streamlit secrets configuration
GEMINI_API_KEY = "your_actual_gemini_api_key_here"
MODEL_NAME = "gemini-1.5-pro"
CHUNK_SIZE = "1000"
CHUNK_OVERLAP = "200"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"
RETRIEVAL_K = "5"
MAX_PAGES_DEFAULT = "3"
MAX_PAGES_LIMIT = "10"
REQUEST_TIMEOUT = "10"
CHAT_HISTORY_ENABLED = "true"
MAX_CHAT_HISTORY_CONTEXT = "5"
FEEDBACK_ENABLED = "true"
FEEDBACK_WEIGHT = "0.2"
```

### 5. **Protobuf Compatibility Fix ✅**

**Good News**: This project has been updated to automatically handle protobuf compatibility issues!

The fix is implemented in `src/config.py` and automatically sets:
```python
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
```

This follows the official protobuf recommendation from [protobuf.dev](https://protobuf.dev/reference/python/python-generated#sharing-messages) for resolving the "Descriptors cannot be created directly" error.

### 6. **Important Notes for Cloud Deployment**

#### Memory and Performance Optimization:
- The app uses CPU-based embeddings for better compatibility
- ChromaDB is configured for in-memory storage (data won't persist between sessions)
- For production, consider using a persistent vector database
- **Protobuf compatibility is automatically handled**

#### Environment Variables:
- **Required**: `GEMINI_API_KEY` - Get this from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Optional**: All other variables have sensible defaults

#### File Upload Limitations:
- Streamlit Cloud has file size limits (usually 200MB max)
- PDF processing works within these limits
- Web scraping is limited by the hosting environment

### 6. **Getting Your Gemini API Key**

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add it to your Streamlit secrets as `GEMINI_API_KEY`

### 7. **Testing Your Deployment**

After deployment:
1. Wait for the build to complete (usually 2-5 minutes)
2. Visit your app URL (provided by Streamlit Cloud)
3. Test the basic functionality:
   - Check if the app loads without errors
   - Try uploading a small PDF
   - Test web scraping with a simple website
   - Ask a question to verify the RAG system works

### 8. **Common Issues and Solutions**

#### Build Errors:
- **Protobuf conflicts**: Fixed in the updated `requirements.txt`
- **Memory issues**: The app is optimized for cloud deployment
- **Dependency conflicts**: All versions are pinned for stability

#### Runtime Errors:
- **Missing API key**: Add `GEMINI_API_KEY` to secrets
- **Model not found**: Ensure you're using `gemini-1.5-pro` (not `gemini-2.5-pro`)
- **Embedding issues**: The app has fallback strategies for different environments

### 9. **Monitoring and Maintenance**

- **Logs**: Check Streamlit Cloud logs for any runtime issues
- **Usage**: Monitor your Gemini API usage and quotas
- **Updates**: Update dependencies regularly for security
- **Performance**: Monitor app performance and optimize as needed

### 10. **Repository Structure for Deployment**

Your final repository should look like this:

```
RAG-LLM-Assistant-with-Gemini/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── .env.example                   # Environment variables template
├── .streamlit/
│   └── config.toml                # Streamlit configuration
├── src/
│   ├── __init__.py
│   ├── config.py                  # App configuration
│   ├── components/                # UI components
│   ├── core/                      # Core RAG functionality
│   └── utils/                     # Utility functions
├── chroma_db/                     # Local vector database (optional)
├── README.md                      # Project documentation
└── DEPLOYMENT.md                  # This file
```

### 11. **Security Best Practices**

- Never commit API keys to your repository
- Use Streamlit secrets for sensitive data
- Keep your dependencies updated
- Monitor your API usage regularly
- Consider rate limiting for production use

---

## Quick Start Commands

If you want to test locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Add your API key to .env file
# Edit .env and add: GEMINI_API_KEY=your_key_here

# Run locally
streamlit run app.py
```

Your app will be available at: `http://localhost:8501`

---

## Support

If you encounter issues:
1. Check the Streamlit Cloud logs
2. Verify your environment variables
3. Test locally first
4. Check the [Streamlit Community Forum](https://discuss.streamlit.io)

Happy deploying! 🚀
