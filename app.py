import streamlit as st
import fitz  # PyMuPDF
import json
from groq import Groq

st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=Space+Mono&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }
section[data-testid="stSidebar"] { background: #12121a !important; border-right: 1px solid #2a2a3e; }
.hero { text-align: center; padding: 2.5rem 1rem 1.5rem; }
.hero h1 { font-size: 2.8rem; font-weight: 800; color: #e8e8f0; letter-spacing: -0.03em; margin-bottom: 0.4rem; }
.hero h1 span { color: #7c6af7; }
.hero p { color: #6b6b8a; font-family: 'Space Mono', monospace; font-size: 0.85rem; }
.stat-row { display: flex; gap: 12px; margin: 1rem 0; }
.stat-card { flex: 1; background: #12121a; border: 1px solid #2a2a3e; border-radius: 10px; padding: 0.85rem 1rem; text-align: center; }
.stat-num { font-size: 1.4rem; font-weight: 800; color: #7c6af7; font-family: 'Space Mono', monospace; }
.stat-label { font-size: 0.7rem; color: #6b6b8a; margin-top: 2px; }
.chat-msg-user { background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px 12px 4px 12px; padding: 0.85rem 1rem; margin: 0.5rem 0; color: #e8e8f0; font-size: 0.9rem; margin-left: 15%; }
.chat-msg-ai { background: #12121a; border: 1px solid #7c6af744; border-left: 3px solid #7c6af7; border-radius: 4px 12px 12px 12px; padding: 0.85rem 1rem; margin: 0.5rem 0; color: #e8e8f0; font-size: 0.9rem; margin-right: 15%; line-height: 1.7; }
.sender-label { font-size: 0.65rem; font-family: 'Space Mono', monospace; color: #6b6b8a; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.08em; }
.quiz-correct { background: #0f2a1a; border: 1px solid #6af7c8; color: #6af7c8; border-radius: 8px; padding: 0.5rem 0.75rem; font-size: 0.85rem; margin-top: 0.5rem; }
.quiz-wrong { background: #2a0f1a; border: 1px solid #f76a8c; color: #f76a8c; border-radius: 8px; padding: 0.5rem 0.75rem; font-size: 0.85rem; margin-top: 0.5rem; }
.tab-header { font-size: 0.65rem; font-family: 'Space Mono', monospace; color: #6b6b8a; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid #2a2a3e; }
div[data-testid="stButton"] button { background: #7c6af7 !important; color: white !important; border: none !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; font-weight: 600 !important; }
.stTextInput input, .stTextArea textarea { background: #12121a !important; border: 1px solid #2a2a3e !important; color: #e8e8f0 !important; border-radius: 8px !important; }
.block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

for key, val in [("messages", []), ("pdf_text", ""), ("pdf_name", ""), ("quiz", []), ("quiz_answers", {}), ("summary", "")]:
    if key not in st.session_state:
        st.session_state[key] = val


def extract_pdf_text(file) -> str:
    raw = file.read()
    doc = fitz.open(stream=raw, filetype="pdf")
    pages_text = []
    for page in doc:
        blocks = page.get_text("blocks")
        page_content = " ".join(
            b[4].strip() for b in blocks
            if isinstance(b[4], str) and b[4].strip()
        )
        if page_content.strip():
            pages_text.append(page_content.strip())
    full_text = "\n\n".join(pages_text).strip()
    if len(full_text) < 50:
        doc2 = fitz.open(stream=raw, filetype="pdf")
        full_text = "\n".join(p.get_text() for p in doc2).strip()
    return full_text



def chunk_text(text: str, max_chars: int = 5000) -> str:
    if len(text) <= max_chars:
        return text
    front = int(max_chars * 0.6)
    back = max_chars - front
    sep = chr(10) + "..." + chr(10)
    return text[:front] + sep + text[-back:]

def ask_groq(system: str, user: str, history=None) -> str:
    if history is None:
        history = []
    try:
        messages = [{"role": "system", "content": system}]
        for h in history[-4:]:
            messages.append(h)
        messages.append({"role": "user", "content": user})
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ["too large", "tokens", "bad_request", "400"]):
            return "The document is too large to process at once. Try uploading a shorter PDF or a single chapter."
        return f"Error communicating with AI: {str(e)}"


def generate_quiz(text: str, num_q: int = 5) -> list:
    prompt = (
        "Based on this document content, generate exactly "
        + str(num_q)
        + " multiple choice questions.\n\n"
        "Return ONLY a JSON array, nothing else. Format:\n"
        '[{"q":"Question?","options":["A) opt1","B) opt2","C) opt3","D) opt4"],'
        '"answer":"A) opt1","explanation":"Why this is correct."}]\n\n'
        "Document:\n" + chunk_text(text, 5000)
    )
    raw = ask_groq(
        "You are a quiz generator. Return only valid JSON arrays, no markdown, no extra text.",
        prompt
    )
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_summary(text: str) -> str:
    prompt = (
        "Summarize this document clearly. Structure it as:\n"
        "1. Main topic (1 sentence)\n"
        "2. Key concepts covered (bullet points)\n"
        "3. Important takeaways (2-3 sentences)\n\n"
        "Document:\n" + chunk_text(text, 5000)
    )
    return ask_groq("You are a helpful academic summarizer.", prompt)


def quick_ask(question: str):
    if not client:
        st.error("Groq API key not found.")
        return
    st.session_state.messages.append({"role": "user", "content": question})
    sys_prompt = "You are an expert academic tutor.\n\nDocument:\n" + chunk_text(st.session_state.pdf_text, 5000)
    with st.spinner("Thinking..."):
        reply = ask_groq(sys_prompt, question, [])
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ── Sidebar ──────────────────────────────────────────────────────────────────
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
        st.markdown(
            "<div class='stat-row'>"
            "<div class='stat-card'><div class='stat-num'>" + str(f"{words:,}") + "</div><div class='stat-label'>words</div></div>"
            "<div class='stat-card'><div class='stat-num'>~" + str(pages_est) + "</div><div class='stat-label'>pages</div></div>"
            "</div>",
            unsafe_allow_html=True
        )
        st.success("✓ " + uploaded.name)
        st.markdown("---")
        if st.button("Clear & Upload New"):
            st.session_state.pdf_text = ""
            st.session_state.pdf_name = ""
            st.session_state.messages = []
            st.session_state.quiz = []
            st.session_state.quiz_answers = {}
            st.session_state.summary = ""
            st.rerun()
    else:
        st.markdown("<p style='color:#6b6b8a;font-size:0.8rem;text-align:center;padding:2rem 0'>Upload a PDF to get started</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='color:#2a2a3e;font-size:0.7rem;text-align:center;font-family:Space Mono'>powered by Llama 3 via Groq</p>", unsafe_allow_html=True)


# ── Main ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='hero'><h1>AI Study <span>Buddy</span></h1>"
    "<p>// chat with your documents · generate quizzes · get summaries</p></div>",
    unsafe_allow_html=True
)

if not st.session_state.pdf_text:
    st.markdown(
        "<div style='text-align:center;padding:3rem 1rem;'>"
        "<div style='font-size:3rem;margin-bottom:1rem'>📄</div>"
        "<p style='color:#6b6b8a;font-size:1rem;'>Upload a PDF in the sidebar to start studying</p>"
        "<p style='color:#2a2a3e;font-size:0.8rem;font-family:Space Mono;margin-top:0.5rem'>textbooks · notes · research papers · anything</p>"
        "</div>",
        unsafe_allow_html=True
    )
    st.stop()

tab1, tab2, tab3 = st.tabs(["💬  Chat", "🧠  Quiz Me", "📋  Summary"])

# ── Chat ──────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<div class='tab-header'>ask anything about your document</div>", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                "<div class='sender-label'>you</div><div class='chat-msg-user'>" + msg["content"] + "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='sender-label'>study buddy</div><div class='chat-msg-ai'>" + msg["content"] + "</div>",
                unsafe_allow_html=True
            )

    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask a question...",
                placeholder="e.g. Explain gradient descent in simple terms",
                label_visibility="collapsed"
            )
        with col2:
            submitted = st.form_submit_button("Send →")

    if submitted and user_input.strip():
        if not client:
            st.error("Groq API key not found.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            sys_prompt = (
                "You are an expert academic tutor. Answer questions based on the document. "
                "If the answer is not in the document, say so.\n\nDocument:\n"
                + chunk_text(st.session_state.pdf_text, 5000)
            )
            with st.spinner("Thinking..."):
                reply = ask_groq(sys_prompt, user_input, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    st.markdown("<p style='color:#6b6b8a;font-size:0.72rem;font-family:Space Mono;margin-top:1rem'>quick prompts:</p>", unsafe_allow_html=True)
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        if st.button("What is this doc about?"):
            quick_ask("What is this document about? Give me a brief overview.")
    with qc2:
        if st.button("List key concepts"):
            quick_ask("List all the key concepts covered in this document.")
    with qc3:
        if st.button("Explain the hardest part"):
            quick_ask("What is the most complex topic in this document? Explain it simply.")

# ── Quiz ──────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div class='tab-header'>test your understanding</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        num_q = st.slider("Number of questions", 3, 10, 5)
    with col2:
        gen_btn = st.button("Generate Quiz", use_container_width=True)

    if gen_btn:
        if not client:
            st.error("Groq API key not found.")
        else:
            with st.spinner("Generating quiz questions..."):
                try:
                    st.session_state.quiz = generate_quiz(st.session_state.pdf_text, num_q)
                    st.session_state.quiz_answers = {}
                except Exception as e:
                    st.error("Couldn't generate quiz. Try again. (" + str(e) + ")")

    if st.session_state.quiz:
        for i, q in enumerate(st.session_state.quiz):
            st.markdown(
                "<div style='background:#12121a;border:1px solid #2a2a3e;border-radius:12px;padding:1.25rem;margin-bottom:1rem'>"
                "<div style='font-size:0.95rem;font-weight:600;color:#e8e8f0;margin-bottom:0.75rem'>Q" + str(i+1) + ". " + q["q"] + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            choice = st.radio("q" + str(i+1), q["options"], key="quiz_" + str(i), label_visibility="collapsed")
            st.session_state.quiz_answers[i] = choice
            if st.button("Check answer", key="check_" + str(i)):
                if choice == q["answer"]:
                    st.markdown("<div class='quiz-correct'>Correct! " + q["explanation"] + "</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='quiz-wrong'>Incorrect. Correct: " + q["answer"] + " — " + q["explanation"] + "</div>", unsafe_allow_html=True)

# ── Summary ───────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='tab-header'>document summary</div>", unsafe_allow_html=True)

    if not st.session_state.summary:
        if st.button("Generate Summary"):
            if not client:
                st.error("Groq API key not found.")
            else:
                with st.spinner("Summarizing your document..."):
                    st.session_state.summary = generate_summary(st.session_state.pdf_text)
                st.rerun()
    else:
        st.markdown("<div class='chat-msg-ai'>" + st.session_state.summary + "</div>", unsafe_allow_html=True)
        if st.button("Regenerate"):
            st.session_state.summary = ""
            st.rerun()
