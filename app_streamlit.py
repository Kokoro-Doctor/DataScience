import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from summarizer import summarize_with_ollama
from sentiment import FinBertSentimentAnalyzer
from analysis import detect_bias
from rag_utils import embed_text, retrieve_similar_docs

# ──────────────────────────────────────────────────────────────
# 📄 Article Scraper
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

# ──────────────────────────────────────────────────────────────
# 🚀 Main App Function
def main():
    st.set_page_config(page_title="📰 Financial News Summarizer", layout="wide")
    st.title("📰 Financial News ")
    st.caption("🔍 Powered by LLaMA ")

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

        st.subheader(f"📰 {title}")
        with st.expander("📝 Click to view full article text"):
            st.write(article_text)

        with st.spinner("✂️ Summarizing..."):
            summary = summarize_with_ollama(article_text)

        with st.expander("📃 Click to view the summary and implications"):
            highlight_words = ["interest rate", "inflation", "growth", "unemployment", "recession"]
            for word in highlight_words:
                summary = summary.replace(word, f"**:blue[{word}]**")
            st.markdown(summary, unsafe_allow_html=True)
            st.download_button("⬇️ Download Summary", summary, file_name="summary.txt")

        with st.spinner("📊 Analyzing sentiment and bias..."):
            analyzer = FinBertSentimentAnalyzer()
            sentiment = analyzer.analyze_sentiment(summary)
            bias = detect_bias(summary)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧠 Sentiment Analysis")
            label = sentiment["label"]
            if label == "positive":
                st.success("🟢 Positive")
            elif label == "negative":
                st.error("🔴 Negative")
            else:
                st.info("⚪ Neutral")
            st.markdown("**Confidence Scores:**")
            st.json(sentiment["scores"])
            st.bar_chart(pd.DataFrame([sentiment["scores"]]))

        with col2:
            st.markdown("### 📌 Detected Political Bias")
            bias_emoji = {"Left": "🔵", "Right": "🔴", "Center": "⚪"}
            st.info(f"{bias_emoji.get(bias, '⚪')} **{bias}**")

        with st.spinner("🔍 Retrieving related knowledge base documents..."):
            query_embedding = embed_text(summary)
            related_docs = retrieve_similar_docs(query_embedding, top_k=3)

        st.markdown("### 📚 Top Related Finance News from Knowledge Base")
        for i, doc in enumerate(related_docs, 1):
            st.markdown(f"- **Doc {i}:** {doc}")

# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
