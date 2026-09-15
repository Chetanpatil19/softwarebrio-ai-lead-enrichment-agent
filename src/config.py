
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_pages_per_domain: int = int(os.getenv("MAX_PAGES_PER_DOMAIN", "8"))
    page_timeout_ms: int = int(os.getenv("PAGE_TIMEOUT_MS", "20000"))
    max_chars_per_page: int = int(os.getenv("MAX_CHARS_PER_PAGE", "8000"))
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"


settings = Settings()
