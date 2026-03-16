# AI Study Buddy 📚

An AI-powered study assistant that lets you chat with any PDF, generate quizzes, and get instant summaries — powered by Llama 3 (via Groq) and built with Python + Streamlit.

## Live Demo
[https://ai-study-buddy-kasvii.streamlit.app/](https://ai-study-buddy-kasvii.streamlit.app/)

---

## What This Project Does

AI Study Buddy implements **Retrieval-Augmented Generation (RAG)** — a technique where instead of relying on an AI's pre-trained knowledge alone, you supply your own document as context and the model answers strictly from that. This makes responses accurate, grounded, and document-specific.

The app has three core features:
- **Chat** — ask any question about your uploaded PDF and get answers grounded in the document
- **Quiz Me** — auto-generates multiple choice questions from the document content to test understanding
- **Summary** — produces a structured summary with key concepts and takeaways

---

## How It Works (Technical Flow)

### 1. PDF Text Extraction — `PyMuPDF (fitz)`
When a user uploads a PDF, the app uses PyMuPDF to extract raw text page by page. Slide-based PDFs (like lecture decks) store text in "blocks" rather than continuous paragraphs, so the app uses block-level extraction (`page.get_text("blocks")`) to handle both regular documents and presentation slides correctly.

### 2. Chunking
Large documents cannot be sent to the model all at once due to token limits. The app uses a smart chunking strategy: for documents exceeding 5000 characters, it takes the **first 60% + last 40%** of the text. This preserves both the introduction (definitions, context) and the conclusion (key takeaways), which are typically the most information-dense parts of any academic document.

### 3. LLM Inference — `Groq API + Llama 3`
The extracted and chunked text is injected into a **system prompt** — a set of instructions given to the model before the user's question. The system prompt tells the model:
- Here is the document content
- Answer only from this document
- If the answer is not here, say so

This is sent to **Llama 3** (an open-source LLM by Meta) running on Groq's infrastructure. Groq uses custom LPU (Language Processing Unit) chips that make inference significantly faster than standard GPU-based APIs.

### 4. Conversation Memory
The app maintains chat history in `st.session_state` — Streamlit's way of persisting data across reruns. Each time the user sends a message, the last 4 messages of history are included in the API call, giving the model conversational context.

### 5. Quiz Generation (Structured Output)
For quiz generation, the model is prompted to return a **strict JSON format** — a list of objects each containing a question, four options, the correct answer, and an explanation. Python then parses this JSON and renders it as interactive radio buttons using Streamlit widgets.

### 6. Web Interface — `Streamlit`
Streamlit converts a plain Python script into a fully interactive web app. Every user interaction (button click, form submit) triggers a full rerun of the script from top to bottom — which is why `st.session_state` is essential to preserve chat history, quiz data, and summaries between interactions.

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend + Backend | Streamlit | Web interface and app logic |
| PDF Parsing | PyMuPDF (fitz) | Extract text from uploaded PDFs |
| LLM | Llama 3 (Meta) | Natural language understanding and generation |
| LLM API | Groq | Fast, free inference API for Llama 3 |
| Language | Python 3.11 | Core programming language |
| Deployment | Streamlit Cloud | Free cloud hosting |

---

## ML / NLP Concepts Demonstrated

- **Large Language Models (LLMs)** — using a pre-trained transformer model (Llama 3) for text generation and comprehension
- **Retrieval-Augmented Generation (RAG)** — grounding LLM responses in a specific external document
- **Prompt Engineering** — structuring system prompts to control model behaviour and output format
- **Structured Output Parsing** — instructing an LLM to return JSON and parsing it programmatically
- **Context Window Management** — chunking text intelligently to stay within token limits
- **Embeddings & Representations** — conceptual foundation of how the LLM understands document content (covered in CSE3201 Unit 5)

---

## Project Structure

```
ai-study-buddy/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```


## For me

> An end-to-end NLP application implementing retrieval-augmented generation — extracting and chunking text from PDF documents, injecting it as context into a large language model via API, and building a conversational interface with auto-generated assessments on top.
> Work on it (proper rag and vector embeddings and maybe add a feature so it can host multiple languages, and even a youtube video summarizer)
