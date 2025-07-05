import requests
from bs4 import BeautifulSoup

def scrape_yahoo_finance(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract paragraphs inside the <article> tag, typical for Yahoo Finance news pages
        paragraphs = soup.select("article p")
        article_text = " ".join([p.get_text(strip=True) for p in paragraphs])

        if not article_text:
            raise ValueError("No article text found")

        return article_text
    except Exception as e:
        print(f"❌ Error scraping article: {e}")
        return None
