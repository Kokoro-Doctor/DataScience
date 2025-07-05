import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

def extract_text_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "aside", "noscript", "header", "footer"]):
            tag.decompose()
        paragraphs = soup.find_all("p")
        return "\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
    except Exception as e:
        print(f"[ERROR] {e}")
        return ""

def extract_text_from_pdf(file):
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        print(f"[PDF ERROR] {e}")
        return ""
