# Google Maps Lead Scraper

## Project Overview

A Streamlit web app that scrapes business lead information (name, phone, email, website) from Google Maps. It uses AI-powered query refinement and Playwright for browser automation.

## Tech Stack

- **Language:** Python 3.12
- **UI Framework:** Streamlit (runs on port 5000)
- **Browser Automation:** Playwright (using system Chromium)
- **AI Integration:** OpenAI GPT API (optional, for query refinement)
- **Data Processing:** Pandas, BeautifulSoup4, Requests

## Project Structure

```
app.py                   # Main Streamlit application entry point
requirements.txt         # Python dependencies
scraper/
  __init__.py
  query_refiner.py       # OpenAI-based query refinement
  maps_scraper.py        # Subprocess orchestrator for scraping
  _scraper_worker.py     # Playwright worker script (runs in subprocess)
  data_enricher.py       # Website crawling for email discovery
  exporter.py            # DataFrame/CSV export utilities
```

## Key Configuration

- Streamlit runs on `0.0.0.0:5000` with `--server.headless true`
- Playwright uses the system Chromium (`chromium-browser`) instead of a bundled browser
- The scraper worker runs in a separate subprocess to avoid asyncio conflicts with Streamlit

## Environment Variables

- `OPENAI_API_KEY` — Optional. Used for AI query refinement. Can also be entered in the app UI.

## Running

The app starts via the "Start application" workflow:
```
streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
```

## Deployment

Configured as a VM deployment (always-running) since it uses browser automation with Playwright.
