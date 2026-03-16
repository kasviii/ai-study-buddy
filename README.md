# AI Study Buddy 📚

An AI-powered study assistant that lets you chat with any PDF, generate quizzes, and get instant summaries — built with Llama 3 (via Groq) and Streamlit.

## Live Demo
[Coming soon — deploy link here]

## Features
- **Chat with your PDF** — ask any question, get answers grounded in your document
- **Auto Quiz Generation** — generates multiple choice questions from your content
- **Smart Summary** — structured summary with key concepts and takeaways
- **Quick Prompts** — one-click questions to get started instantly

## How to Use
1. Upload any PDF (textbook, notes, research paper)
2. Use the Chat tab to ask questions
3. Use Quiz Me to test yourself
4. Use Summary for a quick overview

## Tech Stack
- Python + Streamlit
- Groq API (Llama 3 8B) — free tier
- PyMuPDF for PDF parsing
- Deployed on Streamlit Cloud

## Local Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```
Add your Groq API key in `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_key_here"
```

## Course Details
- Course: CSE3201 — Machine Learning
- Program: B.Tech CSE, Semester VI
- Institution: Manipal University Jaipur
- Session: Jan–May 2026
