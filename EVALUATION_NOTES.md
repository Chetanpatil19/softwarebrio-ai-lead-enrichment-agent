
# How this maps to the rubric

## 30% Agent & Scraping Architecture
- Playwright headless Chromium
- JavaScript-rendered pages supported
- Homepage + ranked relevant internal links
- Same-domain restriction
- Bounded crawl size

## 25% LLM & Structured Output
- Pydantic schema
- OpenAI structured parsing
- Clean text instead of raw HTML
- Explicit anti-hallucination extraction rules
- Source-page tracking

## 20% Error Handling & Resilience
- HTTP errors
- Playwright timeout handling
- Missing/empty pages
- LLM failure fallback
- Per-domain isolation

## 15% Code Quality & Documentation
- Separate crawler, schema, config, LLM and fallback modules
- Type-oriented dataclasses/Pydantic models
- README and environment template

## 10% Loom
- Short walkthrough script supplied in LOOM_SCRIPT.txt
