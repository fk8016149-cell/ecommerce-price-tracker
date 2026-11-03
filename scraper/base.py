import time
from dataclasses import dataclass
from typing import Optional
import httpx
from config import config
from robots_checker import can_fetch_url

@dataclass
class ScrapeResult:
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: str = "PKR"
    in_stock: bool = True
    success: bool = False
    error: Optional[str] = None

class BaseScraper:
    """
    Ethical Base Scraper:
    1. Checks robots.txt permission before sending request.
    2. Enforces polite delay between requests (avoids overloading servers).
    3. Uses transparent, courteous headers.
    """
    def __init__(self, delay_seconds: float = None):
        self.delay_seconds = delay_seconds if delay_seconds is not None else config.SCRAPE_DELAY_SECONDS
        self._last_request_time = 0.0

    def _wait_politely(self):
        """Enforces minimum polite time gap between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_time = time.time()

    def fetch_html(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Fetches HTML content with ethical guardrails.
        Returns: (html_content, error_message)
        """
        # 1. Ethical Check: Robots.txt validation
        allowed, reason = can_fetch_url(url, user_agent=config.USER_AGENT)
        if not allowed:
            return None, f"Legal/Ethical rejection: {reason}"

        # 2. Polite Rate Limiting Delay
        self._wait_politely()

        # 3. HTTP Request with standard headers
        headers = {
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
            "DNT": "1",  # Do Not Track signal
        }

        try:
            with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
                response = client.get(url)
                if response.status_code == 200:
                    return response.text, None
                elif response.status_code == 404:
                    return None, "Product page not found (HTTP 404)."
                elif response.status_code == 403:
                    return None, "Access denied (HTTP 403). Scraping restricted by site owner."
                else:
                    return None, f"Server returned HTTP status {response.status_code}."
        except httpx.TimeoutException:
            return None, "Request timed out after 15 seconds."
        except Exception as e:
            return None, f"Connection error: {str(e)}"

