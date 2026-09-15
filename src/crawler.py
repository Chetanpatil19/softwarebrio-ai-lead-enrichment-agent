
import asyncio
import re
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
KEYWORDS = (
    "about", "company", "team", "leadership", "contact", "pricing",
    "customers", "product", "careers", "founders"
)


@dataclass
class PageContent:
    url: str
    title: str
    text: str
    emails: List[str] = field(default_factory=list)
    linkedin_urls: List[str] = field(default_factory=list)


def normalize_domain(domain: str) -> str:
    domain = domain.strip()
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain
    return domain.rstrip("/")


def same_domain(url: str, base_domain: str) -> bool:
    return urlparse(url).netloc.lower().removeprefix("www.") == base_domain.lower().removeprefix("www.")


def clean_html(html: str, max_chars: int) -> tuple[str, List[str], List[str]]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "form"]):
        tag.decompose()

    emails = sorted(set(EMAIL_RE.findall(soup.get_text(" ", strip=True))))

    linkedin_urls = sorted({
        a.get("href", "").split("?")[0]
        for a in soup.find_all("a", href=True)
        if "linkedin.com/in/" in a.get("href", "")
    })

    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text[:max_chars], emails, linkedin_urls


def score_link(url: str, anchor: str) -> int:
    value = f"{url} {anchor}".lower()
    return sum(3 for kw in KEYWORDS if kw in value)


async def crawl_domain(domain: str, max_pages: int, timeout_ms: int, max_chars: int, headless: bool) -> List[PageContent]:
    base = normalize_domain(domain)
    parsed = urlparse(base)
    host = parsed.netloc.removeprefix("www.")
    queue = [(base, 100)]
    visited = set()
    results: List[PageContent] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="SoftwareBrio-AI-Agent/1.0 (educational assessment)"
        )
        page = await context.new_page()

        while queue and len(results) < max_pages:
            queue.sort(key=lambda x: x[1], reverse=True)
            url, _ = queue.pop(0)
            if url in visited or not same_domain(url, host):
                continue
            visited.add(url)

            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if not response or response.status >= 400:
                    continue

                await page.wait_for_timeout(700)
                html = await page.content()
                text, emails, linkedin_urls = clean_html(html, max_chars)
                title = await page.title()

                if text:
                    results.append(PageContent(url, title, text, emails, linkedin_urls))

                links = await page.locator("a[href]").evaluate_all(
                    """els => els.map(a => ({
                        href: a.href,
                        text: (a.innerText || a.textContent || '').trim()
                    }))"""
                )

                for item in links:
                    href = item.get("href", "")
                    anchor = item.get("text", "")
                    if not href.startswith(("http://", "https://")):
                        continue
                    if same_domain(href, host) and href not in visited:
                        queue.append((href.split("#")[0], score_link(href, anchor)))

            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue

        await browser.close()

    return results
