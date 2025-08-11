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
    c.execute("""CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate TEXT,
        timestamp TEXT,
        jd TEXT,
        questions TEXT,
        ideal TEXT,
        answers TEXT,
        scores TEXT
        -- NOTE: Don't include feedback here if your DB already exists
    )""")
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

def highlight_difference(expected, actual):
    matcher = SequenceMatcher(None, expected.lower(), actual.lower())
    matches = matcher.get_matching_blocks()

    common = []
    for match in matches:
        if match.size > 5:
            common.append(expected[match.a: match.a + match.size])

    missed = []
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())
    missed = list(expected_words - actual_words)

    return ", ".join(set(common)), ", ".join(set(missed))

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
        INSERT INTO interviews(candidate, timestamp, jd, questions, ideal, answers, scores, feedback) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (data['candidate'], ts, data['jd'],
         "\n".join(data['questions']),
         "\n".join(data['ideal']),
         "\n".join(data['answers']),
         ",".join(f"{s:.2f}" for s in data['scores']),
         data.get('feedback',''))
    )
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

# ✅ Now wrap the grading and feedback in the button click block
if st.button("Grade & Save Interview", key="grade_btn"):

    tfidf_scores, highlights = [], []
    for q, a, ideal in zip(st.session_state.questions, answers, st.session_state.ideal):
        score = score_similarity(ideal, a)
        common, missed = highlight_difference(ideal, a)
        tfidf_scores.append(score)
        highlights.append({"common": common, "missed": missed})

    # Score Charts
    st.subheader("📊 Score Summary")
    
    st.pyplot(plot_bar(tfidf_scores))
    st.markdown("**Interpretation:** Each bar represents how close the candidate's answer is to the ideal. A taller bar (closer to 1.0) suggests higher alignment in content, structure, and relevance. Bars below 0.8 may indicate incomplete or off-topic answers.")
    st.plotly_chart(plot_line(tfidf_scores))
    st.markdown("**Interpretation:** This line chart tracks the candidate’s performance across questions. Sudden dips or spikes may signal inconsistency or strong/weak areas in knowledge.")
    st.pyplot(plot_radar(tfidf_scores))
    st.markdown("**Interpretation:** The radar chart visually shows strengths and gaps. Sharp drops in some dimensions could mean the candidate is underprepared on certain themes.")

    # Detailed Per-Question Display
    for i, (q, a, ideal, score, hl) in enumerate(zip(st.session_state.questions, answers, st.session_state.ideal, tfidf_scores, highlights)):
        st.markdown(f"---\n### Q{i+1}: {q}")
        st.write(f"**Candidate Answer:** {a}")
        st.write(f"**Ideal Answer:** {ideal}")
        st.write(f"**Score:** {score:.2f}")
        st.success(f"✅ Positives: {hl['common']}")
        st.error(f"❌ Negatives: {hl['missed']}")

    # --- Copyleaks AI/Plagiarism Detection ---
    copyleaks_user_id = "17ef0379-bdb9-42e9-ab21-452f6a880925"
    copyleaks_api_key = "c06efa2f-34ee-4bbf-97e8-c2f4fc803574"
    access_token = get_copyleaks_access_token(copyleaks_user_id, copyleaks_api_key)

    copyleaks_results = []
    if access_token:
        for i, a in enumerate(answers):
            sid = run_copyleaks_detection(a, access_token, copyleaks_user_id)
            status = f"✅ Q{i+1} Submitted – Scan ID: {sid}" if sid else "❌ Submission Failed"
            copyleaks_results.append(status)
    else:
        copyleaks_results = ["❌ Copyleaks Auth Failed"] * len(answers)

    # Display Results
    st.subheader("🧠 Copyleaks AI / Plagiarism Detection")
    for i, res in enumerate(copyleaks_results):
        st.markdown(f"**Q{i+1}:** {res}")

    txt, md, html = generate_combined_report(st.session_state.cand, copyleaks_results)
    st.download_button("📥 Copyleaks TXT", txt, file_name="copyleaks_report.txt")
    st.download_button("📥 Copyleaks MD", md, file_name="copyleaks_report.md")
    st.download_button("📥 Copyleaks HTML", html, file_name="copyleaks_report.html", mime="text/html")
    st.download_button("📥 Copyleaks PDF", txt, file_name="copyleaks_report.pdf")
    st.download_button("📥 Copyleaks JSON", txt, file_name="copyleaks_report.json")
    st.download_button("📥 Copyleaks JPEG", txt, file_name="copyleaks_report.jpeg")
    st.download_button("📥 Copyleaks JPG", txt, file_name="copyleaks_report.jpg")

    # Save to DB
    save_interview({
        'candidate': st.session_state.cand,
        'jd': st.session_state.jd,
        'questions': st.session_state.questions,
        'ideal': st.session_state.ideal,
        'answers': answers,
        'scores': tfidf_scores,
        'feedback': f"Role: {st.session_state.role}, Type: {st.session_state.qtype}, Mode: {st.session_state.mode}"
    })

    st.success("✅ Interview graded, saved, and Copyleaks checked.")

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
    else:
        st.warning("No interviews available.")

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
                "Scores": r[7] if len(r) > 7 else "",
                "Feedback": r[8] if len(r) > 8 else ""
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
