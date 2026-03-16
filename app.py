import streamlit as st
import fitz  # PyMuPDF
import os
import json
import textwrap
from groq import Groq

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=Space+Mono&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.stApp { background: #0a0a0f; color: #e8e8f0; }

section[data-testid="stSidebar"] {
    background: #12121a !important;
    border-right: 1px solid #2a2a3e;
}

.hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}
.hero h1 {
    font-size: 2.8rem;
    font-weight: 800;
    color: #e8e8f0;
    letter-spacing: -0.03em;
    margin-bottom: 0.4rem;
}
.hero h1 span { color: #7c6af7; }
.hero p {
    color: #6b6b8a;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
}

.stat-row {
    display: flex;
    gap: 12px;
    margin: 1rem 0;
}
.stat-card {
    flex: 1;
    background: #12121a;
    border: 1px solid #2a2a3e;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    text-align: center;
}
.stat-num {
    font-size: 1.4rem;
    font-weight: 800;
    color: #7c6af7;
    font-family: 'Space Mono', monospace;
}
.stat-label {
    font-size: 0.7rem;
    color: #6b6b8a;
    margin-top: 2px;
}

.chat-msg-user {
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 12px 12px 4px 12px;
    padding: 0.85rem 1rem;
    margin: 0.5rem 0;
    color: #e8e8f0;
    font-size: 0.9rem;
    margin-left: 15%;
}
.chat-msg-ai {
    background: #12121a;
    border: 1px solid #7c6af744;
    border-left: 3px solid #7c6af7;
    border-radius: 4px 12px 12px 12px;
    padding: 0.85rem 1rem;
    margin: 0.5rem 0;
    color: #e8e8f0;
    font-size: 0.9rem;
    margin-right: 15%;
    line-height: 1.7;
}
.sender-label {
    font-size: 0.65rem;
    font-family: 'Space Mono', monospace;
    color: #6b6b8a;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.quiz-card {
    background: #12121a;
    border: 1px solid #2a2a3e;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}
.quiz-q {
    font-size: 0.95rem;
    font-weight: 600;
    color: #e8e8f0;
    margin-bottom: 0.75rem;
}
.quiz-correct {
    background: #0f2a1a;
    border: 1px solid #6af7c8;
    color: #6af7c8;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.quiz-wrong {
    background: #2a0f1a;
    border: 1px solid #f76a8c;
    color: #f76a8c;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

.tab-header {
    font-size: 0.65rem;
    font-family: 'Space Mono', monospace;
    color: #6b6b8a;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #2a2a3e;
}

div[data-testid="stButton"] button {
    background: #7c6af7 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
}
div[data-testid="stButton"] button:hover {
    background: #6557d4 !important;
}

.stTextInput input, .stTextArea textarea {
    background: #12121a !important;
    border: 1px solid #2a2a3e !important;
    color: #e8e8f0 !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #7c6af7 !important;
    box-shadow: 0 0 0 2px #7c6af722 !important;
}

.stFileUploader {
    background: #12121a !important;
    border: 2px dashed #2a2a3e !important;
    border-radius: 12px !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    color: #7c6af7 !important;
}

.stSpinner > div { border-top-color: #7c6af7 !important; }

hr { border-color: #2a2a3e !important; }

.block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Groq client ────────────────────────────────────────────────────────────────
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "summary" not in st.session_state:
    st.session_state.summary = ""

# ── Helpers ────────────────────────────────────────────────────────────────────
def extract_pdf_text(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def chunk_text(text: str, max_chars: int = 6000) -> str:
    """Return a relevant context slice — keep it under token limits."""
    return text[:max_chars]

def ask_groq(system: str, user: str, history: list = []) -> str:
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:  # last 3 turns
        messages.append(h)
    messages.append({"role": "user", "content": user})
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages,
        max_tokens=1024,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_quiz(text: str, num_q: int = 5) -> list:
    prompt = f"""Based on this document content, generate exactly {num_q} multiple choice questions.

Return ONLY a JSON array in this exact format, nothing else:
[
  {{
    "q": "Question text here?",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "answer": "A) option1",
    "explanation": "Brief explanation why this is correct."
  }}
]

Document content:
{chunk_text(text, 4000)}"""

    raw = ask_groq("You are a quiz generator. Return only valid JSON arrays, no markdown, no explanation.", prompt)
    # clean markdown fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)

def generate_summary(text: str) -> str:
    prompt = f"""Summarize this document clearly and concisely. Structure your summary with:
1. Main topic (1 sentence)
2. Key concepts covered (bullet points)
3. Important takeaways (2-3 sentences)

Document:
{chunk_text(text, 5000)}"""
    return ask_groq("You are a helpful academic summarizer.", prompt)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 AI Study Buddy")
    st.markdown("<p style='color:#6b6b8a;font-size:0.75rem;font-family:Space Mono'>// upload your document</p>", unsafe_allow_html=True)
    st.markdown("---")

    uploaded = st.file_uploader("Drop a PDF here", type=["pdf"], label_visibility="collapsed")

    if uploaded:
        if uploaded.name != st.session_state.pdf_name:
            with st.spinner("Reading PDF..."):
                st.session_state.pdf_text = extract_pdf_text(uploaded)
                st.session_state.pdf_name = uploaded.name
                st.session_state.messages = []
                st.session_state.quiz = []
                st.session_state.summary = ""

        words = len(st.session_state.pdf_text.split())
        pages_est = max(1, words // 250)

        st.markdown(f"""
        <div class='stat-row'>
            <div class='stat-card'>
                <div class='stat-num'>{words:,}</div>
                <div class='stat-label'>words</div>
            </div>
            <div class='stat-card'>
                <div class='stat-num'>~{pages_est}</div>
                <div class='stat-label'>pages</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.success(f"✓ {uploaded.name}")

        st.markdown("---")
        if st.button("🗑 Clear & Upload New"):
            st.session_state.pdf_text = ""
            st.session_state.pdf_name = ""
            st.session_state.messages = []
            st.session_state.quiz = []
            st.session_state.summary = ""
            st.rerun()
    else:
        st.markdown("<p style='color:#6b6b8a;font-size:0.8rem;text-align:center;padding:2rem 0'>Upload a PDF to get started</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='color:#2a2a3e;font-size:0.7rem;text-align:center;font-family:Space Mono'>powered by Llama 3 via Groq</p>", unsafe_allow_html=True)

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero'>
    <h1>AI Study <span>Buddy</span></h1>
    <p>// chat with your documents · generate quizzes · get summaries</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.pdf_text:
    st.markdown("""
    <div style='text-align:center;padding:3rem 1rem;'>
        <div style='font-size:3rem;margin-bottom:1rem'>📄</div>
        <p style='color:#6b6b8a;font-size:1rem;'>Upload a PDF in the sidebar to start studying</p>
        <p style='color:#2a2a3e;font-size:0.8rem;font-family:Space Mono;margin-top:0.5rem'>textbooks · notes · research papers · anything</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💬  Chat", "🧠  Quiz Me", "📋  Summary"])

# ── TAB 1: CHAT ────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<div class='tab-header'>ask anything about your document</div>", unsafe_allow_html=True)

    # display history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='sender-label'>you</div><div class='chat-msg-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='sender-label'>study buddy</div><div class='chat-msg-ai'>{msg['content']}</div>", unsafe_allow_html=True)

    # input
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Ask a question...", placeholder="e.g. Explain gradient descent in simple terms", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Send →")

    if submitted and user_input.strip():
        if not client:
            st.error("Groq API key not found. Add it to Streamlit secrets.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            system_prompt = f"""You are an expert academic tutor helping a student understand a document.
Answer questions clearly, use examples when helpful, and always base your answers on the document content.
If the answer isn't in the document, say so honestly.

Document content:
{chunk_text(st.session_state.pdf_text)}"""
            with st.spinner("Thinking..."):
                reply = ask_groq(system_prompt, user_input, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    # quick prompts
    st.markdown("<div style='margin-top:1rem'>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6b6b8a;font-size:0.72rem;font-family:Space Mono'>quick prompts:</p>", unsafe_allow_html=True)
    qcol1, qcol2, qcol3 = st.columns(3)
    with qcol1:
        if st.button("What is this doc about?"):
            st.session_state.messages.append({"role": "user", "content": "What is this document about? Give me a brief overview."})
            system_prompt = f"You are an expert academic tutor.\n\nDocument:\n{chunk_text(st.session_state.pdf_text)}"
            with st.spinner("Thinking..."):
                reply = ask_groq(system_prompt, "What is this document about? Give me a brief overview.", [])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qcol2:
        if st.button("List key concepts"):
            st.session_state.messages.append({"role": "user", "content": "List all the key concepts covered in this document."})
            system_prompt = f"You are an expert academic tutor.\n\nDocument:\n{chunk_text(st.session_state.pdf_text)}"
            with st.spinner("Thinking..."):
                reply = ask_groq(system_prompt, "List all the key concepts covered in this document.", [])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with qcol3:
        if st.button("Explain the hardest part"):
            st.session_state.messages.append({"role": "user", "content": "What's the most complex topic in this document? Explain it simply."})
            system_prompt = f"You are an expert academic tutor.\n\nDocument:\n{chunk_text(st.session_state.pdf_text)}"
            with st.spinner("Thinking..."):
                reply = ask_groq(system_prompt, "What's the most complex topic in this document? Explain it simply.", [])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

# ── TAB 2: QUIZ ────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div class='tab-header'>test your understanding</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        num_q = st.slider("Number of questions", 3, 10, 5)
    with col2:
        gen_btn = st.button("Generate Quiz ✨", use_container_width=True)

    if gen_btn:
        if not client:
            st.error("Groq API key not found.")
        else:
            with st.spinner("Generating quiz questions..."):
                try:
                    st.session_state.quiz = generate_quiz(st.session_state.pdf_text, num_q)
                    st.session_state.quiz_answers = {}
                except Exception as e:
                    st.error(f"Couldn't generate quiz. Try again. ({e})")

    if st.session_state.quiz:
        score = 0
        total = len(st.session_state.quiz)

        for i, q in enumerate(st.session_state.quiz):
            st.markdown(f"<div class='quiz-card'><div class='quiz-q'>Q{i+1}. {q['q']}</div></div>", unsafe_allow_html=True)
            choice = st.radio(
                f"q{i+1}",
                q["options"],
                key=f"quiz_{i}",
                label_visibility="collapsed"
            )
            st.session_state.quiz_answers[i] = choice

            if st.button(f"Check answer", key=f"check_{i}"):
                if choice == q["answer"]:
                    st.markdown(f"<div class='quiz-correct'>✓ Correct! {q['explanation']}</div>", unsafe_allow_html=True)
                    score += 1
                else:
                    st.markdown(f"<div class='quiz-wrong'>✗ Incorrect. Correct answer: {q['answer']}<br>{q['explanation']}</div>", unsafe_allow_html=True)

# ── TAB 3: SUMMARY ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='tab-header'>document summary</div>", unsafe_allow_html=True)

    if not st.session_state.summary:
        if st.button("Generate Summary 📋", use_container_width=False):
            if not client:
                st.error("Groq API key not found.")
            else:
                with st.spinner("Summarizing your document..."):
                    st.session_state.summary = generate_summary(st.session_state.pdf_text)
                st.rerun()
    else:
        st.markdown(f"<div class='chat-msg-ai'>{st.session_state.summary}</div>", unsafe_allow_html=True)
        if st.button("Regenerate"):
            st.session_state.summary = ""
            st.rerun()
