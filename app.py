from scraper import scrape_yahoo_finance
from summarizer import summarize_with_ollama
from sentiment import FinBertSentimentAnalyzer
from analysis import detect_bias


analyzer = FinBertSentimentAnalyzer()

def run_pipeline():
    url = input("Please enter the Yahoo Finance URL to scrape: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return
    
    article_text = scrape_yahoo_finance(url)

    if not article_text:
        print("No article text found. Exiting.")
        return

    print(f"\nArticle Text:\n{article_text}")

    summary = summarize_with_ollama(article_text)
    print(f"\nSummary:\n{summary}")

    try:
        sentiment = analyzer.analyze_sentiment(summary)
        print(f"\nSentiment:\n{sentiment}")
    except Exception as e:
        print(f"❌ Sentiment analysis failed: {e}")
        sentiment = {"label": "unknown", "scores": {}}

    try:
        bias = detect_bias(summary)
        print(f"\n⚖️ Detected Bias:\n{bias}")
    except Exception as e:
        print(f"❌ Bias detection failed: {e}")

if __name__ == "__main__":
    run_pipeline()
