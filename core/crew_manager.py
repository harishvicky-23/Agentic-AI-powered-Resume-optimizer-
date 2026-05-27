"""
JobApplicationCrew - CrewAI implementation.

This keeps the Streamlit-facing class name while orchestrating the workflow
with CrewAI agents and tasks. The same free model/key split is preserved:
Groq handles job analysis and resume rewriting, while Gemini handles profile,
career advice, and interview preparation.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from config import GEMINI_MODEL, GROQ_MODEL
from crewai import Agent, Crew, LLM, Process, Task


os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

STEP_ORDER = [
    ("job_analysis", "Job Analyzer", 35),
    ("profile", "Profile Generator", 50),
    ("optimized_resume", "Resume Optimizer", 65),
    ("skill_project_advice", "Skill & Project Advisor", 80),
    ("interview", "Interview Coach", 100),
]


class PipelineStepError(RuntimeError):
    def __init__(self, step_key: str, step_title: str, model: str, reason: str):
        self.step_key = step_key
        self.step_title = step_title
        self.model = model
        self.reason = reason
        super().__init__(
            f"{step_title} stopped while using {model}. Reason: {reason}"
        )


def _groq(temperature: float = 0.7) -> LLM:
    return LLM(
        model=f"groq/{GROQ_MODEL}",
        temperature=temperature,
        api_key=os.environ["GROQ_API_KEY"],
        timeout=120,
    )


def _gemini(temperature: float = 0.7) -> LLM:
    return LLM(
        model=f"gemini/{GEMINI_MODEL}",
        temperature=temperature,
        api_key=os.environ["GOOGLE_API_KEY"],
        timeout=120,
    )


class JobApplicationCrew:
    """
    Four-step job application pipeline:
      1. Analyze the job posting.
      2. Build a candidate profile.
      3. Tailor the resume.
      4. Generate interview prep.
      5. Recommend good-to-have skills and stronger project angles.
    """

    def __init__(self, temperature: float = 0.7, enable_rag: bool = True):
        self.temperature = temperature
        self.enable_rag = enable_rag
        self.job_llm = _groq(temperature)
        self.profile_llm = _gemini(temperature)
        self.resume_llm = _groq(temperature)
        self.interview_llm = _gemini(temperature)
        self.advisor_llm = _gemini(temperature)

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for step in self.iter_steps(inputs):
            result = step["results"]
        return result

    def iter_steps(self, inputs: dict[str, Any], on_step_start=None):
        """Run CrewAI one task at a time and yield each completed result."""
        job_desc = inputs.get("job_description", "")
        resume = inputs.get("resume", "")
        job_role = inputs.get("job_role", "the advertised role")

        if self.enable_rag:
            try:
                from utils.rag_processor import RAGProcessor

                rag = RAGProcessor()
                resume = rag.summarize_resume(resume)
                job_desc = rag.summarize_job_description(job_desc)
            except Exception as e:
                print(f"[RAG] Skipped due to error: {e}")

        tasks = self._build_tasks(
            job_role=job_role,
            job_desc=job_desc,
            resume=resume,
        )
        results = _empty_results(job_role)

        for key, title, progress in STEP_ORDER:
            task = tasks[key]
            model = _task_model(task)
            if on_step_start:
                on_step_start(
                    {
                        "key": key,
                        "title": title,
                        "progress": progress,
                        "model": model,
                    }
                )
            try:
                crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False,
                    memory=False,
                )
                crew_output = crew.kickoff()
            except Exception as exc:
                raise PipelineStepError(
                    step_key=key,
                    step_title=title,
                    model=model,
                    reason=_classify_error(exc),
                ) from exc
            content = _task_output(task) or _content(crew_output)
            _store_step_result(results, key, content)

            yield {
                "key": key,
                "title": title,
                "content": content,
                "progress": progress,
                "results": dict(results),
            }

    def _build_tasks(self, job_role: str, job_desc: str, resume: str) -> dict[str, Task]:
        job_agent = Agent(
            role="Concise Job Signal Analyst",
            goal="Extract only the hiring signals that downstream resume and interview tasks need.",
            backstory="You compress job posts into practical evidence: must-have skills, responsibilities, seniority, keywords, and selection criteria.",
            llm=self.job_llm,
            allow_delegation=False,
            verbose=False,
            max_iter=1,
        )
        profile_agent = Agent(
            role="Candidate Evidence Mapper",
            goal="Map the resume evidence to the job requirements without writing resume copy.",
            backstory="You identify proof points, transferable strengths, and missing evidence so the resume writer can avoid generic repetition.",
            llm=self.profile_llm,
            allow_delegation=False,
            verbose=False,
            max_iter=1,
        )
        resume_agent = Agent(
            role="First-Person ATS Resume Writer",
            goal="Create a concise, targeted Markdown resume in first person for summary and value proposition sections.",
            backstory="You write direct, candidate-owned resume copy. You avoid third-person phrasing, repeated summaries, and invented facts.",
            llm=self.resume_llm,
            allow_delegation=False,
            verbose=False,
            max_iter=1,
        )
        advisor_agent = Agent(
            role="Portfolio Gap Advisor",
            goal="Prioritize the few missing signals and project upgrades that would most improve this application.",
            backstory="You give direct, practical next actions tied to the current role, avoiding long generic advice.",
            llm=self.advisor_llm,
            allow_delegation=False,
            verbose=False,
            max_iter=1,
        )
        interview_agent = Agent(
            role="Focused Interview Coach",
            goal="Create role-specific interview preparation from the final tailored resume and job signals.",
            backstory="You prepare candidates quickly with high-probability questions, grounded STAR prompts, and targeted review areas.",
            llm=self.interview_llm,
            allow_delegation=False,
            verbose=False,
            max_iter=1,
        )

        job_task = Task(
            description=_job_analysis_prompt(job_role, job_desc),
            expected_output="Concise Markdown job signal brief with must-have skills, responsibilities, seniority, keywords, and selection criteria.",
            agent=job_agent,
        )
        profile_task = Task(
            description=_profile_prompt(resume),
            expected_output="Concise Markdown evidence map: matching strengths, reusable proof points, gaps, and positioning notes. Not resume copy.",
            agent=profile_agent,
            context=[job_task],
        )
        resume_task = Task(
            description=_resume_prompt(job_role, resume),
            expected_output="Complete Markdown resume with a first-person Executive Summary and first-person Unique Value Proposition, no fabricated facts.",
            agent=resume_agent,
            context=[job_task, profile_task],
        )
        advice_task = Task(
            description=_skill_project_advice_prompt(job_role, resume),
            expected_output="Concise Markdown with good-to-have missing skills, project upgrade tips, and a top-three priority plan.",
            agent=advisor_agent,
            context=[job_task, resume_task],
        )
        interview_task = Task(
            description=_interview_prompt(job_role),
            expected_output="Markdown interview preparation with role-specific questions, STAR talking points, interviewer questions, and review topics.",
            agent=interview_agent,
            context=[job_task, profile_task, resume_task, advice_task],
        )

        return {
            "job_analysis": job_task,
            "profile": profile_task,
            "optimized_resume": resume_task,
            "skill_project_advice": advice_task,
            "interview": interview_task,
        }


def _content(result: Any) -> str:
    content = getattr(result, "content", result)
    content = getattr(content, "raw", content)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content or "").strip()


def _task_output(task: Task) -> str:
    output = getattr(task, "output", None)
    if not output:
        return ""
    return _content(output)


def _task_model(task: Task) -> str:
    llm = getattr(getattr(task, "agent", None), "llm", None)
    return str(getattr(llm, "model", None) or getattr(llm, "model_name", None) or "unknown model")


def _classify_error(exc: Exception) -> str:
    text = str(exc).strip()
    lowered = text.lower()
    if "rate limit" in lowered or "429" in lowered or "quota" in lowered:
        category = "rate limit or quota exceeded"
    elif "context" in lowered or "token" in lowered or "maximum" in lowered:
        category = "token or context limit"
    elif "api key" in lowered or "unauthorized" in lowered or "401" in lowered or "403" in lowered:
        category = "API key or permission issue"
    elif "timeout" in lowered or "timed out" in lowered:
        category = "request timeout"
    elif "connection" in lowered or "network" in lowered:
        category = "network connection issue"
    else:
        category = exc.__class__.__name__
    text = re.sub(r"\s+", " ", text)
    if len(text) > 900:
        text = text[:900] + "..."
    return f"{category}: {text}" if text else category


def _empty_results(job_role: str) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "job_role": job_role,
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


def _store_step_result(results: dict[str, Any], key: str, content: str) -> None:
    results["timestamp"] = datetime.now().isoformat(timespec="seconds")

    if key == "job_analysis":
        results["job_analysis"] = content or "*(Job analysis not captured)*"
    elif key == "profile":
        results["candidate_profile"] = content or "*(Candidate profile not captured)*"
    elif key == "optimized_resume":
        results["optimized_resume"] = content or "*(Resume not captured)*"
    elif key == "skill_project_advice":
        results["skill_project_advice"] = content or "*(Skill and project advice not captured)*"
    elif key == "interview":
        interview_questions, talking_points = _split_interview(content)
        num_q = len(re.findall(r"^\s*\*\*Q\d+", interview_questions, re.M))
        num_tp = len(
            re.findall(r"^\s*\*\*(Situation|Task|Action|Result)\*\*", talking_points, re.M)
        )
        results["interview_questions"] = interview_questions or content
        results["talking_points"] = talking_points or "*(Talking points not captured)*"
        results["raw_output"] = content
        results["num_questions"] = num_q if num_q > 0 else "10"
        results["num_points"] = num_tp if num_tp > 0 else "10+"
        results["status"] = "complete"


def _job_analysis_prompt(job_role: str, job_desc: str) -> str:
    return f"""You are a concise job requirements analyst.

Analyze this job posting for the role: {job_role}

JOB DESCRIPTION:
```
{job_desc[:6000]}
```

Return a structured Markdown report with:
1. Role Snapshot - seniority, team context, primary mission
2. Must-Have Skills - top 8 only
3. Nice-To-Have Signals - top 5 only
4. Key Responsibilities - top 5 only
5. Candidate Selection Criteria - what the resume must prove
6. ATS Keywords - exact phrases, comma-separated

Keep it concise. Avoid restating the whole job post.
"""


def _profile_prompt(resume: str) -> str:
    return f"""You are a candidate evidence mapper.

Map resume evidence to the job analysis. Do not write final resume prose.

RESUME:
```
{resume[:6000]}
```

Return Markdown with:
1. Relevant Strengths - 5 bullets tied to the job
2. Evidence To Reuse - bullets with exact resume facts/projects/skills
3. Missing Or Weak Proof - concise gaps only
4. Positioning Notes - how the resume writer should differentiate the candidate

Do not invent facts.
Do not include an Executive Summary or Unique Value Proposition here.
"""


def _resume_prompt(job_role: str, resume: str) -> str:
    return f"""You are an expert ATS resume optimizer and first-person resume writer.

Rewrite the candidate resume for this role: {job_role}

ORIGINAL RESUME:
```
{resume[:6000]}
```

Rules:
- Output a complete Markdown resume using ## section headings.
- Start with ## Executive Summary written in first person.
- Include ## Unique Value Proposition at the end written in first person and make it distinct from the Executive Summary.
- The Executive Summary should say what I am best at and what role fit I bring.
- The Unique Value Proposition should explain my differentiator and why I am valuable for this specific role.
- Weave ATS keywords naturally into skills and experience, not by stuffing.
- Reorder bullets with the most relevant first.
- Quantify achievements only when the resume supports it.
- Do not invent qualifications, companies, or dates.
- Avoid third-person phrases such as "the candidate", "he", "she", or the person's name in summary/value sections.
- Keep the resume concise and avoid repeating the same sentence across sections.
"""


def _skill_project_advice_prompt(
    job_role: str,
    original_resume: str,
) -> str:
    return f"""You are a career strategy advisor for technical candidates.

Identify the non-mandatory but high-signal improvements that would make this
candidate more competitive for: {job_role}

ORIGINAL RESUME:
```
{original_resume[:5000]}
```

Return concise Markdown with exactly these sections:

## Good-To-Have Skills Missing
List 4-6 skills, tools, domains, or signals that are useful for this job but
not clearly proven in the resume. For each item include:
- **Skill**
- **Why it matters**
- **How to show it quickly**

## Project Upgrade Tips
Recommend 3 project ideas or upgrades that would likely carry better weight
for this job than weak or generic current projects. For each item include:
- **Project angle**
- **Why it has stronger weightage**
- **What to build or improve**
- **Resume bullet to aim for**

## Priority Plan
Rank the top 3 actions the candidate should do first.

Rules:
- Do not invent experience.
- Keep advice practical for a portfolio, resume, or interview.
- Prefer advice tied directly to the job description.
"""


def _interview_prompt(job_role: str) -> str:
    return f"""You are a senior interview coach.

Prepare interview materials for a candidate applying for: {job_role}

Produce Markdown with:

## Part A - Interview Questions
10 total questions. Format each as:
**Q1. [Question]**
> Why they ask this: ...
> How to answer: ...

Include 3 behavioral, 4 technical, 2 situational, and 1 culture-fit question.

## Part B - STAR Talking Points
For each of the candidate's top 3 experiences, write:
- **Situation** - brief context
- **Task** - responsibility
- **Action** - specific action
- **Result** - measurable or concrete outcome

## Part C - Questions to Ask the Interviewer
5 thoughtful questions.

## Part D - Topics to Review
Likely technical concepts.
"""


def _split_interview(text: str) -> tuple[str, str]:
    if not text:
        return "", ""

    part_b_patterns = [
        r"(?i)##\s*Part\s*B",
        r"(?i)## STAR Talking Points",
        r"(?i)## Talking Points",
    ]
    for pattern in part_b_patterns:
        match = re.search(pattern, text)
        if match:
            return text[: match.start()].strip(), text[match.start() :].strip()

    mid = len(text) // 2
    return text[:mid].strip(), text[mid:].strip()
