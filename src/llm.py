
import json
from typing import List

from openai import OpenAI

from .schemas import CompanyIntelligence, TeamMember


SYSTEM_PROMPT = """
You are a lead-enrichment extraction agent.

Use ONLY the supplied cleaned website text. Never invent facts.
Return structured data matching the schema.

Rules:
- company_overview must be exactly two concise sentences.
- target_audience_icp should identify the most likely users/buyers supported by the text.
- contact_emails must contain only public generic/company emails explicitly present in the supplied text.
- key_leadership_team should include names, roles and LinkedIn URLs only when supported by the supplied text.
- If a field is not supported, use an empty list/string rather than guessing.
- data_confidence_score must reflect completeness and source quality:
  0.9+ = strong first-party evidence for most fields
  0.7-0.89 = good evidence with some missing fields
  0.4-0.69 = partial evidence
  below 0.4 = weak evidence
"""


def extract_with_llm(domain: str, pages: List[dict], api_key: str, model: str) -> CompanyIntelligence:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)

    compact_pages = []
    for p in pages:
        compact_pages.append({
            "url": p["url"],
            "title": p["title"],
            "text": p["text"][:8000],
        })

    prompt = (
        f"Target domain: {domain}\n\n"
        "Cleaned first-party pages:\n"
        + json.dumps(compact_pages, ensure_ascii=False)
    )

    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=CompanyIntelligence,
        temperature=0,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("LLM returned no structured result.")
    return parsed
