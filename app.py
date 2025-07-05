import streamlit as st
from news_fetcher import fetch_news_links_yahoo
from extractors import extract_text_from_url, extract_text_from_pdf
from chunker import chunk_text
from embedding_db import store_chunks, retrieve_similar_chunks, get_all_documents
from rag_analyzer import analyze_article_rag, analyze_financial_report
from utils import compute_cosine_similarity, compute_rouge_l
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='torch')

st.set_page_config(page_title="Financial News Analyzer", layout="wide")
st.title("📊 Financial News & Report Analyzer (RAG + ChromaDB + Mistral)")

tab1, tab2 = st.tabs(["📰 Analyze News", "📁 Analyze Financial Reports"])

# ---- TAB 1: News Analysis ----
with tab1:
    company_name = st.text_input("Enter a company name (e.g., Meta, Tesla, Infosys)")

    if st.button("Analyze News"):
        if not company_name.strip():
            st.warning("Please enter a valid company name.")
        else:
            links = fetch_news_links_yahoo(company_name)
            if not links:
                st.error("No articles found.")
            else:
                st.success(f"Latest {len(links)} articles are:")
                all_texts, all_summaries = [], []

                for i, url in enumerate(links):
                    st.markdown(f"### Article {i+1}")
                    article_text = extract_text_from_url(url)

                    if not article_text or len(article_text) < 100:
                        st.warning(f"⚠️ Skipped (Too short): {url}")
                        continue

                    chunks = chunk_text(article_text)
                    metadata = [{"source_url": url} for _ in chunks]
                    stored_count, total_count = store_chunks(chunks, metadata)

                    st.success(f"Stored {stored_count} chunks. Total in DB: {total_count}")
                    relevant_chunks = retrieve_similar_chunks(article_text)
                    context = " ".join(relevant_chunks) if relevant_chunks else article_text

                    result = analyze_article_rag(context)
                    summary = result.get("summary", "").strip()
                    sentiment = result.get("sentiment", "Unknown").strip()
                    bias = result.get("bias", "Unknown").strip()

                    rouge_score = compute_rouge_l(summary, article_text)
                    cosine_score = compute_cosine_similarity(summary, article_text)

                    st.write(f"**Summary**: {summary}")
                    st.write(f"**Sentiment**: {sentiment}")
                    st.write(f"**Bias**: {bias}")
                    st.write(f"**ROUGE-L**: {rouge_score:.2f} | **Cosine**: {cosine_score:.2f}")
                    st.write("---")

                    all_texts.append(article_text)
                    all_summaries.append(summary)

                if all_texts:
                    combined_text = " ".join(all_texts)[:4000]
                    final_result = analyze_article_rag(combined_text)
                    st.subheader(f"📊 Overall News Summary for '{company_name}'")
                    st.write(f"**Summary**: {final_result.get('summary')}")
                    st.write(f"**Sentiment**: {final_result.get('sentiment')}")
                    st.write(f"**Bias**: {final_result.get('bias')}")

# ---- TAB 2: Financial PDF Analysis ----
with tab2:
    st.write("Upload 5-Year Financial Report PDFs (Profit, Revenue, Debt Analysis + Investment Advice)")
    uploaded_files = st.file_uploader("Upload PDF reports", type=["pdf"], accept_multiple_files=True)

    if st.button("Analyze Reports"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF.")
        else:
            combined_report_text = ""

            for file in uploaded_files:
                st.write(f"📄 Processing: {file.name}")
                text = extract_text_from_pdf(file)
                if text:
                    combined_report_text += "\n\n" + text
                else:
                    st.warning(f"Could not extract text from: {file.name}")

            if combined_report_text.strip():
                report_chunks = chunk_text(combined_report_text)
                store_chunks(report_chunks)

                result = analyze_financial_report(combined_report_text)
                st.subheader("📈 Financial Report Analysis (5 Years)")
                st.write(f"**Profit Trend**: {result.get('profit')}")
                st.write(f"**Revenue Trend**: {result.get('revenue')}")
                st.write(f"**Debt Status**: {result.get('debt')}")
                st.write(f"**Investment Advice**: {result.get('investment_advice')}")
