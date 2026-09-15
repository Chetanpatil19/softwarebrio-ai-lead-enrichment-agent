import re
from typing import List

from .schemas import CompanyIntelligence, TeamMember


def fallback_extract(domain: str, pages: List[dict]) -> CompanyIntelligence:
    """
    Deterministic fallback used when LLM extraction is unavailable.

    It extracts useful information directly from the cleaned website
    content so the pipeline can continue without crashing.
    """

    text = "\n\n".join(p["text"] for p in pages)
    lower = text.lower()

    # ---------------------------------------------------------
    # 1. Extract public email addresses
    # ---------------------------------------------------------
    emails = sorted(
        set(
            re.findall(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                text,
                re.I,
            )
        )
    )

    # ---------------------------------------------------------
    # 2. Extract LinkedIn URLs discovered by the crawler
    # ---------------------------------------------------------
    linkedin = []

    for page in pages:
        linkedin.extend(page.get("linkedin_urls", []))

    linkedin = sorted(set(linkedin))

    # ---------------------------------------------------------
    # 3. Determine target audience from website content
    # ---------------------------------------------------------
    if any(
        word in lower
        for word in [
            "developer",
            "developers",
            "engineering team",
            "software engineer",
            "api",
            "technical team",
        ]
    ):
        audience = (
            "Developers, engineers, and technical teams using the company's "
            "software platform, APIs, or developer tools."
        )

    elif any(
        word in lower
        for word in [
            "enterprise",
            "businesses",
            "organizations",
            "companies",
        ]
    ):
        audience = (
            "Businesses, organizations, and enterprise teams using the "
            "company's products or services."
        )

    elif any(
        word in lower
        for word in [
            "customer",
            "customers",
            "users",
        ]
    ):
        audience = (
            "Customers and users who need the company's products or services."
        )

    else:
        audience = (
            "The target audience could not be confidently determined "
            "from the available website content."
        )

    # ---------------------------------------------------------
    # 4. Try to create a simple overview from page titles/content
    # ---------------------------------------------------------
    domain_name = domain.replace("www.", "").split(".")[0].title()

    product_words = []

    keywords = [
        "platform",
        "software",
        "technology",
        "developer",
        "developers",
        "API",
        "AI",
        "cloud",
        "database",
        "security",
        "analytics",
        "payments",
    ]

    for keyword in keywords:
        if keyword.lower() in lower:
            product_words.append(keyword)

    if product_words:
        unique_words = list(dict.fromkeys(product_words))[:4]

        overview = (
            f"{domain_name} operates a technology-focused business and its "
            f"website describes products or services related to "
            f"{', '.join(unique_words)}. "
            f"The available website content indicates that its offerings "
            f"are designed for customers and users who need these capabilities."
        )
    else:
        overview = (
            f"{domain_name} provides products or services described on its "
            f"official website. "
            f"The available website content provides limited information for "
            f"a more specific automated company description."
        )

    # ---------------------------------------------------------
    # 5. Create conservative leadership records from LinkedIn URLs
    # ---------------------------------------------------------
    leadership = []

    for url in linkedin:
        leadership.append(
            TeamMember(
                name="Unknown",
                role="LinkedIn profile discovered from website",
                linkedin_url=url,
            )
        )

    # ---------------------------------------------------------
    # 6. Confidence score
    # ---------------------------------------------------------
    confidence = 0.35

    if len(pages) >= 5:
        confidence += 0.10

    if emails:
        confidence += 0.10

    if linkedin:
        confidence += 0.05

    confidence = min(confidence, 0.60)

    # ---------------------------------------------------------
    # 7. Return structured result
    # ---------------------------------------------------------
    return CompanyIntelligence(
        domain=domain,
        company_overview=overview,
        target_audience_icp=audience,
        contact_emails=emails,
        key_leadership_team=leadership,
        data_confidence_score=confidence,
        source_pages=[p["url"] for p in pages],
    )