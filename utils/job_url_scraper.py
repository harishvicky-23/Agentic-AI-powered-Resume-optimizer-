from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


class UrlScrapeError(RuntimeError):
    pass


class EnvVar(BaseModel):
    name: str
    description: str = ""
    required: bool = False


def scrape_job_url(url: str) -> str:
    """Scrape a job URL with CrewAI tools, using Serper as a search fallback."""
    if not url.startswith(("http://", "https://")):
        raise UrlScrapeError("Please enter a valid URL starting with http:// or https://.")

    errors: list[str] = []

    try:
        text = _scrape_with_crewai_tool(url)
        if _looks_useful(text):
            return _clean_scraped_text(text)
        errors.append("ScrapeWebsiteTool returned too little job-posting text.")
    except Exception as exc:
        errors.append(f"ScrapeWebsiteTool: {_short_error(exc)}")

    try:
        text = _scrape_with_requests(url)
        if _looks_useful(text):
            return _clean_scraped_text(text)
        errors.append("Requests fallback returned too little job-posting text.")
    except Exception as exc:
        errors.append(f"Requests fallback: {_short_error(exc)}")

    if os.getenv("SERPER_API_KEY"):
        try:
            text = _search_with_serper(url)
            if _looks_useful(text, min_len=120):
                return _clean_scraped_text(text)
            errors.append("Serper returned too little search context.")
        except Exception as exc:
            errors.append(f"SerperDevTool: {_short_error(exc)}")
    else:
        errors.append("SERPER_API_KEY is not configured, so Serper fallback was skipped.")

    raise UrlScrapeError("Could not extract a usable job description. " + " | ".join(errors))


def _scrape_with_crewai_tool(url: str) -> str:
    tool_cls = _load_tool_class(
        "scrape_website_tool/scrape_website_tool.py",
        "ScrapeWebsiteTool",
    )
    tool = tool_cls()
    return str(tool._run(website_url=url))


def _search_with_serper(url: str) -> str:
    tool_cls = _load_tool_class(
        "serper_dev_tool/serper_dev_tool.py",
        "SerperDevTool",
        needs_envvar=True,
    )
    query = f"job description requirements responsibilities {url}"
    tool = tool_cls(n_results=5)
    return str(tool._run(search_query=query))


def _load_tool_class(relative_tool_path: str, class_name: str, needs_envvar: bool = False) -> Any:
    if needs_envvar:
        import crewai.tools as crewai_tools

        if not hasattr(crewai_tools, "EnvVar"):
            crewai_tools.EnvVar = EnvVar

    root = Path(__file__).resolve().parents[1]
    module_path = root / ".venv" / "Lib" / "site-packages" / "crewai_tools" / "tools" / relative_tool_path
    if not module_path.exists():
        raise UrlScrapeError(f"CrewAI tool file not found: {module_path.name}")

    spec = importlib.util.spec_from_file_location(f"_job_tool_{class_name}", module_path)
    if not spec or not spec.loader:
        raise UrlScrapeError(f"Could not load CrewAI tool: {class_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def _scrape_with_requests(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def _clean_scraped_text(text: str) -> str:
    text = re.sub(r"The following text is scraped website content:\s*", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text)


def _looks_useful(text: str, min_len: int = 300) -> bool:
    lowered = text.lower()
    signals = ["responsibilities", "requirements", "qualifications", "skills", "experience", "about the role"]
    return len(text.strip()) >= min_len and any(signal in lowered for signal in signals)


def _short_error(exc: Exception) -> str:
    text = re.sub(r"\s+", " ", str(exc)).strip()
    return text[:400] + ("..." if len(text) > 400 else "")
