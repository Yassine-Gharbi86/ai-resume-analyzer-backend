"""
api/ai_service.py — AI Analysis Service (Phase 3 + 4)

Responsibilities:
  1. Extract raw text from a PDF using PyMuPDF
  2. Analyze a resume with Groq → structured JSON (Phase 3)
  3. Match a resume against a job description → match report (Phase 4)
"""

import fitz
import json
import re
from groq import Groq
from django.conf import settings

GROQ_MODEL = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────

def _get_client() -> Groq:
    """Returns an authenticated Groq client. Raises if key is missing."""
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Run: export GROQ_API_KEY='gsk_...' then restart the server."
        )
    return Groq(api_key=settings.GROQ_API_KEY)


def _call_groq(client: Groq, prompt: str, max_tokens: int = 2000) -> dict:
    """
    Sends a prompt to Groq and returns a parsed Python dict.

    Both the resume analysis and job matching prompts instruct the model
    to return JSON only. This function handles the API call and JSON
    parsing in one place so neither prompt needs its own try/except.
    """
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise JSON-generating AI. "
                    "You always return valid JSON and nothing else. "
                    "No markdown, no code blocks, no preamble, no explanation."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )

    raw = completion.choices[0].message.content.strip()

    # Strip accidental markdown code fences defensively
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw)
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"AI returned invalid JSON. Error: {e}. "
            f"First 300 chars: {raw[:300]}"
        )


def extract_text_from_pdf(file_path: str) -> str:
    """
    Opens a PDF from disk and extracts all readable text via PyMuPDF.

    Returns text capped at 6000 characters (~1500 tokens) to stay
    within Groq's context window comfortably.
    """
    doc = fitz.open(file_path)
    pages_text = []

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text")
        if text.strip():
            pages_text.append(text)

    doc.close()

    if not pages_text:
        raise ValueError(
            "No readable text found in this PDF. "
            "It may be a scanned image. Please use a text-based PDF."
        )

    return "\n--- PAGE BREAK ---\n".join(pages_text)[:6000]


# ─────────────────────────────────────────────
# PHASE 3 — RESUME ANALYSIS
# ─────────────────────────────────────────────

ANALYSIS_PROMPT = """
You are an expert ATS (Applicant Tracking System) and career coach AI.
Analyze the resume text below and return a structured JSON analysis.

RESUME TEXT:
{resume_text}

Return ONLY a valid JSON object — no markdown, no code fences, no explanation.
Use exactly this structure:

{{
  "ats_score": <integer 0-100>,
  "score_breakdown": {{
    "contact_info": <integer 0-20>,
    "work_experience": <integer 0-30>,
    "skills": <integer 0-25>,
    "education": <integer 0-15>,
    "formatting": <integer 0-10>
  }},
  "summary": "<2-3 sentence overall assessment>",
  "experience_summary": {{
    "years_of_experience": "<e.g. 3-5 years>",
    "seniority_level": "<Junior | Mid-level | Senior | Lead | Executive>",
    "top_roles": ["<role 1>", "<role 2>"],
    "industries": ["<industry 1>", "<industry 2>"]
  }},
  "skills": {{
    "technical": ["<skill>", "..."],
    "soft": ["<skill>", "..."],
    "missing_keywords": ["<important keyword not in resume>", "..."]
  }},
  "strengths": [
    "<specific strength>",
    "<specific strength>",
    "<specific strength>"
  ],
  "improvements": [
    {{
      "priority": "high",
      "issue": "<concise issue title>",
      "suggestion": "<specific actionable suggestion>"
    }},
    {{
      "priority": "medium",
      "issue": "<concise issue title>",
      "suggestion": "<specific actionable suggestion>"
    }},
    {{
      "priority": "low",
      "issue": "<concise issue title>",
      "suggestion": "<specific actionable suggestion>"
    }}
  ],
  "keywords_found": ["<keyword>", "..."],
  "overall_verdict": "<Strong | Good | Average | Needs Work>"
}}
"""


def run_full_analysis(file_path: str) -> dict:
    """
    Phase 3 pipeline: PDF path → text → AI analysis → dict.
    This is the only function the analyze view needs to call.
    """
    resume_text = extract_text_from_pdf(file_path)
    client      = _get_client()
    prompt      = ANALYSIS_PROMPT.format(resume_text=resume_text)
    analysis    = _call_groq(client, prompt, max_tokens=2000)

    analysis['extracted_text_preview'] = resume_text[:500]
    analysis['text_length']            = len(resume_text)
    return analysis


# ─────────────────────────────────────────────
# PHASE 4 — JOB MATCHING
# ─────────────────────────────────────────────

MATCH_PROMPT = """
You are an expert ATS recruiter AI.
Compare the resume and job description below and return a structured match report.

RESUME TEXT:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a valid JSON object — no markdown, no code fences, no explanation.
Use exactly this structure:

{{
  "match_score": <integer 0-100>,
  "verdict": "<Excellent Match | Good Match | Partial Match | Poor Match>",
  "summary": "<2-3 sentence overall assessment of fit>",
  "score_breakdown": {{
    "skills_match": <integer 0-35>,
    "experience_match": <integer 0-30>,
    "education_match": <integer 0-15>,
    "keywords_match": <integer 0-20>
  }},
  "matched_keywords": ["<keyword present in both resume and JD>", "..."],
  "missing_keywords": ["<keyword in JD but NOT in resume>", "..."],
  "matched_skills": ["<skill the candidate has that the JD requires>", "..."],
  "missing_skills": ["<skill the JD requires that the candidate lacks>", "..."],
  "strengths_for_role": [
    "<specific reason this candidate is strong for this role>",
    "<specific reason>",
    "<specific reason>"
  ],
  "gaps": [
    {{
      "area": "<gap area title>",
      "detail": "<what is missing and why it matters for this role>"
    }}
  ],
  "tailoring_suggestions": [
    {{
      "priority": "high",
      "suggestion": "<specific actionable change to make the resume fit this JD better>"
    }},
    {{
      "priority": "medium",
      "suggestion": "<specific actionable change>"
    }},
    {{
      "priority": "low",
      "suggestion": "<specific actionable change>"
    }}
  ],
  "job_title_detected": "<job title extracted from the JD>",
  "company_detected": "<company name if found in JD, else null>"
}}
"""


def run_job_match(file_path: str, job_description: str) -> dict:
    """
    Phase 4 pipeline: PDF + job description text → match report → dict.

    Args:
        file_path:       absolute path to the stored resume PDF
        job_description: raw text pasted by the user from a job posting

    Returns:
        dict with match score, keyword gaps, tailoring suggestions, etc.
    """
    if not job_description or len(job_description.strip()) < 50:
        raise ValueError(
            "Job description is too short. "
            "Please paste the full job posting (at least 50 characters)."
        )

    resume_text = extract_text_from_pdf(file_path)
    client      = _get_client()

    # Trim job description to 4000 chars so the combined prompt
    # stays within Groq's token limits alongside the resume text.
    jd_trimmed = job_description.strip()[:4000]

    prompt = MATCH_PROMPT.format(
        resume_text=resume_text,
        job_description=jd_trimmed,
    )

    return _call_groq(client, prompt, max_tokens=2500)
