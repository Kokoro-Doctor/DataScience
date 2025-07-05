import json
import json5
import re
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="mistral")

# --- Financial News Prompt ---
news_template = """
You are a financial news assistant.
Given the following article, perform three tasks:
1. Provide a detailed summary.
2. Identify the sentiment (Positive/Neutral/Negative).
3. Determine political bias (Left/Center/Right).

Respond ONLY in JSON format like:
{{ "summary": "...", "sentiment": "...", "bias": "..." }}

Article:
{article}
"""
news_prompt = PromptTemplate(input_variables=["article"], template=news_template)
rag_chain = news_prompt | llm


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON-like structure found in response")
    json_text = match.group()
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return json5.loads(json_text)


def analyze_article_rag(text: str) -> dict:
    try:
        response = rag_chain.invoke({"article": text})
        return extract_json(response)
    except Exception as e:
        print(f"[ERROR] News RAG failed: {e}")
        return {"summary": "", "sentiment": "Unknown", "bias": "Unknown"}

# --- Financial Report Prompt ---
report_template = """
You are a financial report analyst.
Given the annual reports below, extract:
1. Profit trend over 5 years.
2. Revenue trend over 5 years.
3. Any presence of major debts or liabilities.
4. Clear investment recommendation: Should someone invest in this company?
   If yes, is it short-term (1-2 years) or long-term (3-5+ years)?

Respond ONLY in JSON format like:
{{ "profit": "...", "revenue": "...", "debt": "...", "investment_advice": "..." }}

Reports:
{article}
"""
report_prompt = PromptTemplate(input_variables=["article"], template=report_template)
report_chain = report_prompt | llm


def analyze_financial_report(text: str) -> dict:
    try:
        trimmed_text = text[:4000] 
        response = report_chain.invoke({"article": trimmed_text})
        return extract_json(response)
    except Exception as e:
        print(f"[ERROR] Report RAG failed: {e}")
        return {
            "profit": "Unknown",
            "revenue": "Unknown",
            "debt": "Unknown",
            "investment_advice": "Unable to determine"
        }
