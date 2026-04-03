import re

import requests
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

# Common junk emails to filter out
JUNK_DOMAINS = {"example.com", "sentry.io", "wixpress.com", "googleapis.com", "w3.org", "schema.org"}

# Words that are NOT person names — nav links, page sections, junk
JUNK_NAMES = {
    "us", "blog", "career", "careers", "contact", "about", "home", "faq",
    "shipping", "returns", "privacy", "policy", "terms", "login", "signup",
    "shop", "store", "products", "services", "gallery", "portfolio",
    "menu", "help", "support", "news", "events", "team", "our", "the",
    "best", "top", "premium", "welcome", "click", "here", "read", "more",
    "view", "see", "all", "new", "old", "get", "buy", "sell", "free",
    "sponsored", "advertisement", "ad", "promo", "offer", "discount",
}


def _is_valid_email(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    if domain in JUNK_DOMAINS:
        return False
    if email.endswith((".png", ".jpg", ".svg", ".gif", ".webp")):
        return False
    return True


def _extract_emails_from_html(html: str) -> list[str]:
    raw = EMAIL_REGEX.findall(html)
    return list({e for e in raw if _is_valid_email(e)})


def _is_valid_person_name(name: str) -> bool:
    """Check if a string looks like an actual person's name."""
    name = name.strip()
    if not name:
        return False

    words = name.lower().split()

    # Must be 2-4 words (first + last, or first + middle + last)
    if len(words) < 2 or len(words) > 4:
        return False

    # No word should be a known junk/nav word
    for w in words:
        if w in JUNK_NAMES:
            return False

    # Each word should be alphabetic and start with uppercase in original
    original_words = name.split()
    for w in original_words:
        if not re.match(r"^[A-Z][a-z]+$", w):
            return False

    # Name shouldn't contain business-like words
    business_words = {"salon", "studio", "shop", "store", "ltd", "pvt", "inc", "llc", "corp"}
    if any(w in business_words for w in words):
        return False

    return True


def _extract_contact_name(soup: BeautifulSoup) -> str:
    """Try to find an owner or contact person name from the page."""
    # Remove nav, header, footer, script, style elements to avoid junk
    for tag in soup.find_all(["nav", "header", "footer", "script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Strict patterns: "Owner: Firstname Lastname" etc.
    patterns = [
        r"(?:owner|founder|ceo|managing\s+director|proprietor)\s*[:\-–]\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:founded\s+by|owned\s+by|managed\s+by|run\s+by)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip()
            if _is_valid_person_name(candidate):
                return candidate

    return ""


def _first_name_from_email(email: str) -> str:
    """Try to extract a first name from an email address like john.doe@company.com or john@company.com."""
    if not email:
        return ""

    local = email.split("@")[0].lower()

    # Skip generic emails
    generic = {"info", "contact", "hello", "admin", "support", "sales", "enquiry",
               "enquiries", "help", "office", "mail", "service", "team", "hr",
               "marketing", "billing", "sourcing", "store", "shop", "booking", "storemgr"}
    if local in generic:
        return ""

    # Check for firstname.lastname or firstname_lastname pattern — take first part
    parts = re.split(r"[._\-]", local)
    first = parts[0]
    if first.isalpha() and len(first) > 1:
        return first.capitalize()

    return ""


def _scrape_website(url: str, timeout: int = 10) -> dict:
    """Visit a business website to extract emails and contact names."""
    result = {"emails": [], "contact_name": ""}

    if not url:
        return result

    # Ensure URL has protocol
    if not url.startswith("http"):
        url = "https://" + url

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        result["emails"] = _extract_emails_from_html(html)
        result["contact_name"] = _extract_contact_name(soup)

        # Also try /contact and /about pages
        base_url = url.rstrip("/")
        for path in ["/contact", "/contact-us", "/about", "/about-us"]:
            try:
                r2 = requests.get(base_url + path, headers=HEADERS, timeout=8, allow_redirects=True)
                if r2.status_code == 200:
                    more_emails = _extract_emails_from_html(r2.text)
                    result["emails"].extend(more_emails)
                    if not result["contact_name"]:
                        soup2 = BeautifulSoup(r2.text, "html.parser")
                        result["contact_name"] = _extract_contact_name(soup2)
            except Exception:
                continue

        # Deduplicate emails
        result["emails"] = list(set(result["emails"]))

    except Exception:
        pass

    return result


def enrich_businesses(businesses: list[dict], progress_callback=None) -> list[dict]:
    """Enrich scraped business data with emails and contact names from their websites."""
    enriched = []

    for i, biz in enumerate(businesses):
        if progress_callback:
            progress_callback(f"Enriching {i + 1}/{len(businesses)}: {biz.get('name', 'Unknown')}")

        website_data = _scrape_website(biz.get("website", ""))

        email = website_data["emails"][0] if website_data["emails"] else ""

        # Determine first name:
        # 1. Try name extracted from website (valid person name) — take first word
        # 2. Try to derive first name from email (e.g., john.doe@company.com → John)
        # 3. Fall back to first word of the business name so it's never empty
        contact_name = website_data["contact_name"]  # already validated full name
        if contact_name:
            first_name = contact_name.split()[0]
        else:
            first_name = _first_name_from_email(email)

        # Last resort: use first word of the business name
        if not first_name:
            business_name = biz.get("name", "")
            if business_name:
                first_word = business_name.split()[0]
                # Only use it if it looks like a word (not a number/symbol)
                if first_word.replace("-", "").isalpha():
                    first_name = first_word.capitalize()

        # Build notes
        notes_parts = []
        if biz.get("rating"):
            notes_parts.append(f"Rating: {biz['rating']}")
        if biz.get("reviews"):
            notes_parts.append(f"Reviews: {biz['reviews']}")
        if biz.get("category"):
            notes_parts.append(f"Category: {biz['category']}")
        if biz.get("website"):
            notes_parts.append(f"Website: {biz['website']}")

        enriched.append(
            {
                "firstName": first_name,
                "email": email,
                "phone": biz.get("phone", ""),
                "address": biz.get("address", ""),
                "company": biz.get("name", ""),
                "status": "lead",
                "notes": " | ".join(notes_parts),
            }
        )

    return enriched
