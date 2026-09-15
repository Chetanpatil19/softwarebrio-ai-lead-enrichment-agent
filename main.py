
import argparse
import asyncio
import json
import logging
from pathlib import Path

from src.config import settings
from src.crawler import crawl_domain
from src.fallback import fallback_extract
from src.llm import extract_with_llm


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


async def process_domain(domain: str):
    logging.info("Crawling %s", domain)
    pages = await crawl_domain(
        domain=domain,
        max_pages=settings.max_pages_per_domain,
        timeout_ms=settings.page_timeout_ms,
        max_chars=settings.max_chars_per_page,
        headless=settings.headless,
    )

    page_dicts = [
        {
            "url": p.url,
            "title": p.title,
            "text": p.text,
            "emails": p.emails,
            "linkedin_urls": p.linkedin_urls,
        }
        for p in pages
    ]

    if not page_dicts:
        logging.warning("No usable pages found for %s", domain)
        return {
            "domain": domain,
            "company_overview": "",
            "target_audience_icp": "",
            "contact_emails": [],
            "key_leadership_team": [],
            "data_confidence_score": 0.0,
            "source_pages": [],
            "error": "No usable pages found",
        }

    try:
        result = extract_with_llm(
            domain=domain,
            pages=page_dicts,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
        # Keep crawler-discovered source pages authoritative.
        result.source_pages = [p.url for p in pages]
        return result.model_dump()

    except Exception as exc:
        logging.warning("LLM extraction failed for %s: %s. Using fallback.", domain, exc)
        result = fallback_extract(domain, page_dicts)
        result.source_pages = [p.url for p in pages]
        result_dict = result.model_dump()
        result_dict["llm_fallback"] = True
        result_dict["error"] = str(exc)
        return result_dict


async def async_main(domains, output_file):
    results = []
    for domain in domains:
        try:
            results.append(await process_domain(domain))
        except Exception as exc:
            logging.exception("Unexpected failure for %s", domain)
            results.append({
                "domain": domain,
                "company_overview": "",
                "target_audience_icp": "",
                "contact_emails": [],
                "key_leadership_team": [],
                "data_confidence_score": 0.0,
                "source_pages": [],
                "error": str(exc),
            })

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous lead enrichment agent")
    parser.add_argument("domains", nargs="+", help="Company domains, e.g. postman.com")
    parser.add_argument("--output", default="output/output.json")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(async_main(args.domains, args.output))
