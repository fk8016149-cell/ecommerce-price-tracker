import urllib.robotparser
from urllib.parse import urlparse
import httpx
from config import config

# Cache parsers per domain to avoid re-fetching robots.txt repeatedly
_robots_cache = {}

def get_domain_robots_url(target_url: str) -> str:
    """Extracts the base scheme://host and appends /robots.txt."""
    parsed = urlparse(target_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

def can_fetch_url(target_url: str, user_agent: str = None) -> tuple[bool, str]:
    """
    Checks robots.txt compliance to ensure ethical and legal scraping.
    Returns: (is_allowed: bool, reason: str)
    """
    if not config.ENFORCE_ROBOTS_TXT:
        return True, "Robots.txt check bypassed via configuration."

    user_agent = user_agent or config.USER_AGENT
    parsed = urlparse(target_url)
    netloc = parsed.netloc

    if not netloc:
        return False, "Invalid URL format."

    # Return cached parser if available
    if netloc in _robots_cache:
        rp = _robots_cache[netloc]
    else:
        robots_url = get_domain_robots_url(target_url)
        rp = urllib.robotparser.RobotFileParser()
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                resp = client.get(robots_url, headers={"User-Agent": user_agent})
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                elif resp.status_code in (401, 403):
                    # Access denied to robots.txt -> Respect site's privacy
                    return False, f"Target domain disallowed access to robots.txt (HTTP {resp.status_code})."
                else:
                    # 404 means no robots.txt file exists -> Allowed by default
                    rp.allow_all = True
            _robots_cache[netloc] = rp
        except Exception as e:
            # If robots.txt cannot be fetched due to network issue, fail safely or allow with warning
            return True, f"Could not fetch robots.txt ({e}), proceeding with polite delay."

    # Test permissions for our user agent on the specific path
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"

    allowed = rp.can_fetch(user_agent, target_url) or rp.can_fetch("*", target_url)
    if allowed:
        return True, "Allowed by website's robots.txt policy."
    else:
        return False, f"Scraping '{path}' is explicitly DISALLOWED by {netloc}/robots.txt."

