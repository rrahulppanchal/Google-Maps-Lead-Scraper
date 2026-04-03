"""
Standalone Playwright scraper worker.
Runs in its own subprocess to avoid asyncio event loop conflicts with Streamlit on Windows.

Usage: python _scraper_worker.py "search query" max_results
Outputs: JSON array of business dicts to stdout (last line)
"""

import sys
import io
import json
import random
import re
import time

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from playwright.sync_api import sync_playwright


def log(msg):
    print(f"[INFO] {msg}", file=sys.stderr, flush=True)


def random_delay(min_s=1.0, max_s=2.5):
    time.sleep(random.uniform(min_s, max_s))


def scroll_results(page, target_count=20):
    """Scroll the results feed until we have enough listing links."""
    for i in range(30):  # max 30 scrolls
        links = page.query_selector_all('a[href*="/maps/place/"]')
        if len(links) >= target_count:
            log(f"Got {len(links)} links after {i+1} scrolls")
            return links

        page.evaluate(
            '() => { const f = document.querySelector(\'div[role="feed"]\'); if(f) f.scrollTop = f.scrollHeight; }'
        )
        random_delay(1.5, 2.5)

        # Check if we hit the end (no new results loaded)
        new_links = page.query_selector_all('a[href*="/maps/place/"]')
        if len(new_links) == len(links) and i > 2:
            log(f"No more results. Total: {len(new_links)}")
            return new_links

    return page.query_selector_all('a[href*="/maps/place/"]')


def extract_detail(page):
    """Extract business details from the currently open listing detail panel."""
    info = {
        "name": "",
        "phone": "",
        "address": "",
        "website": "",
        "rating": "",
        "reviews": "",
        "category": "",
    }

    try:
        # Business name — get ALL h1s, the business name is usually the last non-empty one
        h1_elements = page.query_selector_all("h1")
        for h1 in h1_elements:
            text = h1.inner_text().strip()
            if text and text != "Results":
                info["name"] = text

        # Rating
        rating_el = page.query_selector('div.F7nice span[aria-hidden="true"]')
        if rating_el:
            info["rating"] = rating_el.inner_text().strip()

        # Reviews count
        reviews_el = page.query_selector('div.F7nice span[aria-label]')
        if reviews_el:
            label = reviews_el.get_attribute("aria-label") or ""
            nums = re.findall(r"[\d,]+", label)
            if nums:
                info["reviews"] = nums[0].replace(",", "")

        # Category
        cat_el = page.query_selector('button[jsaction*="category"]')
        if cat_el:
            info["category"] = cat_el.inner_text().strip()

        # Address — button with data-item-id="address"
        addr_btn = page.query_selector('button[data-item-id="address"]')
        if addr_btn:
            aria = addr_btn.get_attribute("aria-label") or ""
            info["address"] = aria.replace("Address:", "").strip()

        # Phone — button with data-item-id starting with "phone:tel:"
        phone_btn = page.query_selector('button[data-item-id^="phone:tel:"]')
        if phone_btn:
            aria = phone_btn.get_attribute("aria-label") or ""
            info["phone"] = aria.replace("Phone:", "").strip()

        # Website — a[data-item-id="authority"]
        website_link = page.query_selector('a[data-item-id="authority"]')
        if website_link:
            info["website"] = (website_link.get_attribute("href") or "").strip()

    except Exception as e:
        log(f"Error extracting detail: {e}")

    return info


def scrape(query, max_results):
    results = []

    import shutil
    chromium_path = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")

    with sync_playwright() as p:
        launch_kwargs = dict(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path

        browser = p.chromium.launch(**launch_kwargs)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            """
        )

        page = context.new_page()

        try:
            # Use direct search URL (faster than typing)
            search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            log(f"Navigating to: {search_url}")
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

            # Wait for results feed to appear
            log("Waiting for results feed...")
            page.wait_for_selector('div[role="feed"]', timeout=15000)
            random_delay(3, 5)

            # Scroll to load enough results
            log(f"Scrolling for {max_results} results...")
            listing_links = scroll_results(page, target_count=max_results)
            log(f"Found {len(listing_links)} listing links total")

            # Process each listing
            seen_names = set()
            for i, link in enumerate(listing_links):
                if len(results) >= max_results:
                    break

                try:
                    # Get aria-label for quick name check
                    aria_name = link.get_attribute("aria-label") or ""

                    # Click to open detail panel
                    link.click()
                    random_delay(2, 3)

                    # Wait for detail panel to load
                    page.wait_for_selector('button[data-item-id="address"]', timeout=5000)
                    random_delay(0.5, 1)

                    detail = extract_detail(page)

                    if detail["name"] and detail["name"] not in seen_names:
                        seen_names.add(detail["name"])
                        results.append(detail)
                        log(f"[{len(results)}/{max_results}] {detail['name']} | Phone: {detail['phone']} | Web: {detail['website'][:40]}")

                except Exception as e:
                    log(f"Skipping listing {i}: {e}")
                    continue

        except Exception as e:
            log(f"Scraping failed: {e}")
        finally:
            browser.close()

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python _scraper_worker.py <query> <max_results>", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    max_results = int(sys.argv[2])

    log(f"Starting scrape: '{query}' (max {max_results})")
    businesses = scrape(query, max_results)
    log(f"Done. Got {len(businesses)} results.")

    # Output JSON to stdout — this is what the parent process reads
    print(json.dumps(businesses, ensure_ascii=False))
