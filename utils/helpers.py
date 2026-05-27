"""
Utility helpers — URL scraping, PDF reading, skill extraction, validation.
"""

from __future__ import annotations
import re
from typing import Optional
from urllib.parse import urlparse


# ─── Validation ───────────────────────────────────────────────────────────────────
def validate_inputs(
    resume: str,
    job_description: str,
    github_url: Optional[str] = None,
) -> tuple[bool, str]:
    errors = []
    if not resume or len(resume.strip()) < 100:
        errors.append("Resume must be at least 100 characters.")
    if len(resume) > 60_000:
        errors.append("Resume too long (max 60 000 chars).")
    if not job_description or len(job_description.strip()) < 80:
        errors.append("Job description must be at least 80 characters.")
    if github_url and not _valid_url(github_url):
        errors.append("GitHub URL format invalid.")
    return (not errors), " | ".join(errors)


def _valid_url(url: str) -> bool:
    try:
        r = urlparse(url)
        return bool(r.scheme and r.netloc)
    except Exception:
        return False


# ─── PDF Reading ─────────────────────────────────────────────────────────────────
def extract_pdf_text(file_bytes: bytes) -> str:
    import io
    from pypdf import PdfReader          # pypdf — pure Python, no compiler needed
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


# ─── URL Scraping ────────────────────────────────────────────────────────────────
def extract_text_from_url(url: str, timeout: int = 15) -> str:
    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobOptimizerBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
    return "\n".join(lines)


# ─── Skill Extraction ─────────────────────────────────────────────────────────────
_SKILLS = [
    # Languages
    "Python","JavaScript","TypeScript","Java","Go","Rust","C++","C#","Ruby",
    "PHP","Swift","Kotlin","Scala","R","Perl","Bash","Shell",
    # Frontend
    "React","Vue","Angular","Next.js","Svelte","Tailwind CSS","HTML","CSS","SASS",
    # Backend
    "Node.js","Django","Flask","FastAPI","Spring","Express","Laravel","Rails","ASP.NET",
    # Databases
    "PostgreSQL","MySQL","MongoDB","Redis","Elasticsearch","DynamoDB","Cassandra",
    "SQLite","Oracle","SQL Server","BigQuery","Snowflake",
    # Cloud
    "AWS","Azure","GCP","Google Cloud","Heroku","DigitalOcean","Cloudflare",
    # DevOps
    "Docker","Kubernetes","Terraform","Ansible","Jenkins","GitHub Actions",
    "GitLab CI","Linux","Nginx","Prometheus","Grafana",
    # Data / AI
    "TensorFlow","PyTorch","Scikit-learn","Pandas","NumPy","Spark","Kafka",
    "Airflow","dbt","LangChain","LLM","RAG","OpenAI","Hugging Face",
    "Machine Learning","Deep Learning","NLP","Computer Vision","MLOps",
    # Practices / misc
    "REST API","GraphQL","gRPC","Microservices","CI/CD","Git","Agile","Scrum",
    "Kanban","TDD","BDD","System Design","Distributed Systems","Event-driven",
]

def extract_skills(text: str) -> list[str]:
    tl = text.lower()
    return list(dict.fromkeys(s for s in _SKILLS if s.lower() in tl))


def match_score(resume: str, job: str) -> int:
    r = set(extract_skills(resume))
    j = set(extract_skills(job))
    if not j:
        return 0
    return round(len(r & j) / len(j) * 100)


# ─── Text Utilities ───────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    text = re.sub(r"\x00|\ufeff", "", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def truncate(text: str, max_chars: int = 6_000) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last = cut.rfind(".")
    return (cut[:last + 1] if last > max_chars - 400 else cut) + "…"


def parse_years_of_experience(job_text: str) -> Optional[int]:
    m = re.search(r"(\d+)\+?\s*years?", job_text, re.IGNORECASE)
    return int(m.group(1)) if m else None
