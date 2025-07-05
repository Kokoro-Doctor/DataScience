import requests
from bs4 import BeautifulSoup

def fetch_news_links_yahoo(company_name, max_articles=5):
    query = company_name.replace(" ", "+")
    url = f"https://www.bing.com/news/search?q={query}+site:finance.yahoo.com"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("https://finance.yahoo.com") and href not in links:
            links.append(href)
        if len(links) >= max_articles:
            break
    return links
