import re
import random
import yake
import streamlit as st
import pdfplumber
import docx2txt
from pptx import Presentation
import spacy, io, os, hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fpdf import FPDF
import sqlite3, datetime
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import pandas as pd

def get_ideal_answer_bank(path):
    if not os.path.exists(path):
        return {}, f"❌ QA.txt not found at: {path}"
    else:
        return load_ideal_answer_bank(path), None
    
import uuid
import requests

def get_copyleaks_access_token(user_id, api_key):
    response = requests.post("https://id.copyleaks.com/v3/account/login/api", json={
        "email": user_id,
        "key": api_key
    })
    return response.json().get("access_token", "") if response.status_code == 200 else None

def run_copyleaks_detection(text, access_token, user_id):
    scan_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "base64": text.encode("utf-8").decode("utf-8"),
        "filename": f"Answer_{scan_id}.txt",
        "properties": {
            "sandbox": True  # Free tier
        }
    }
    response = requests.put(f"https://api.copyleaks.com/v3/scans/submit/{scan_id}", headers=headers, json=data)
    return scan_id if response.status_code in [200, 201] else None

def generate_combined_report(candidate, results):
    txt = f"Copyleaks Detection Report for {candidate}\n\n"
    md = f"# Copyleaks Report for {candidate}\n\n"
    html = f"<html><body><h1>Copyleaks Report for {candidate}</h1><ul>"

    for i, r in enumerate(results):
        txt += f"Q{i+1}: {r}\n"
        md += f"**Q{i+1}**: {r}\n\n"
        html += f"<li><strong>Q{i+1}</strong>: {r}</li>"

    html += "</ul></body></html>"
    return txt, md, html

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as cosine_sim
import numpy as np

def hybrid_similarity(candidate_answer, ideal_answer):
    """
    Combines TF-IDF cosine similarity with a semantic embedding similarity.
    Returns a score between 0 and 1.
    """

    # --- TF-IDF Cosine ---
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([ideal_answer, candidate_answer])
    cosine_score = cosine_sim(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # --- Semantic Embeddings ---
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode([ideal_answer, candidate_answer])
        semantic_score = cosine_sim(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]
    except Exception:
        semantic_score = cosine_score  # fallback

    # Weighted score (adjust as needed)
    final_score = round((0.5 * cosine_score) + (0.5 * semantic_score), 3)
    return final_score

def minillm_grade(candidate_answer, ideal_answer):
    """
    Uses a lightweight LLM like MiniLLM to semantically grade the answer.
    Returns (score between 0-1, reasoning string).
    """
    import openai  # or your chosen MiniLLM client

    prompt = f"""
    You are an interview evaluator.
    Compare the candidate's answer to the ideal answer.
    Candidate Answer: {candidate_answer}
    Ideal Answer: {ideal_answer}

    Give:
    - A numeric score from 0 to 1 (1 = perfect answer, 0 = completely wrong)
    - A short reasoning (max 2 sentences).
    Format: SCORE: <score>
    REASON: <reason>
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Replace with your MiniLLM API
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    # Extract score & reasoning
    score_line = [line for line in content.split("\n") if "SCORE:" in line]
    reason_line = [line for line in content.split("\n") if "REASON:" in line]

    score = float(score_line[0].split(":")[1].strip()) if score_line else 0
    reason = reason_line[0].split(":", 1)[1].strip() if reason_line else "No reason provided."

    return score, reason

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as cosine_sim
import numpy as np

def hybrid_similarity(candidate_answer, ideal_answer):
    """
    Combines TF-IDF cosine similarity with a semantic embedding similarity.
    Returns a score between 0 and 1.
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([ideal_answer, candidate_answer])
    cosine_score = cosine_sim(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode([ideal_answer, candidate_answer])
        semantic_score = cosine_sim([embeddings[0]], [embeddings[1]])[0][0]
    except Exception:
        semantic_score = cosine_score

    final_score = round((0.5 * cosine_score) + (0.5 * semantic_score), 3)
    return final_score

def minillm_grade(candidate_answer, ideal_answer):
    """
    Placeholder MiniLLM scoring.
    Replace this with actual API call or local inference.
    """
    try:
        # Example: simple keyword matching fallback
        overlap = len(set(candidate_answer.lower().split()) & set(ideal_answer.lower().split()))
        ratio = overlap / max(1, len(set(ideal_answer.lower().split())))
        score = round(ratio, 3)
        reason = f"Overlap ratio: {score}"
        return score, reason
    except Exception as e:
        return 0, f"Error in MiniLLM scoring: {e}"
    
from gpt4all import GPT4All
import os

# Path to your local model
MODEL_PATH = os.path.join("models", "ggml-gpt4all-j-v1.3-groovy.bin")

# Load the local model once at startup
local_llm = GPT4All(MODEL_PATH)

def generate_questions_and_ideals(jd_section, qtype, n=5):
    """
    Generates N questions + ideal answers from a JD section and question type.
    Uses the local GPT4All model.
    """
    prompt = f"""
    You are an expert interviewer. Based on the following job description section:

    {jd_section}

    Generate {n} {qtype} interview questions.
    For each question, also provide a short (2–3 sentence) ideal answer.
    Format your response as:
    Q1: <question>
    Ideal: <ideal answer>
    Q2: ...
    """
    output = local_llm.prompt(prompt, max_tokens=500)

    questions, ideals = [], []
    for line in output.split("\n"):
        if line.strip().startswith("Q"):
            q_text = line.split(":", 1)[-1].strip()
            questions.append(q_text)
        elif line.strip().lower().startswith("ideal"):
            ideal_text = line.split(":", 1)[-1].strip()
            ideals.append(ideal_text)

    return questions[:n], ideals[:n]


def llm_grade_answer(candidate_answer, ideal_answer):
    """
    Uses local GPT4All to grade a candidate answer against an ideal answer.
    Returns score (0–1), reasoning, and optionally a better suggested answer.
    """
    prompt = f"""
    Compare the following candidate answer to the ideal answer.

    Ideal Answer: {ideal_answer}
    Candidate Answer: {candidate_answer}

    Give a score between 0 and 1 (1 = perfect match, 0 = totally wrong).
    Then explain in 1–2 sentences why.

    Format:
    Score: <number>
    Reason: <text>
    BestAnswer: <optional improved answer>
    """
    output = local_llm.prompt(prompt, max_tokens=300)

    score, reason, best = 0, "", ""
    for line in output.split("\n"):
        if line.lower().startswith("score"):
            try:
                score = float(line.split(":")[1].strip())
            except:
                score = 0
        elif line.lower().startswith("reason"):
            reason = line.split(":", 1)[-1].strip()
        elif line.lower().startswith("bestanswer"):
            best = line.split(":", 1)[-1].strip()

    return score, reason, best

# ---- Ollama helpers (paste near your imports) ----
try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

def generate_questions_and_ideals_ollama(jd_section, qtype, n=5, model="mistral"):
    """
    Generate n questions and short ideal answers from jd_section using Ollama.
    Returns (questions_list, ideals_list). Falls back to keyword generator if Ollama not available or parse fails.
    """
    # fallback generator if Ollama not present
    if not OLLAMA_AVAILABLE:
        qs = generate_keywords_qs(jd_section, qtype, n, use_hardcoded=False)
        ideals = [f"Short ideal answer: {q}" for q in qs]
        return qs, ideals

    prompt = f"""
You are an expert interviewer. Based on the job description excerpt below, create {n} {qtype} interview questions.
For each question provide a short ideal answer (1-3 sentences).
Format exactly (one Q/A per block):

Q1: <question>
A1: <ideal answer>

Q2: ...
"""
    try:
        res = ollama.chat(model=model, messages=[{"role":"user","content":prompt}])
        text = res["message"]["content"].strip()
    except Exception as e:
        # fallback
        qs = generate_keywords_qs(jd_section, qtype, n, use_hardcoded=False)
        ideals = [f"Short ideal answer: {q}" for q in qs]
        return qs, ideals

    questions, ideals = [], []
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"^q\d+\s*:", line.lower()):
            q = line.split(":",1)[1].strip()
            questions.append(q)
        elif re.match(r"^a\d+\s*:", line.lower()):
            a = line.split(":",1)[1].strip()
            ideals.append(a)

    # Try block parsing if counts mismatch
    if not questions or len(questions) != len(ideals):
        questions, ideals = [], []
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for b in blocks:
            qline = next((l for l in b.splitlines() if l.lower().startswith("q")), None)
            aline = next((l for l in b.splitlines() if l.lower().startswith("a")), None)
            if qline and aline:
                questions.append(qline.split(":",1)[1].strip())
                ideals.append(aline.split(":",1)[1].strip())

    if not questions:
        qs = generate_keywords_qs(jd_section, qtype, n, use_hardcoded=False)
        ideals = [f"Short ideal answer: {q}" for q in qs]
        return qs, ideals

    return questions[:n], ideals[:n]


def llm_grade_answer_ollama(candidate_answer, ideal_answer, model="mistral"):
    """
    Use Ollama to grade candidate_answer vs ideal_answer.
    Returns (llm_score_float_between_0_1, reason_str, best_answer_str).
    Fallback: simple overlap heuristic.
    """
    if not OLLAMA_AVAILABLE:
        overlap = len(set(candidate_answer.lower().split()) & set(ideal_answer.lower().split()))
        denom = max(1, len(set(ideal_answer.lower().split())))
        ratio = overlap / denom
        return round(ratio, 3), f"Overlap fallback: {ratio:.3f}", ideal_answer

    prompt = f"""
Compare the Candidate Answer to the Ideal Answer below.

Ideal Answer:
{ideal_answer}

Candidate Answer:
{candidate_answer}

Output EXACTLY these three labeled lines (no extra chatter):
SCORE: <number between 0 and 1>
REASON: <one-sentence explanation>
BEST_ANSWER: <a concise 1-2 sentence improved ideal answer>
"""
    try:
        res = ollama.chat(model=model, messages=[{"role":"user","content":prompt}])
        out = res["message"]["content"].strip()
    except Exception as e:
        return 0.0, f"LLM error: {e}", ideal_answer

    score, reason, best = 0.0, "", ""
    for line in out.splitlines():
        low = line.strip().lower()
        if low.startswith("score:"):
            try:
                score = float(line.split(":",1)[1].strip())
            except:
                score = 0.0
        elif low.startswith("reason:"):
            reason = line.split(":",1)[1].strip()
        elif low.startswith("best_answer:") or low.startswith("bestanswer:"):
            best = line.split(":",1)[1].strip()
    score = max(0.0, min(1.0, float(score if score else 0.0)))
    return round(score, 3), reason, best

# ========== Page Setup ==========
for key in [
    "questions", "scores", "ideal", "cand", "jd", "section", "role",
    "qtype", "mode", "answers", "feedback"
]:
    if key not in st.session_state:
        st.session_state[key] = "" if key not in ["questions", "scores", "ideal", "answers"] else []
st.set_page_config(page_title="Smart Interview Assistant", layout="wide")

# Ensure required session_state keys exist to avoid AttributeError
for key in ["questions", "scores", "ideal"]:
    if key not in st.session_state:
        st.session_state[key] = []
for key in ["cand", "jd", "section"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ========== Constants ==========
DB = "interview_assistant.db"
import os

# ========== Load SpaCy Model ==========
nlp = spacy.load("en_core_web_sm")

# ========== Database Setup ==========
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate TEXT,
        timestamp TEXT,
        jd TEXT,
        questions TEXT,
        ideal TEXT,
        answers TEXT,
        scores TEXT,
        verdicts TEXT,
        feedback TEXT
    )
""")
    ensure_column_exists("interviews", "verdicts", "TEXT")
    conn.commit()
    conn.close()

def ensure_column_exists(table, column, dtype="TEXT"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute(f"SELECT {column} FROM {table} LIMIT 1")
    except sqlite3.OperationalError:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {dtype}")
        conn.commit()
    conn.close()

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def check_login(u, p):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password_hash=?", (u, hash_pw(p)))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ⏬ Initialization
init_db()
ensure_column_exists("interviews", "feedback", "TEXT")

# ========== Load Ideal Answer Bank ==========
def load_ideal_answer_bank(path):
    bank = {}
    role = section = None
    question = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Identify new section like "Pharmaceutical Sales Representative — Technical Questions"
            if "—" in line and "Questions" in line:
                parts = line.split("—")
                role = parts[0].strip()
                section = parts[1].replace("Questions", "").strip()
                bank.setdefault(role, {}).setdefault(section, {})
                question = None
            # Detect question line starting with "1. ", "2. ", etc.
            elif re.match(r"^\d+\.\s", line):
                question = line.split(". ", 1)[1].strip()
            # Capture answer (the line right after the question)
            elif question:
                bank[role][section][question] = line
                question = None
    return bank

# ========== Chart Plotting Functions ==========
def plot_bar(scores):
    fig, ax = plt.subplots(figsize=(6,4))
    ax.bar(range(len(scores)), scores, color='skyblue')
    ax.set_ylim(0, 1)
    ax.set_title("Scores per Question")
    ax.set_xlabel("Question")
    ax.set_ylabel("Similarity Score")
    ax.set_xticks(range(len(scores)))
    ax.set_xticklabels([f"Q{i+1}" for i in range(len(scores))])
    plt.tight_layout()
    return fig

def plot_line(scores):
    fig = px.line(x=list(range(1, len(scores)+1)), y=scores, markers=True)
    fig.update_layout(title="Score Trend", xaxis_title="Question", yaxis_title="Similarity Score")
    return fig

def plot_radar(scores):
    categories = [f"Q{i+1}" for i in range(len(scores))]
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    values = scores + [scores[0]]  # Close the radar loop
    angles += angles[:1]
    fig, ax = plt.subplots(subplot_kw={'polar':True})
    ax.plot(angles, values, color='orange', linewidth=2)
    ax.fill(angles, values, color='orange', alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 1)
    ax.set_title("Radar Chart of Scores")
    return fig

# ========== Text & PDF Processing ==========
def extract_text(file):
    name = file.name.lower()
    if name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
    elif name.endswith(".docx"):
        return docx2txt.process(file)
    elif name.endswith(".pptx"):
        txt = ""
        prs = Presentation(file)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    txt += shape.text + "\n"
        return txt
    elif name.endswith(".txt"):
        return io.TextIOWrapper(file, encoding="utf-8").read()
    return ""

def generate_pdf(candidate, questions, answers, scores):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Interview Report: {candidate}", ln=True)
    for i, (q, a, s) in enumerate(zip(questions, answers, scores)):
        pdf.multi_cell(0, 10, txt=f"Q{i+1}: {q}\nA: {a}\nScore: {s:.2f}\n")
    fn = f"{candidate}_report.pdf"
    pdf.output(fn)
    return fn

def export_excel(rows):
    df = pd.DataFrame([
        {"Candidate": r[1], "Date": r[2], "AvgScore": np.mean(list(map(float, r[7].split(","))))}
        for r in rows
    ])
    fn = "interviews.xlsx"
    df.to_excel(fn, index=False)
    return fn

# ========== Similarity and Key Phrase Extraction ==========
def score_similarity(expected, actual):
    if not actual.strip(): 
        return 0.0
    vectorizer = TfidfVectorizer().fit([expected, actual])
    vecs = vectorizer.transform([expected, actual])
    return cosine_similarity(vecs[0], vecs[1])[0][0]

from difflib import SequenceMatcher
def get_answer_verdict(candidate_answer, ideal_answer, score_threshold=0.75):
    sim = score_similarity(ideal_answer, candidate_answer)
    copied_score = SequenceMatcher(None, candidate_answer.lower(), ideal_answer.lower()).ratio()

    if not candidate_answer.strip():
        verdict = "No Answer"
        explanation = "The candidate didn't provide any answer."
    elif copied_score > 0.85:
        verdict = "Copied"
        explanation = "The candidate's answer is nearly identical to the expected answer. Likely copied."
    elif sim >= score_threshold:
        verdict = "Correct"
        explanation = "The candidate's answer is accurate and well aligned with the expected answer."
    elif 0.4 <= sim < score_threshold:
        verdict = "Partially Correct"
        explanation = "The answer is somewhat correct but missing key elements or details."
    else:
        verdict = "Incorrect"
        explanation = "The answer does not match the expected response and contains factual or conceptual errors."

    return {
        "similarity": round(sim, 2),
        "copied_score": round(copied_score, 2),
        "verdict": verdict,
        "explanation": explanation
    }

def highlight_difference(expected, actual):
    matcher = SequenceMatcher(None, expected.lower(), actual.lower())
    matches = matcher.get_matching_blocks()

    common = []
    for match in matches:
        if match.size > 5:
            common.append(expected[match.a: match.a + match.size])

    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())

    missing_from_candidate = expected_words - actual_words   # 🟡 Gaps (not mentioned)
    wrong_in_candidate = actual_words - expected_words        # 🔴 Extra / wrong info

    return (
        ", ".join(set(common)), 
        ", ".join(missing_from_candidate), 
        ", ".join(wrong_in_candidate)
    )

def extract_key_phrases(text):
    kw_extractor = yake.KeywordExtractor(lan="en", top=10)
    keywords = kw_extractor.extract_keywords(text)
    return [kw for kw, _ in keywords if len(kw.split()) <= 5]

def generate_keywords_qs(section, qtype, count, use_hardcoded=True):
    role_patterns = {
        "Pharmaceutical Sales Representative": {
            "Technical": [
                "How have you applied your knowledge of pharmaceutical regulations during a product promotion campaign?",
                "Describe a challenge you faced when communicating clinical data to doctors.",
                "Can you explain your process for tracking competitor activity in the pharma industry?",
                "What strategies have you used to ensure accurate and compliant product promotion?",
                "In what ways have you used reporting tools to track your sales performance?",
            ],
            "Behavioral": [
                "Tell me about a time when you successfully turned around a doctor’s initial hesitation about your product.",
                "How did you handle a situation where a pharmacy was reluctant to stock your drug?",
                "Describe an instance where traveling frequently affected your performance — how did you adapt?",
                "What did you learn from a sales pitch that didn’t go as expected?",
                "How have your interactions with healthcare professionals shaped your sales approach?",
            ],
            "Mixed": [
                "How do you approach building long-term relationships with hospitals and clinics?",
                "Can you walk me through your method of preparing for a sales meeting?",
                "What’s your strategy for keeping up with both market trends and compliance requirements?",
                "How has your understanding of clinical data helped you communicate more effectively?",
                "Describe a time you balanced aggressive targets with ethical promotion practices.",
            ],
        }
        # ... (additional roles can be added here)
    }
    for role, qtypes in role_patterns.items():
        if re.search(role, section, re.IGNORECASE) and use_hardcoded:
            if qtype in qtypes:
                return qtypes[qtype][:count]
    key_phrases = extract_key_phrases(section)
    if not key_phrases:
        key_phrases = [s.strip() for s in re.split(r'[.\n]', section) if len(s.split()) > 3]
    prefix_map = {
        "Technical": ["Explain your experience with {}.", "How have you used {} in your projects?", "Describe a challenge you faced with {}."],
        "Behavioral": ["Tell me about a time you handled {}.", "How have you approached situations involving {}?", "Describe an experience related to {}."],
        "Mixed": ["How do you approach {}?", "Can you discuss a time when you applied {}?", "What do you find challenging about {}?"]
    }
    templates = prefix_map.get(qtype, [])
    if templates and key_phrases:
        return [random.choice(templates).format(phrase) for phrase in random.sample(key_phrases, min(len(key_phrases), count))]
    return []

# ========== Interview DB Operations ==========
def save_interview(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    ts = datetime.datetime.now().isoformat()
    c.execute("""
    INSERT INTO interviews(candidate, timestamp, jd, questions, ideal, answers, scores, verdicts, feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    data['candidate'], ts, data['jd'],
    "\n".join(data['questions']),
    "\n".join(data['ideal']),
    "\n".join(data['answers']),
    ",".join(f"{s:.2f}" for s in data['scores']),
    "\n".join([v["verdict"] for v in data["verdicts"]]),
    data.get('feedback', '')
))
    conn.commit()
    conn.close()

def load_interviews():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute("SELECT * FROM interviews ORDER BY timestamp DESC").fetchall()
    conn.close()
    return rows

# ========== Export / Search Helpers ==========
def extract_multiple_jds(text):
    pattern = r"(?i)(Job Title:|Position:|Opening for|Role:)(.*)"
    matches = list(re.finditer(pattern, text))
    starts = [m.start() for m in matches] + [len(text)]
    jds = {}
    for i in range(len(matches)):
        job_title = matches[i].group(2).strip()[:50].replace('\n', ' ')
        key = f"{job_title}" if job_title else f"JD {i+1}"
        jds[key] = text[starts[i]:starts[i+1]].strip()
    return jds

def extract_sections_by_patterns(text):
    section_titles = {
        "Summary": r"(summary:|position overview)",
        "Responsibilities": r"(essential duties|responsibilities include|you will be responsible)",
        "Supervisory Responsibilities": r"(supervisory responsibilities)",
        "Competencies": r"(competencies)",
        "Qualifications": r"(qualifications|required skills)",
        "Education and Experience": r"(education and/or experience|educational background)",
        "Language Skills": r"(language skills)",
        "Mathematical Skills": r"(mathematical skills)",
        "Reasoning Ability": r"(reasoning ability)",
        "Computer Skills": r"(computer skills)",
        "Certificates": r"(certificates|licenses|registrations)",
        "Other Skills": r"(other skills and abilities)",
        "Physical Demands": r"(physical demands)",
        "Work Environment": r"(work environment)",
    }

    lines = text.splitlines()
    sections = {}
    current_section = "Introduction"
    buffer = []

    for line in lines:
        lower = line.strip().lower()
        matched = False
        for title, pattern in section_titles.items():
            if re.search(pattern, lower):
                if buffer:
                    sections[current_section] = "\n".join(buffer).strip()
                buffer = [line]
                current_section = title
                matched = True
                break
        if not matched:
            buffer.append(line)

    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


def extract_sections_hybrid(text):
    sections = extract_sections_by_patterns(text)
    if not sections or len(sections) == 1:
        # Fallback: split into paragraph chunks if structured titles not found
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        chunk_size = 5
        sections = {}
        for i in range(0, len(lines), chunk_size):
            key = f"Part {i//chunk_size + 1}"
            sections[key] = "\n".join(lines[i:i+chunk_size])
    return sections

# ========== Streamlit UI ==========

# Header with Logout if logged in
if 'user' in st.session_state:
    cols = st.columns([9, 1])
    cols[0].markdown("### 🧠 Smart Interview Assistant")
    if cols[1].button("Logout", key="logout_button"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
else:
    st.title("🧠 Smart Interview Assistant")

# Login / Register
if 'user' not in st.session_state:
    mode = st.selectbox("Login/Register", ["Login", "Register"], key="mode")
    u = st.text_input("Username", key="u")
    p = st.text_input("Password", type="password", key="p")
    if st.button(mode):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        if mode == "Register":
            try:
                # For simplicity, all new users registered as Interviewers
                c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)", (u, hash_pw(p), "Interviewer"))
                conn.commit()
                st.success("Registered! Please login.")
            except Exception:
                st.error("Username already taken.")
        else:
            role = check_login(u, p)
            if role:
                st.session_state.user = u
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid credentials.")
        conn.close()
    st.stop()

# Load QA.txt safely after login
QA_FILE = os.path.join(os.path.dirname(__file__), "QA.txt")
ideal_answer_bank, qa_error = get_ideal_answer_bank(QA_FILE)

if qa_error:
    st.warning(qa_error)

# Sidebar: show logged in user and role
st.sidebar.markdown(f"Logged in as **{st.session_state.user}** ({st.session_state.role})")

# Main Tabs
tabs = st.tabs(["🧠 Interview Assistant", "📊 Dashboard", "📝 Reports", "🔍 Search / Filter"])
with tabs[0]:
    st.header("🧠 Smart Interview Assistant")

    cand = st.text_input("Candidate Name", key="cand_input")

    file = st.file_uploader("Upload Job Description (any format)", type=None, key="jd_file")
    full_jd_text, jd_options = "", {}

    def extract_text_generic(file):
        name = file.name.lower()
        if name.endswith((".pdf", ".docx", ".pptx", ".txt")):
            return extract_text(file)
        elif name.endswith(".csv"):
            return pd.read_csv(file).to_string()
        elif name.endswith((".xls", ".xlsx")):
            return pd.read_excel(file).to_string()
        elif name.endswith((".py", ".ipynb", ".java", ".m")):
            return file.read().decode("utf-8")
        elif name.endswith((".mp3", ".wav", ".mp4")):
            return "[AUDIO/VIDEO FILE UPLOADED — transcript will appear here after grading]"
        else:
            return "[Unsupported format]"

    if file:
        raw = extract_text_generic(file)
        jds = extract_multiple_jds(raw)
        jd_options = list(jds.keys())
        selected_jd = st.selectbox("Select Job Title", ["Select..."] + jd_options, key="jd_select")
        if selected_jd != "Select...":
            full_jd_text = jds[selected_jd]

    if full_jd_text:
        sections = extract_sections_hybrid(full_jd_text)
        sections["Full JD"] = full_jd_text
        selected_section = st.selectbox("Select JD Section", list(sections.keys()), key="jd_section")
        st.markdown("### Selected Section Content")
        st.info(sections[selected_section])

        roles = list(ideal_answer_bank.keys())
        selected_role = st.selectbox("Select Role", ["Select..."] + roles, key="role_select")

        question_count = st.slider("Number of Questions", 3, 10, 5, key="qcount_slider")

        qtypes = ["Technical", "Behavioral", "Mixed"]
        selected_type = st.selectbox("Select Question Type", ["Select..."] + qtypes, key="qtype_select")

        if selected_role != "Select..." and selected_type != "Select...":
            mode = st.radio("Question Mode", ["RAG", "Non-RAG"], key="rag_radio")

            qa_pairs = ideal_answer_bank[selected_role][selected_type]
            all_q = list(qa_pairs.keys())
            random.shuffle(all_q)
            if mode == "RAG":
                selected_qs = all_q[:question_count]
            else:
                selected_qs = all_q[question_count:question_count * 2]
                if len(selected_qs) < question_count:
                    selected_qs += all_q[:question_count - len(selected_qs)]

            if st.button("Generate Questions", key="generate_btn"):
                st.session_state.questions = selected_qs
                st.session_state.ideal = [qa_pairs[q] for q in selected_qs]
                st.session_state.jd = full_jd_text
                st.session_state.section = selected_section
                st.session_state.cand = cand
                st.session_state.role = selected_role
                st.session_state.qtype = selected_type
                st.session_state.mode = mode
                st.rerun()

    if st.session_state.questions:
       if all([st.session_state.cand, st.session_state.role, st.session_state.qtype, st.session_state.mode]):
        st.subheader(f"Interviewing: {st.session_state.cand} | {st.session_state.role} | {st.session_state.qtype} | {st.session_state.mode}")

input_mode = st.selectbox(
    "Answer Input Mode", 
    ["Type Now", "Upload File", "Voice Assessment"], 
    key="ans_input_mode"
)
answers, transcripts = [], []
        
def transcribe_audio(audio_bytes):
            return "[Stub Transcript] Whisper transcription logic here"

for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}: {q}**")

for i, q in enumerate(st.session_state.questions):
    st.markdown(f"**Q{i+1}: {q}**")

    if input_mode == "Type Now":
        key = f"answer_q{i}"
        if key not in st.session_state:
            st.session_state[key] = ""  # 👈 initialize once

        a = st.text_area(
    f"Your Answer (Q{i+1})",
    value=st.session_state[key],  # Load value
    key=key
)

    elif input_mode == "Upload File":
        a_file = st.file_uploader(f"Upload Answer File Q{i+1}", type=None, key=f"ansfile_{i}")
        a = extract_text_generic(a_file) if a_file else ""

    else:  # Voice Assessment
        a_audio = st.audio(label=f"Record Voice Q{i+1}", format="audio/wav", key=f"audio_{i}")
        a = transcribe_audio(a_audio) if a_audio else "[Awaiting audio input]"

    answers.append(a or "")

# ---- Full Grade & Save Interview block (replace your current one) ----
if st.button("Grade & Save Interview", key="grade_btn"):

    # 1) Generate dynamic Qs & Ideals if session doesn't already have them (or you prefer regen)
    jd_for_generation = st.session_state.get("jd") or st.session_state.get("section") or ""
    qtype_for_generation = st.session_state.get("qtype") or "Mixed"
    desired_n = st.session_state.get("qcount", len(st.session_state.questions) or 5)

    try:
        gen_qs, gen_ideals = generate_questions_and_ideals_ollama(jd_for_generation, qtype_for_generation, n=desired_n)
        # optionally overwrite session questions/ideal so UI shows generated ones later
        st.session_state.generated_questions = gen_qs
        st.session_state.generated_ideals = gen_ideals
        st.session_state.questions = gen_qs
        st.session_state.ideal = gen_ideals
    except Exception as e:
        st.error(f"Question generation failed, using existing questions: {e}")
        gen_qs = st.session_state.get("questions", [])
        gen_ideals = st.session_state.get("ideal", [])

    # 2) Gather answers from session (textareas keys must match how you store them)
    answers_list = []
    # if the UI stores answers in keys like answer_q_0 ... answer_q_n:
    for i in range(len(gen_qs)):
        answers_list.append(st.session_state.get(f"answer_q_{i}", "").strip())

    # ensure lengths align
    if len(answers_list) < len(gen_qs):
        answers_list += [""] * (len(gen_qs) - len(answers_list))
    elif len(answers_list) > len(gen_qs):
        answers_list = answers_list[:len(gen_qs)]

    tfidf_scores, highlights, verdicts = [], [], []

    # 3) Grade each answer
    for idx, (q, a) in enumerate(zip(gen_qs, answers_list)):
        ideal = gen_ideals[idx] if idx < len(gen_ideals) else ""

        # hybrid similarity (your hybrid function)
        try:
            hybrid_score = hybrid_similarity(a, ideal)
        except Exception as e:
            hybrid_score = 0.0

        # LLM grading
        try:
            llm_score, llm_reason, llm_best = llm_grade_answer_ollama(a, ideal)
        except Exception as e:
            llm_score, llm_reason, llm_best = 0.0, f"LLM failed: {e}", ""

        # final score (adjust weights here)
        final_score = round((0.6 * hybrid_score) + (0.4 * llm_score), 3)
        tfidf_scores.append(final_score)

        # highlights (common, missing, wrong)
        common, missing, wrong = highlight_difference(ideal, a)
        highlights.append({"common": common, "missing": missing, "wrong": wrong})

        # base verdict
        base_verdict = get_answer_verdict(a, ideal)
        # extend verdict with LLM info and scores
        base_verdict.update({
            "hybrid_score": round(hybrid_score, 3),
            "llm_score": llm_score,
            "llm_reason": llm_reason,
            "llm_best": llm_best,
            "final_score": final_score
        })
        verdicts.append(base_verdict)

    # 4) Charts & interpretation
    st.subheader("📊 Score Summary (Hybrid + LLM)")
    try:
        st.pyplot(plot_bar(tfidf_scores))
    except Exception:
        st.write("Unable to render bar chart.")
    st.markdown("**Interpretation:** Final score = 60% hybrid similarity + 40% LLM semantic score.")
    try:
        # unique key to avoid duplicate element id errors
        st.plotly_chart(plot_line(tfidf_scores), key=f"line_chart_{random.randint(0,999999)}")
    except Exception:
        pass
    try:
        st.pyplot(plot_radar(tfidf_scores))
    except Exception:
        pass

    # 5) Per-question display, verdict badge, LLM reasoning, flag button
    for i, (q, a, ideal, score, hl, v) in enumerate(zip(gen_qs, answers_list, gen_ideals, tfidf_scores, highlights, verdicts)):
        st.markdown(f"---\n### Q{i+1}: {q}")
        st.write(f"**Generated Ideal:** {ideal}")
        st.write(f"**Candidate Answer:** {a}")
        st.write(f"**Final Score:** {score:.3f}  (Hybrid: {v.get('hybrid_score')}, LLM: {v.get('llm_score')})")
        st.success(f"✅ Matched: {hl['common']}")
        st.warning(f"🟡 Missing: {hl['missing']}")
        st.error(f"🔴 Extra / Wrong Info: {hl['wrong']}")

        verdict_label = v.get("verdict", "Unknown")
        badge = {"Correct":"🟢","Partially Correct":"🟡","Copied":"🔴","Incorrect":"🔴","No Answer":"⚪"}.get(verdict_label, "❓")
        st.markdown(f"**Verdict:** {badge} {verdict_label}")
        st.info(f"**Explanation:** {v.get('explanation','')}")
        st.markdown(f"**LLM Reasoning:** {v.get('llm_reason','')}")
        if v.get("llm_best"):
            st.markdown(f"**LLM Suggested Ideal:** {v.get('llm_best')}")

        if st.button(f"🚩 Flag Suspicious (Q{i+1})", key=f"flag_{i}"):
            flagged = st.session_state.get("flags", [])
            flagged.append({"candidate": st.session_state.get("cand",""), "q_index": i, "question": q})
            st.session_state["flags"] = flagged
            st.warning(f"Q{i+1} flagged for review.")

    # 6) Save to DB (store verdicts as JSON so LLM_reason & best are persisted)
    save_interview({
        'candidate': st.session_state.get("cand", ""),
        'jd': jd_for_generation,
        'questions': gen_qs,
        'ideal': gen_ideals,
        'answers': answers_list,
        'scores': tfidf_scores,
        'verdicts': verdicts,
        'feedback': f"Role: {st.session_state.get('role','')}, Type: {st.session_state.get('qtype','')}, Mode: Ollama-Dynamic"
    })

    st.success("✅ Interview graded, saved, and LLM-checked.")

# Tab 1: Dashboard (Aggregate view)
with tabs[1]:
    st.header("📊 Candidate Dashboard")
    rows = load_interviews()

    if rows:
        selected = st.selectbox("Select Candidate", [f"{r[1]} – {r[2][:10]}" for r in rows])
        idx = [f"{r[1]} – {r[2][:10]}" for r in rows].index(selected)

        scores = list(map(float, rows[idx][7].split(",")))
        st.pyplot(plot_bar(scores))
        st.plotly_chart(plot_line(scores))
        st.pyplot(plot_radar(scores))

        # ✅ INSERT THIS INSIDE `if rows:` ⬇️
        verdict_list = rows[idx][8].split("\n")
        verdict_counts = pd.Series(verdict_list).value_counts()

        st.subheader("🧠 Verdict Summary")
        st.bar_chart(verdict_counts)

        fig = px.pie(
            names=verdict_counts.index,
            values=verdict_counts.values,
            title="Verdict Distribution"
        )
        st.plotly_chart(fig)

    else:
        st.warning("No interviews available.")

# Optional Pie Chart
fig = px.pie(
    names=verdict_counts.index,
    values=verdict_counts.values,
    title="Verdict Distribution"
)
st.plotly_chart(fig)

# Tab 2: Reports (Export)
with tabs[2]:
    st.header("📝 Reports")

    # Load and pad rows to avoid IndexError
    rows = [r + ("",) * (9 - len(r)) for r in load_interviews()]

    formats = [
        "PDF", "Word", "Excel", "TXT", "CSV", "HTML", "Markdown",
        "Python (.py)", "Java (.java)", "JSON", "XML",
        "SQLITE (.db)", "CSV (.csv)", "Text (.txt)", "DOCX (.docx)"
    ]

    fmt = st.selectbox("Export Format", formats)

    if rows:
        # Build DataFrame safely
        df = pd.DataFrame([
    {
        "Candidate": r[1] if len(r) > 1 else "",
        "Date": r[2][:10] if len(r) > 2 else "",
        "JD": r[3] if len(r) > 3 else "",
        "Questions": r[4] if len(r) > 4 else "",
        "Ideal": r[5] if len(r) > 5 else "",
        "Answers": r[6] if len(r) > 6 else "",
        "Copyleaks": r[7] if len(r) > 7 else "",
        "Scores": r[8] if len(r) > 8 else "",
        "Verdicts": r[9] if len(r) > 9 else "",
        "Feedback": r[10] if len(r) > 10 else ""
    } for r in rows
])

        if st.button("Download Report"):
            if fmt == "Excel":
                fn = "report.xlsx"
                df.to_excel(fn, index=False)
                with open(fn, "rb") as f:
                    st.download_button("Download Excel Report", f, file_name=fn)

            elif fmt == "TXT" or fmt == "Text (.txt)":
                content = df.to_string(index=False)
                st.download_button("Download TXT Report", content, file_name="report.txt", mime="text/plain")

            elif fmt == "CSV" or fmt == "CSV (.csv)":
                csv = df.to_csv(index=False)
                st.download_button("Download CSV Report", csv, file_name="report.csv", mime="text/csv")

            elif fmt == "HTML":
                html = df.to_html(index=False)
                st.download_button("Download HTML Report", html, file_name="report.html", mime="text/html")

            elif fmt == "Markdown":
                md = df.to_markdown(index=False)
                st.download_button("Download Markdown Report", md, file_name="report.md", mime="text/markdown")

            elif fmt == "JSON":
                js = df.to_json(orient="records", indent=2)
                st.download_button("Download JSON Report", js, file_name="report.json", mime="application/json")

            elif fmt == "XML":
                xml = "<data>\n" + "\n".join(
                    ["  <row>" + "".join([f"<{col}>{val}</{col}>" for col, val in row.items()]) + "</row>" for _, row in df.iterrows()]
                ) + "\n</data>"
                st.download_button("Download XML Report", xml, file_name="report.xml", mime="application/xml")

            elif fmt == "Python (.py)":
                code = "# Interview Report as Python Comment\n" + df.to_string(index=False)
                st.download_button("Download Python File", code, file_name="report.py", mime="text/x-python")

            elif fmt == "Java (.java)":
                code = "// Interview Report as Java Comment\n" + df.to_string(index=False)
                st.download_button("Download Java File", code, file_name="report.java", mime="text/x-java")

            elif fmt == "SQLITE (.db)":
                conn = sqlite3.connect("report.db")
                df.to_sql("interview_data", conn, if_exists="replace", index=False)
                conn.close()
                with open("report.db", "rb") as f:
                    st.download_button("Download SQLite DB", f, file_name="report.db", mime="application/octet-stream")

            elif fmt == "PDF":
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                for idx, row in df.iterrows():
                    pdf.multi_cell(0, 10, txt=f"Candidate: {row['Candidate']}\nDate: {row['Date']}\nScore: {row['Scores']}\n---")
                pdf.output("report.pdf")
                with open("report.pdf", "rb") as f:
                    st.download_button("Download PDF Report", f, file_name="report.pdf", mime="application/pdf")

            elif fmt == "Word" or fmt == "DOCX (.docx)":
                from docx import Document
                doc = Document()
                doc.add_heading("Interview Report", 0)
                for _, row in df.iterrows():
                    doc.add_paragraph(f"Candidate: {row['Candidate']}")
                    doc.add_paragraph(f"Date: {row['Date']}")
                    doc.add_paragraph(f"Score: {row['Scores']}")
                    doc.add_paragraph("-" * 40)
                doc.save("report.docx")
                with open("report.docx", "rb") as f:
                    st.download_button("Download Word Report", f, file_name="report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    else:
        st.warning("No interviews to export yet.")
        
# Tab 3: Search/Filter
with tabs[3]:
    st.header("🔍 Search / Filter")
    interviews = load_interviews()
    interviews = [r + ("",) * (9 - len(r)) for r in interviews]  # ⬅️ Ensure all rows have 9 elements

    df = pd.DataFrame(interviews, columns=[
        "ID", "Candidate", "Timestamp", "JD", "Questions", "Ideal", "Answers", "Scores", "Feedback"
    ])

    if not df.empty:
        search = st.text_input("🔎 Search by Candidate", key="search_name")
        role_filter = st.selectbox(
            "Filter by Role (from Feedback)", ["All"] + df["Feedback"].dropna().unique().tolist(), key="role_filter"
        )
        min_score, max_score = st.slider(
            "Filter by Score Range", 0.0, 1.0, (0.0, 1.0), 0.05, key="score_slider"
        )

        filtered_df = df.copy()
        if search:
            filtered_df = filtered_df[filtered_df["Candidate"].str.contains(search, case=False, na=False)]
        if role_filter != "All":
            filtered_df = filtered_df[filtered_df["Feedback"].str.contains(role_filter, na=False)]

        filtered_df["AvgScore"] = filtered_df["Scores"].apply(
            lambda s: round(np.mean(list(map(float, s.split(",")))), 2)
        )
        filtered_df = filtered_df[filtered_df["AvgScore"].between(min_score, max_score)]

        st.dataframe(filtered_df[["Candidate", "Timestamp", "AvgScore", "Feedback"]])
    else:
        st.warning("No interviews saved yet.")



        # Core libraries
import os
import re
import random
import string
import pandas as pd
import numpy as np

# Streamlit
import streamlit as st

# ML/NLP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

# Load SpaCy model (no internet or API key required)
try:
    nlp = spacy.load("en_core_web_md")  # medium-sized model
except OSError:
    st.error("❌ SpaCy model 'en_core_web_md' not found. Run: python -m spacy download en_core_web_md")
    st.stop()

def tfidf_cosine(text1, text2):
    """Standard TF-IDF Cosine Similarity"""
    vect = TfidfVectorizer().fit([text1, text2])
    vec1 = vect.transform([text1])
    vec2 = vect.transform([text2])
    return cosine_similarity(vec1, vec2)[0][0]

def get_cosine_similarity_spacy(text1, text2):
    """Semantic similarity using SpaCy vectors"""
    vec1 = nlp(text1).vector.reshape(1, -1)
    vec2 = nlp(text2).vector.reshape(1, -1)
    return cosine_similarity(vec1, vec2)[0][0]

def hybrid_similarity(text1, text2):
    """Weighted average of TF-IDF, Jaccard, and SpaCy semantic similarity"""
    tfidf_score = tfidf_cosine(text1, text2)

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    jaccard_score = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0

    spacy_score = get_cosine_similarity_spacy(text1, text2)

    final_score = (0.4 * tfidf_score) + (0.3 * jaccard_score) + (0.3 * spacy_score)
    return round(final_score, 4)