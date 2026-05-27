"""
Job Application Optimizer - Complete Streamlit Application
Powered by Groq + Google AI (100% Free)
"""

import streamlit as st
import os
import json
import re
from datetime import datetime
from pathlib import Path

from config import GEMINI_MODEL, GROQ_MODEL
from utils.asyncio_compat import ensure_event_loop
from utils.job_url_scraper import scrape_job_url


# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Application Optimizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0');

    :root {
        --ink: #17133f;
        --muted: #64748b;
        --brand: #6557ff;
        --brand-2: #10b981;
        --line: #e5e7eb;
        --panel: #f8fafc;
    }

    /* Sidebar - Strictly scoped so it doesn't leak into main containers */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #211b56 0%, #312f7e 100%); 
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] code { 
        color: #f8fafc !important; 
    }
    [data-testid="stSidebar"] .stButton>button {
        background: #ffffff;
        border: 1px solid rgba(255,255,255,.35);
        color: #20184f !important;
        box-shadow: 0 8px 22px rgba(9,7,40,.16);
    }
    [data-testid="stSidebar"] .stButton>button p {
        color: #20184f !important;
        font-weight: 700;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: #eef2ff;
        border-color: #a5b4fc;
    }
    [data-testid="stSidebar"] hr { 
        border-color: rgba(255,255,255,.18); 
    }

    /* Cards & Main Content Surfaces */
    .card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,.08);
        margin-bottom: 1rem;
        border-left: 4px solid #6C63FF;
    }
    .card-green  { border-left-color: #10b981; }
    .card-orange { border-left-color: #f59e0b; }
    .card-red    { border-left-color: #ef4444; }
    
    .surface {
        background: #ffffff !important;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 1px 10px rgba(15,23,42,.05);
        min-height: 100%;
    }
    
    /* Explicitly forcing legible dark text for content cards on main panel */
    .surface h3 { 
        margin-top: 0; 
        color: var(--ink) !important; 
    }
    .surface p { 
        color: var(--muted) !important; 
    }
    
    .model-chip {
        display: flex;
        align-items: center;
        gap: .55rem;
        background: rgba(255,255,255,.10);
        border: 1px solid rgba(255,255,255,.20);
        border-radius: 8px;
        padding: .65rem .75rem;
        margin: .55rem 0;
    }
    .model-dot {
        width: 12px;
        height: 12px;
        border-radius: 99px;
        flex: 0 0 auto;
        box-shadow: 0 0 0 4px rgba(255,255,255,.08);
    }
    .dot-groq { background: #a78bfa; }
    .dot-gemini { background: #38bdf8; }
    .model-chip strong,
    .model-chip span { color: #f8fafc !important; }
    .model-chip span {
        display: block;
        font-size: .78rem;
        color: #c7d2fe !important;
        margin-top: .1rem;
    }
    
    /* Layout Flow & Grids */
    .flow {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: .65rem;
        align-items: stretch;
        margin: 1rem 0;
    }
    .flow-node {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: .85rem;
        min-height: 105px;
    }
    .flow-node strong {
        display: block;
        color: var(--ink);
        margin: .25rem 0;
    }
    .flow-node span {
        color: var(--muted);
        font-size: .86rem;
        line-height: 1.35;
    }
    .flow-node .material-symbols-rounded { color: var(--brand); }
    
    .agent-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: .7rem;
        margin-top: .8rem;
    }
    .agent-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: .85rem;
    }
    .agent-card strong {
        display: block;
        color: var(--ink);
        margin: .25rem 0;
    }
    .agent-card small {
        color: var(--brand);
        font-weight: 800;
    }
    .agent-card p {
        color: var(--muted);
        font-size: .86rem;
        line-height: 1.35;
        margin: .35rem 0 0;
    }
    
    .api-card {
        background: #ffffff !important;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem 1.15rem;
        min-height: 100%;
        box-shadow: 0 1px 8px rgba(15,23,42,.04);
    }

    .api-card h3 {
        display: flex;
        align-items: center;
        gap: .45rem;
        margin-top: 0;
        color: var(--ink) !important;
        font-weight: 800 !important;
    }

    .api-card .api-note {
        color: var(--muted) !important;
        font-size: .9rem;
        margin: .2rem 0 .8rem;
    }
    .api-card .api-note strong {
        color: var(--ink) !important;
    }
    
    @media (max-width: 900px) {
        .flow, .agent-grid { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 560px) {
        .flow, .agent-grid { grid-template-columns: 1fr; }
    }

    /* Badges & Stepper Styling */
    .badge {
        display: inline-block;
        padding: .2rem .7rem;
        border-radius: 999px;
        font-size: .78rem;
        font-weight: 600;
        margin: .15rem;
    }
    .badge-purple { background: #ede9fe; color: #6d28d9; }
    .badge-green  { background: #d1fae5; color: #065f46; }
    .badge-orange { background: #fef3c7; color: #92400e; }

    .step-active   { color: #6C63FF; font-weight: 700; }
    .step-complete { color: #10b981; font-weight: 700; }
    .step-pending  { color: #9ca3af; }

    .agent-log {
        background: #0f172a;
        color: #94a3b8;
        font-family: monospace;
        font-size: .8rem;
        padding: 1rem;
        border-radius: 8px;
        max-height: 300px;
        overflow-y: auto;
        white-space: pre-wrap;
    }

    .output-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
    }
    .stage-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem 1.15rem;
        margin: .75rem 0 1.25rem;
        box-shadow: 0 1px 8px rgba(15,23,42,.04);
    }
    .stage-title {
        display: flex;
        align-items: center;
        gap: .5rem;
        margin: .35rem 0 .65rem;
        color: var(--ink);
        font-weight: 800;
        font-size: 1.05rem;
    }
    .stage-caption {
        color: var(--muted);
        font-size: .82rem;
        margin: -.3rem 0 .65rem;
    }
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        font-size: 1.25rem;
        line-height: 1;
        display: inline-block;
        color: var(--brand);
    }
    .small-credit {
        color: #64748b;
        font-size: .78rem;
        text-align: right;
        margin-top: 1.2rem;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6C63FF, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }

    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    div[data-testid="metric-container"] {
        background: #f1f5f9;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State ───────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "home",
        "resume_text": "",
        "job_text": "",
        "job_role": "",
        "results": None,
        "processing": False,
        "logs": [],
        "stats": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def icon(name: str) -> str:
    return f'<span class="material-symbols-rounded">{name}</span>'

def clean_display_markdown(content: str) -> str:
    text = (content or "").strip()
    fence = re.match(r"^```(?:markdown|md)?\s*(.*?)\s*```$", text, flags=re.S | re.I)
    return fence.group(1).strip() if fence else text

# ─── Sidebar Navigation ──────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"## {icon('track_changes')} Job Optimizer", unsafe_allow_html=True)
        st.markdown("---")

        pages = {
            "🏠 Home":      "home",
            "📝 Inputs":    "input",
            "⚙️ Process":   "process",
            "📊 Results":   "results",
            "🔑 API Setup": "setup",
        }
        for label, key in pages.items():
            active = st.session_state.page == key
            style = "color:#a5b4fc;font-weight:700;" if active else ""
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")

        # Quick status
        status_items = {
            "Resume":   bool(st.session_state.resume_text),
            "Job":      bool(st.session_state.job_text),
            "Results":  st.session_state.results is not None,
        }
        st.markdown(f"#### {icon('task_alt')} Progress", unsafe_allow_html=True)
        for label, done in status_items.items():
            mark = "check_circle" if done else "radio_button_unchecked"
            st.markdown(f"{icon(mark)} {label}", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Model Stack")
        st.markdown(
            f"""
<div class="model-chip">
  <div class="model-dot dot-groq"></div>
  <div><strong>Groq</strong><span>{GROQ_MODEL}</span></div>
</div>
<div class="model-chip">
  <div class="model-dot dot-gemini"></div>
  <div><strong>Google Gemini</strong><span>{GEMINI_MODEL}</span></div>
</div>
""",
            unsafe_allow_html=True,
        )

sidebar()

# ─── Helpers ────────────────────────────────────────────────────────────────────
def nav(page: str):
    st.session_state.page = page
    st.rerun()

def read_pdf(file) -> str:
    """Extract text from uploaded PDF."""
    import io
    from pypdf import PdfReader          # pypdf — pure Python, no compiler needed
    reader = PdfReader(io.BytesIO(file.read()))
    return "\n".join(p.extract_text() or "" for p in reader.pages)

def render_output_panel(content: str, empty: str = "_No output generated yet._"):
    with st.container(border=True):
        st.markdown(clean_display_markdown(content) or empty)

def read_env_values() -> dict[str, str]:
    env_path = Path(".env")
    values = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values

def save_env_values(updates: dict[str, str]) -> list[str]:
    existing = read_env_values()
    saved = []
    for key, value in updates.items():
        if value:
            existing[key] = value
            os.environ[key] = value
            saved.append(key)
    if saved:
        Path(".env").write_text(
            "\n".join(f"{key}={value}" for key, value in existing.items()) + "\n"
        )
    return saved

def short_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return exc.__class__.__name__
    text = re.sub(r"\s+", " ", text)
    return text[:700] + ("..." if len(text) > 700 else "")

# ─── PAGE: HOME ─────────────────────────────────────────────────────────────────
def page_home():
    st.markdown('<p class="hero-title">Job Application Optimizer</p>', unsafe_allow_html=True)
    st.markdown("#### Multi-agent resume tailoring, skill-gap guidance, and interview preparation")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<div class="surface">
<h3>{icon('groups')} CrewAI Agents</h3>
<p>Five specialist agents run in sequence, each focused on one decision: job analysis, profile, resume, advice, or interview prep.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="surface">
<h3>{icon('hub')} Model Routing</h3>
<p>Groq handles fast analysis and resume writing. Gemini handles profile synthesis, strategy, and coaching output.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="surface">
<h3>{icon('database_search')} RAG Context</h3>
<p>FAISS retrieval condenses long resumes and job descriptions into focused context before the crew starts.</p>
</div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Project Pipeline")
    st.markdown(
        f"""
<div class="flow">
  <div class="flow-node">{icon('upload_file')}<strong>Inputs</strong><span>Resume file/text plus job description or URL.</span></div>
  <div class="flow-node">{icon('segment')}<strong>RAG Chunking</strong><span>Resume and JD are split into searchable context blocks.</span></div>
  <div class="flow-node">{icon('database')}<strong>FAISS Retrieval</strong><span>Relevant snippets are selected for the agents.</span></div>
  <div class="flow-node">{icon('groups')}<strong>CrewAI Tasks</strong><span>Agents execute one task at a time with shared context.</span></div>
  <div class="flow-node">{icon('fact_check')}<strong>Live Outputs</strong><span>Each completed stage appears immediately on Process.</span></div>
  <div class="flow-node">{icon('download')}<strong>Package</strong><span>Optimised resume, gaps, questions, and STAR notes.</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### Agents, Tasks, And Crew Summary")
    st.markdown(
        f"""
<div class="agent-grid">
  <div class="agent-card">{icon('travel_explore')}<strong>Job Analyzer</strong><small>Groq</small><p>Extracts skills, responsibilities, ATS keywords, and culture signals.</p></div>
  <div class="agent-card">{icon('person_search')}<strong>Profile Generator</strong><small>Gemini</small><p>Builds an evidence-based candidate profile from resume context.</p></div>
  <div class="agent-card">{icon('description')}<strong>Resume Optimizer</strong><small>Groq</small><p>Creates a targeted Markdown resume without inventing facts.</p></div>
  <div class="agent-card">{icon('route')}<strong>Skill Advisor</strong><small>Gemini</small><p>Identifies good-to-have gaps and stronger project directions.</p></div>
  <div class="agent-card">{icon('record_voice_over')}<strong>Interview Coach</strong><small>Gemini</small><p>Generates questions, STAR talking points, and review topics.</p></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    if st.button("Start Application Review", use_container_width=True, type="primary"):
        nav("input")


# ─── PAGE: INPUT ────────────────────────────────────────────────────────────────
def page_input():
    st.title("📝 Your Information")

    # ── Resume ──────────────────────────────────────────────────────────────────
    st.subheader("1. Resume")
    resume_method = st.radio("How would you like to provide your resume?",
                             ["📁 Upload file (PDF / TXT / MD)", "✏️ Paste text"],
                             horizontal=True)

    if resume_method == "📁 Upload file (PDF / TXT / MD)":
        file = st.file_uploader("Upload resume", type=["pdf", "txt", "md"], label_visibility="collapsed")
        if file:
            if file.name.endswith(".pdf"):
                text = read_pdf(file)
            else:
                text = file.read().decode("utf-8", errors="ignore")
            st.session_state.resume_text = text
            st.success(f"✅ Resume loaded — {len(text):,} characters")
            with st.expander("Preview"):
                st.text(text[:800] + ("…" if len(text) > 800 else ""))
    else:
        text = st.text_area("Paste your resume here:", height=250,
                            value=st.session_state.resume_text,
                            placeholder="John Doe\n\nExperience\n...\nSkills\n...")
        st.session_state.resume_text = text

    st.markdown("---")

    # ── Job Description ──────────────────────────────────────────────────────────
    st.subheader("2. Job Description")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.job_role = st.text_input(
            "Job Role / Title",
            value=st.session_state.job_role,
            placeholder="e.g. Senior Backend Engineer"
        )

    jd_tab1, jd_tab2, jd_tab3 = st.tabs(["✏️ Paste text", "📁 Upload TXT", "🔗 Extract from URL"])

    with jd_tab1:
        jd_text = st.text_area("Paste the job description:", height=220,
                               value=st.session_state.job_text,
                               placeholder="Requirements\nResponsibilities\n...")
        st.session_state.job_text = jd_text

    with jd_tab2:
        jd_file = st.file_uploader("Upload job description", type=["txt", "md"], label_visibility="collapsed")
        if jd_file:
            text = jd_file.read().decode("utf-8", errors="ignore")
            st.session_state.job_text = text
            st.success(f"✅ Job description loaded — {len(text):,} characters")
            with st.expander("Preview"):
                st.text(text[:800] + ("…" if len(text) > 800 else ""))

    with jd_tab3:
        url_input = st.text_input("Job posting URL", placeholder="https://jobs.example.com/123")
        if st.button("🔄 Extract from URL"):
            if url_input and url_input.startswith("http"):
                with st.spinner("Scraping with CrewAI website tools and Serper fallback…"):
                    try:
                        extracted = scrape_job_url(url_input)
                        st.session_state.job_text = extracted
                        st.success(f"✅ Extracted {len(extracted):,} characters")
                        st.text_area("Preview:", value=extracted[:600], height=150, disabled=True)
                    except Exception as e:
                        st.error(f"❌ {e}")
            else:
                st.warning("Please enter a valid URL starting with https://")

    st.markdown("---")

    # ── Validation summary ───────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    col1.metric("Resume", "✅ Ready" if st.session_state.resume_text else "⚠️ Missing")
    col2.metric("Job JD", "✅ Ready" if st.session_state.job_text else "⚠️ Missing")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚙️ Continue to Process →", use_container_width=True):
            if not st.session_state.resume_text:
                st.error("Please add your resume.")
            elif not st.session_state.job_text:
                st.error("Please add the job description.")
            else:
                nav("process")
    with c2:
        if st.button("🔑 Check API Setup first", use_container_width=True):
            nav("setup")


# ─── PAGE: PROCESS ───────────────────────────────────────────────────────────────
def page_process():
    st.title("⚙️ Processing")

    if not st.session_state.resume_text or not st.session_state.job_text:
        st.warning("Please fill in your inputs first.")
        if st.button("← Back to Input"):
            nav("input")
        return

    # ── Config ───────────────────────────────────────────────────────────────────
    with st.expander("⚙️ Advanced settings", expanded=False):
        temperature = st.slider(
            "LLM Temperature",
            0.0,
            1.0,
            0.7,
            0.05,
            help="Lower = more focused; higher = more creative. RAG is always enabled.",
        )
    if "temperature" not in st.session_state:
        temperature = 0.7

    # ── Run ───────────────────────────────────────────────────────────────────────
    if st.button("🚀 Start AI Processing", use_container_width=True, type="primary"):
        st.session_state.results = None
        st.session_state.logs = []
        _run_crew(temperature)

    if st.session_state.results:
        run_status = st.session_state.results.get("status")
        if run_status == "complete":
            st.success("✅ Done!  Navigate to Results →")
        elif run_status == "failed":
            st.warning("Some steps finished before the run stopped. You can view the partial results.")
        else:
            st.info("Results are being generated step by step.")

        if st.button("📊 View Results →", use_container_width=True):
            nav("results")


def _run_crew(temperature: float):
    """Orchestrate the AI pipeline with live UI feedback."""
    import traceback

    log_box   = st.empty()
    progress  = st.progress(0)
    status    = st.empty()
    live_area = st.container()
    logs: list[str] = []

    def log(msg: str):
        logs.append(msg)
        log_box.markdown(
            '<div class="agent-log">' + "\n".join(logs[-30:]) + "</div>",
            unsafe_allow_html=True
        )

    def render_live_result(title: str, content: str):
        with live_area:
            st.markdown(
                f'<div class="stage-title">{title}</div>',
                unsafe_allow_html=True,
            )
            render_output_panel(content, "_No output captured for this step._")
            st.markdown("---")

    try:
        log("🔧 Importing dependencies…")
        from core.crew_manager import JobApplicationCrew
        progress.progress(5)

        log("🤖 Initialising agents…")
        status.info("Initialising AI agents…")
        crew = JobApplicationCrew(temperature=temperature, enable_rag=True)
        progress.progress(15)

        log("📋 Preparing inputs…")
        inputs = {
            "job_description": st.session_state.job_text,
            "resume":          st.session_state.resume_text,
            "job_role":        st.session_state.job_role,
        }
        progress.progress(20)

        st.session_state.results = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "job_role": st.session_state.job_role,
            "job_analysis": "",
            "candidate_profile": "",
            "optimized_resume": "",
            "skill_project_advice": "",
            "interview_questions": "",
            "talking_points": "",
            "raw_output": "",
            "num_questions": "0",
            "num_points": "0",
            "status": "running",
        }

        status_labels = {
            "job_analysis": "🔍 Analysing job requirements…",
            "profile": "👤 Building your professional profile…",
            "optimized_resume": "📝 Tailoring your resume…",
            "skill_project_advice": "🧭 Finding good-to-have skills and stronger project angles…",
            "interview": "🎤 Generating interview questions and talking points…",
        }

        display_titles = {
            "job_analysis": f"{icon('travel_explore')} Job Analysis",
            "profile": f"{icon('person_search')} Candidate Profile",
            "optimized_resume": f"{icon('description')} Optimised Resume",
            "skill_project_advice": f"{icon('route')} Skill & Project Guidance",
            "interview": f"{icon('record_voice_over')} Interview Prep",
        }

        with live_area:
            st.markdown("## Live Results")
            st.caption("Each section appears as soon as that agent finishes.")

        def on_step_start(step):
            key = step["key"]
            model = step.get("model", "unknown model")
            log(f"{status_labels[key]} Model: {model}")
            status.info(f"{status_labels[key]} ({model})")
            progress.progress(max(20, step["progress"] - 10))

        for index, step in enumerate(crew.iter_steps(inputs, on_step_start=on_step_start), start=1):
            key = step["key"]
            progress.progress(step["progress"])
            st.session_state.results = step["results"]
            render_live_result(display_titles[key], step["content"])
            log(f"✅ Step {index}/5 complete — {step['title']}.")

        log("✅ All agents completed successfully.")
        status.success("Done!")

    except Exception as e:
        if st.session_state.results:
            st.session_state.results["status"] = "failed"
            st.session_state.results["error"] = str(e)
            st.session_state.results["failed_step"] = getattr(e, "step_title", None)
            st.session_state.results["failed_model"] = getattr(e, "model", None)
            st.session_state.results["failure_reason"] = getattr(e, "reason", str(e))
        tb = traceback.format_exc()
        log(f"❌ ERROR: {e}\n{tb}")
        failed_step = getattr(e, "step_title", "Processing")
        failed_model = getattr(e, "model", "unknown model")
        failure_reason = getattr(e, "reason", str(e))
        status.error(f"{failed_step} stopped on {failed_model}.")
        st.error(f"Stopped at: {failed_step}")
        st.caption(f"Model: {failed_model}")
        st.caption(f"Reason: {failure_reason}")
        st.markdown("""
**Common fixes:**
- Check your API keys on the API Setup page
- Confirm internet access
- Try shorter inputs (< 4 000 chars each)
        """)


# ─── PAGE: RESULTS ───────────────────────────────────────────────────────────────
def page_results():
    st.markdown(f"# {icon('analytics')} Results", unsafe_allow_html=True)

    if not st.session_state.results:
        st.warning("No results yet — run Processing first.")
        if st.button("⚙️ Go to Process"):
            nav("process")
        return

    R = st.session_state.results
    ts = R.get("timestamp", "N/A")

    # ── Header metrics ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resume", "Optimised" if R.get("optimized_resume") else "Pending")
    c2.metric("Guidance", "Ready" if R.get("skill_project_advice") else "Pending")
    c3.metric("Questions", R.get("num_questions", "10"))
    c4.metric("Talking Points", R.get("num_points", "10+"))

    if R.get("status") == "failed":
        st.warning("This run stopped before all stages completed. Partial results are shown below.")
        if R.get("failed_step"):
            st.caption(f"Stopped at: {R.get('failed_step')} · Model: {R.get('failed_model')}")
        if R.get("failure_reason"):
            st.caption(f"Reason: {R.get('failure_reason')}")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Optimised Resume",
        "Skill & Project Gaps",
        "Interview Questions",
        "Talking Points",
        "Job Analysis",
        "Download All",
    ])

    # ── Tab 1: Resume ─────────────────────────────────────────────────────────────
    with tab1:
        resume_out = R.get("optimized_resume", "_No resume output generated._")
        st.markdown(f"### {icon('description')} Optimised Resume", unsafe_allow_html=True)
        render_output_panel(resume_out)
        st.download_button("⬇️ Download resume (.md)", resume_out,
                           file_name="optimized_resume.md", mime="text/markdown")

    # ── Tab 2: Skill & Project Gaps ──────────────────────────────────────────────
    with tab2:
        advice_out = R.get("skill_project_advice", "_No skill or project guidance generated._")
        st.markdown(f"### {icon('route')} Skill & Project Gaps", unsafe_allow_html=True)
        render_output_panel(advice_out)
        st.download_button("⬇️ Download skill and project guidance (.md)", advice_out,
                           file_name="skill_project_guidance.md", mime="text/markdown")

    # ── Tab 3: Questions ──────────────────────────────────────────────────────────
    with tab3:
        q_out = R.get("interview_questions", "_No questions generated._")
        st.markdown(f"### {icon('psychology_alt')} Interview Questions", unsafe_allow_html=True)
        render_output_panel(q_out)
        st.download_button("⬇️ Download questions (.md)", q_out,
                           file_name="interview_questions.md", mime="text/markdown")

    # ── Tab 4: Talking Points ─────────────────────────────────────────────────────
    with tab4:
        tp_out = R.get("talking_points", "_No talking points generated._")
        st.markdown(f"### {icon('tips_and_updates')} Talking Points", unsafe_allow_html=True)
        render_output_panel(tp_out)
        st.download_button("⬇️ Download talking points (.md)", tp_out,
                           file_name="talking_points.md", mime="text/markdown")

    # ── Tab 5: Job Analysis ───────────────────────────────────────────────────────
    with tab5:
        ja_out = R.get("job_analysis", "_No job analysis generated._")
        st.markdown(f"### {icon('travel_explore')} Job Analysis", unsafe_allow_html=True)
        render_output_panel(ja_out)

    # ── Tab 6: Download All ───────────────────────────────────────────────────────
    with tab6:
        st.markdown(f"### {icon('download')} Download complete package", unsafe_allow_html=True)
        package = {
            "generated_at":      R.get("timestamp"),
            "job_role":          st.session_state.job_role,
            "optimized_resume":  R.get("optimized_resume",""),
            "skill_project_advice": R.get("skill_project_advice",""),
            "interview_questions": R.get("interview_questions",""),
            "talking_points":    R.get("talking_points",""),
            "job_analysis":      R.get("job_analysis",""),
        }
        st.download_button(
            "⬇️ Download everything (JSON)",
            data=json.dumps(package, indent=2, ensure_ascii=False),
            file_name=f"job_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # Combined markdown
        combined_md = f"""# Job Application Package
Generated: {R.get('timestamp','')}
Role: {st.session_state.job_role}

---

## Optimised Resume

{R.get('optimized_resume','')}

---

## Interview Questions

{R.get('interview_questions','')}

---

## Skill And Project Guidance

{R.get('skill_project_advice','')}

---

## Talking Points

{R.get('talking_points','')}

---

## Job Analysis

{R.get('job_analysis','')}
"""
        st.download_button(
            "⬇️ Download everything (Markdown)",
            data=combined_md,
            file_name=f"job_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Process Another Application", use_container_width=True):
            st.session_state.results = None
            st.session_state.resume_text = ""
            st.session_state.job_text = ""
            st.session_state.job_role = ""
            nav("input")
    with c2:
        if st.button("✏️ Tweak Inputs & Re-run", use_container_width=True):
            nav("input")

    if ts and ts != "N/A":
        st.markdown(
            f'<div class="small-credit">Generated by Job Optimizer · {ts[:16]}</div>',
            unsafe_allow_html=True,
        )


# ─── PAGE: SETUP ─────────────────────────────────────────────────────────────────
def page_setup():
    st.markdown(f"# {icon('key')} API Key Setup", unsafe_allow_html=True)
    st.markdown("""
Enter a new key only when you want to update it. Saved keys stay hidden.
""")

    col_groq, col_google = st.columns(2)

    with col_groq:
        st.markdown(
            f"""<div class="api-card">
<h3>{icon('bolt')} Groq</h3>
<div class="api-note">Model: <strong>{GROQ_MODEL}</strong></div>
<div class="api-note">Create a key at console.groq.com and paste it below to update only Groq.</div>
</div>""",
            unsafe_allow_html=True,
        )
        with st.form("groq_key_form", clear_on_submit=True):
            groq_key = st.text_input(
                "GROQ_API_KEY",
                type="password",
                value="",
                placeholder="Paste a new Groq key, or leave blank to test saved key",
            )
            save_groq, test_groq = st.columns(2)
            save_groq_clicked = save_groq.form_submit_button("Save Groq Key", use_container_width=True)
            test_groq_clicked = test_groq.form_submit_button("Test Groq", use_container_width=True)
            if save_groq_clicked:
                saved = save_env_values({"GROQ_API_KEY": groq_key.strip()})
                if saved:
                    st.success("Groq key saved.")
                else:
                    st.warning("Paste a Groq key before saving.")
            if test_groq_clicked:
                try:
                    key = groq_key.strip() or os.getenv("GROQ_API_KEY")
                    if not key:
                        raise ValueError("Enter a Groq key or save one first.")
                    from langchain_groq import ChatGroq

                    llm = ChatGroq(
                        model_name=GROQ_MODEL,
                        api_key=key,
                        temperature=0,
                    )
                    res = llm.invoke("Say 'Groq OK' only.")
                    st.success(f"Groq working: {res.content[:40]}")
                except Exception as e:
                    st.error("Groq test failed.")
                    st.caption(short_error(e))

    with col_google:
    st.markdown(
        f"""<div class="api-card">
<h3>{icon('auto_awesome')} Google AI</h3>
<div class="api-note">Model: <strong>{GEMINI_MODEL}</strong></div>
<div class="api-note">Using Streamlit Secrets first, then environment fallback.</div>
</div>""",
        unsafe_allow_html=True,
    )

    with st.form("google_key_form", clear_on_submit=True):

        google_key = st.text_input(
            "GOOGLE_API_KEY",
            type="password",
            value="",
            placeholder="Optional local override key"
        )

        save_google, test_google = st.columns(2)

        save_google_clicked = save_google.form_submit_button(
            "Save Google Key",
            use_container_width=True
        )

        test_google_clicked = test_google.form_submit_button(
            "Test Gemini",
            use_container_width=True
        )

        # SAVE KEY LOCALLY
        if save_google_clicked:

            if google_key.strip():
                os.environ["GOOGLE_API_KEY"] = google_key.strip()
                st.success("Google API key saved locally.")
            else:
                st.warning("Please enter a key.")

        # TEST GEMINI
        if test_google_clicked:

            try:
                import time
                import concurrent.futures

                # PRIORITY:
                # 1. Streamlit Secrets
                # 2. Manual textbox
                # 3. Environment variable

                key = (
                    st.secrets.get("GOOGLE_API_KEY")
                    or google_key.strip()
                    or os.getenv("GOOGLE_API_KEY")
                )

                if not key:
                    raise ValueError(
                        "No Google API key found in Streamlit Secrets or environment."
                    )

                ensure_event_loop()

                from langchain_google_genai import ChatGoogleGenerativeAI

                llm = ChatGoogleGenerativeAI(
                    model=GEMINI_MODEL,
                    google_api_key=key,
                    temperature=0,
                    timeout=10,  # HARD TIMEOUT
                )

                # RUN WITH HARD STOP
                def run_test():
                    return llm.invoke("Reply ONLY with: Gemini OK")

                start = time.time()

                with concurrent.futures.ThreadPoolExecutor() as executor:

                    future = executor.submit(run_test)

                    try:
                        res = future.result(timeout=10)

                    except concurrent.futures.TimeoutError:
                        raise TimeoutError(
                            "Gemini API did not respond within 10 seconds."
                        )

                total = round(time.time() - start, 2)

                response_text = getattr(res, "content", str(res))

                st.success(f"✅ Gemini working in {total}s")
                st.code(response_text)

            except Exception as e:

                error_text = str(e)

                # BETTER ERROR MESSAGES

                if "429" in error_text:
                    st.error("❌ Gemini quota exceeded.")
                    st.caption(
                        "Your Google AI project has no remaining quota "
                        "or billing is disabled."
                    )

                elif "API_KEY" in error_text.upper():
                    st.error("❌ Invalid Google API key.")

                elif "timeout" in error_text.lower():
                    st.error("❌ Gemini request timeout.")
                    st.caption(
                        "The API did not respond within 10 seconds."
                    )

                elif "quota" in error_text.lower():
                    st.error("❌ Gemini quota/billing issue.")

                else:
                    st.error("❌ Google AI test failed.")
                    st.caption(error_text)

# ─── Router ───────────────────────────────────────────────────────────────────────
page = st.session_state.page
if   page == "home":    page_home()
elif page == "input":   page_input()
elif page == "process": page_process()
elif page == "results": page_results()
elif page == "setup":   page_setup()
else:
    page_home()
