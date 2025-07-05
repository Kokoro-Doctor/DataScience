import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from summarizer import summarize_with_ollama
from sentiment import FinBertSentimentAnalyzer
from analysis import detect_bias
from rag_utils import embed_text, retrieve_similar_docs

# Cosine Similarity Evaluation
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# ─────────────────────────────────────────────
@st.cache_resource
def load_embedding_model():
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    return tokenizer, model

def embed_text_for_eval(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        model_output = model(**inputs)
    token_embeddings = model_output[0]
    input_mask_expanded = inputs['attention_mask'].unsqueeze(-1).expand(token_embeddings.size())
    embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / \
                torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return F.normalize(embedding, p=2, dim=1)

def scrape_yahoo_article_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.select("article p")
        article_text = " ".join([p.get_text(strip=True) for p in paragraphs])
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Article"
        return title, article_text
    except Exception as e:
        st.error(f"❌ Error scraping article: {e}")
        return None, None

# ─────────────────────────────────────────────
def main():
    st.set_page_config(page_title="📰 Financial News Summarizer", layout="wide")
    st.title("📰 Financial News Summarizer")
    st.caption("🔍 LLaMA, FinBERT, Transformers, RAG")

    # Initialize state if not yet
    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "title" not in st.session_state:
        st.session_state.title = ""
    if "article_text" not in st.session_state:
        st.session_state.article_text = ""

    url = st.text_input("🔗 Enter a Yahoo Finance article URL:")

    if st.button("🔍 Analyze"):
        if not url:
            st.error("⚠️ Please enter a valid URL.")
            return

        with st.spinner("🔄 Scraping article..."):
            title, article_text = scrape_yahoo_article_text(url)

        if not article_text:
            st.error("❌ Failed to extract article text. Please check the URL.")
            return

        with st.spinner("✂️ Summarizing..."):
            summary = summarize_with_ollama(article_text)

        # Save to session state
        st.session_state.summary = summary
        st.session_state.title = title
        st.session_state.article_text = article_text

    # ─────────────────────────────────────────────
    if st.session_state.summary:
        st.subheader(f"📰 {st.session_state.title}")
        with st.expander("📝 Full Article Text"):
            st.write(st.session_state.article_text)

        with st.expander("📃 Summary and Implications"):
            highlight_words = ["interest rate", "inflation", "growth", "unemployment", "recession"]
            formatted = st.session_state.summary
            for word in highlight_words:
                formatted = formatted.replace(word, f"**:blue[{word}]**")
            st.markdown(formatted, unsafe_allow_html=True)
            st.download_button("⬇️ Download Summary", st.session_state.summary, file_name="summary.txt")

        with st.spinner("📊 Sentiment and Bias Analysis..."):
            analyzer = FinBertSentimentAnalyzer()
            sentiment = analyzer.analyze_sentiment(st.session_state.summary)
            bias = detect_bias(st.session_state.summary)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🧠 Sentiment")
            label = sentiment["label"]
            if label == "positive":
                st.success("🟢 Positive")
            elif label == "negative":
                st.error("🔴 Negative")
            else:
                st.info("⚪ Neutral")
            st.json(sentiment["scores"])
            st.bar_chart(pd.DataFrame([sentiment["scores"]]))

        with col2:
            st.markdown("### 📌 Bias")
            emoji = {"Left": "🔵", "Right": "🔴", "Center": "⚪"}
            st.info(f"{emoji.get(bias, '⚪')} **{bias}**")

        with st.spinner("🔍 Retrieving Similar Docs..."):
            query_embedding = embed_text(st.session_state.summary)
            docs = retrieve_similar_docs(query_embedding, top_k=3)

        st.markdown("### 📚 Top Related Docs")
        for i, doc in enumerate(docs, 1):
            st.markdown(f"- **Doc {i}:** {doc}")

        # ─────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🧪 Evaluate Summary Against Reference")
        reference = st.text_area("✍️ Paste Reference Summary", height=150)
        if st.button("✅ Evaluate Summary Similarity"):
            if not reference.strip():
                st.warning("⚠️ Please paste a reference summary.")
            else:
                tokenizer, model = load_embedding_model()
                try:
                    emb1 = embed_text_for_eval(st.session_state.summary, tokenizer, model)
                    emb2 = embed_text_for_eval(reference, tokenizer, model)
                    sim = torch.matmul(emb1, emb2.T).item()
                    st.metric("📏 Cosine Similarity Score", f"{sim:.3f}")
                    if sim >= 0.85:
                        st.success("✅ Strong similarity")
                    elif sim >= 0.65:
                        st.info("🟡 Moderate similarity")
                    else:
                        st.error("❌ Weak similarity")
                except Exception as e:
                    st.error(f"❌ Similarity calculation failed: {e}")

# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
str