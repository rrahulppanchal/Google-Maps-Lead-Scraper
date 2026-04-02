import json
import os
import subprocess
import sys


def scrape_google_maps(
    query: str,
    max_results: int = 20,
    progress_callback=None,
) -> list[dict]:
    """
    Scrape Google Maps by running the scraper in a separate subprocess
    to avoid Streamlit/Windows asyncio event loop conflicts.
    """
    if progress_callback:
        progress_callback("Launching scraper...")

    script_path = os.path.join(os.path.dirname(__file__), "_scraper_worker.py")

    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        result = subprocess.run(
            [sys.executable, "-X", "utf8", script_path, query, str(max_results)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=env,
            encoding="utf-8",
            errors="replace",
        )

        # Show stderr progress in callback
        if result.stderr and progress_callback:
            lines = result.stderr.strip().split("\n")
            for line in lines[-5:]:  # show last 5 log lines
                progress_callback(line.replace("[INFO] ", ""))

        if result.returncode != 0 and not result.stdout.strip():
            if progress_callback:
                progress_callback(f"Scraper error: {result.stderr[-500:]}")
            return []

        # Find the JSON line in stdout (last line starting with [)
        output = result.stdout.strip()
        if not output:
            if progress_callback:
                progress_callback("No output from scraper")
            return []

        lines = output.split("\n")
        json_line = ""
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("["):
                json_line = line
                break

        if not json_line:
            if progress_callback:
                progress_callback("No results parsed from scraper output")
            return []

        businesses = json.loads(json_line)

        if progress_callback:
            progress_callback(f"Scraped {len(businesses)} businesses successfully")

        return businesses

    except subprocess.TimeoutExpired:
        if progress_callback:
            progress_callback("Scraper timed out after 5 minutes")
        return []
    except Exception as e:
        if progress_callback:
            progress_callback(f"Scraper failed: {e}")
        return []
