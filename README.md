# 🎯 Job Application Optimizer

CrewAI-powered multi-agent pipeline that tailors your resume to any job posting,
generates targeted interview questions, and creates STAR talking points.
**100 % free** — powered by Groq Llama 3.3 + Google Gemini. No OpenAI required.

---

## ✨ What It Does

| Output | Description |
|--------|-------------|
| 📄 **Optimised Resume** | Your resume rewritten to match the job's ATS keywords and priorities |
| 🧭 **Skill & Project Gaps** | Good-to-have skills you lack plus higher-weightage project ideas |
| ❓ **Interview Questions** | 10 role-specific questions with why-they-ask and how-to-answer tips |
| 💡 **STAR Talking Points** | Situation / Task / Action / Result for your top 3 experiences |
| 🔍 **Job Analysis** | Skills breakdown — must-have vs. nice-to-have, ATS keywords |

---

## 🛠️ Tech Stack

| Component | Library / Service |
|-----------|------------------|
| AI orchestration | CrewAI sequential agents |
| Fast LLM (free) | [Groq](https://console.groq.com) — `llama-3.3-70b-versatile` |
| Smart LLM (free) | [Google Gemini Flash](https://ai.google.dev) — `gemini-2.0-flash` |
| RAG embeddings | Google `embedding-001` + FAISS |
| Web UI | [Streamlit](https://streamlit.io) |

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd job-application-optimizer
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get your free API keys

**Groq** (fast Llama inference)
```
https://console.groq.com  →  Sign up  →  API Keys  →  Create
```

**Google AI** (Gemini Flash)
```
https://ai.google.dev  →  Get API Key in Google AI Studio  →  Create API Key
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and paste your keys
```

Or use the **🔑 API Setup** page in the app — it writes `.env` for you.

### 4. Run

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## 📁 Project Structure

```
job-application-optimizer/
├── app.py                    # Streamlit UI — single-file, all pages
├── core/
│   ├── __init__.py
│   └── crew_manager.py       # CrewAI agent orchestration
├── utils/
│   ├── __init__.py
│   ├── rag_processor.py      # FAISS + Google Embeddings RAG
│   └── helpers.py            # PDF/URL parsing, skill extraction
├── .streamlit/
│   └── config.toml           # Theme & server settings
├── requirements.txt
├── .env.example              # Copy to .env and fill keys
└── README.md
```

---

## 🤖 Pipeline Design

```
┌─────────────────────────────────────────────────────┐
│  Input: resume + job JD/URL                         │
└──────────────────────┬──────────────────────────────┘
                       │  RAG pre-processing (FAISS)
           ┌───────────▼───────────┐
           │   Job Analyzer        │  Groq Llama 3.3
           │   (extracts JD)       │
           └───────────┬───────────┘
           ┌───────────▼───────────┐
           │   Profile Generator   │  Google Gemini
           │   (builds profile)    │
           └───────────┬───────────┘
           ┌───────────▼───────────┐
           │   Resume Optimizer    │  Groq Llama 3.3
           │   (tailors resume)    │
           └───────────┬───────────┘
           ┌───────────▼───────────┐
           │ Skill & Project Advisor│ Google Gemini
           │ (gaps + project tips)  │
           └───────────┬───────────┘
           ┌───────────▼───────────┐
           │   Interview Coach     │  Google Gemini
           │   (Qs + talking pts)  │
           └───────────┬───────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Output: resume · gaps · projects · interview prep  │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

All settings live in `.env`:

```dotenv
GROQ_API_KEY=gsk_...           # Required
GOOGLE_API_KEY=AIza...         # Required
```

Advanced settings (in the app UI):

| Setting | Default | Effect |
|---------|---------|--------|
| Temperature | 0.7 | Lower = focused, higher = creative |
| RAG | Always on | Improves context quality |

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `GROQ_API_KEY not found` | Check `.env` exists in project root |
| `google.api_core.exceptions.InvalidArgument` | Verify `GOOGLE_API_KEY` is correct |
| Processing hangs > 10 min | Shorten inputs; disable RAG; try again |
| FAISS import error | `pip install faiss-cpu --upgrade` |
| Poor output quality | Add more detail to JD; increase temperature |
| PDF text garbled | Paste text manually instead |

---

## 📜 Licence

MIT — use freely, modify, redistribute.

---

## 🙏 Credits

- [Groq](https://groq.com) — free ultra-fast inference
- [Google AI](https://ai.google.dev) — free Gemini API
