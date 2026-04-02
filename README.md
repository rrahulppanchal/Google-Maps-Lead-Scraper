# Google Maps Lead Scraper

A Python tool that scrapes business leads from Google Maps for CRM sales outreach. Enter a search query like "best salons in ahmedabad", and it extracts business names, phone numbers, emails, websites, and more — exported as a clean CSV ready for your CRM.

## Features

- **AI Query Refinement** — Uses OpenAI GPT to optimize your search query for better Google Maps results
- **Google Maps Scraping** — Playwright-based browser automation extracts business listings
- **Email Enrichment** — Visits business websites to find email addresses and contact names
- **CSV Export** — Output formatted as `name, email, phone, company, status, notes`
- **Streamlit Web UI** — Simple dashboard with progress tracking and one-click CSV download

## Prerequisites

- Python 3.10 or higher
- Google Chrome or Chromium (installed automatically by Playwright)
- OpenAI API key (optional — for AI query refinement)

## Setup

### Windows

```bash
# 1. Clone the repository
git clone <repo-url>
cd scrapper

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browser
python -m playwright install chromium

# 5. (Optional) Copy and fill in your OpenAI API key
copy .env.example .env
```

### macOS / Linux

```bash
# 1. Clone the repository
git clone <repo-url>
cd scrapper

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browser and system dependencies
python -m playwright install chromium
python -m playwright install-deps

# 5. (Optional) Copy and fill in your OpenAI API key
cp .env.example .env
```

## Running the App

### Windows

```bash
venv\Scripts\activate
python -m streamlit run app.py
```

### macOS / Linux

```bash
source venv/bin/activate
python -m streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

## Usage

1. Enter your **OpenAI API key** in the sidebar (optional — enables smarter searches)
2. Type a search query like `salons in ahmedabad` or `restaurants in mumbai`
3. Set the **Max Results** slider (5–100)
4. Click **Scrape**
5. Wait for the scraper to finish (progress is shown in real-time)
6. View results in the table and click **Download CSV**

## CSV Output Format

| name | email | phone | company | status | notes |
|------|-------|-------|---------|--------|-------|
| LS Salon Academy | info@lssalonacademy.com | 098240 87868 | LS Salon Academy | lead | Rating: 4.8 \| Category: Hairdresser |

## Project Structure

```
scrapper/
├── app.py                        # Streamlit web UI
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore
└── scraper/
    ├── __init__.py
    ├── query_refiner.py          # OpenAI GPT query optimization
    ├── maps_scraper.py           # Subprocess launcher for the worker
    ├── _scraper_worker.py        # Playwright Google Maps scraper (runs in subprocess)
    ├── data_enricher.py          # Website email/contact extraction
    └── exporter.py               # CSV export
```

## Troubleshooting

### `playwright` is not recognized

Use `python -m playwright install chromium` instead of `playwright install chromium`.

### Scraper returns 0 results

- Google Maps may show a consent/cookie page in some regions. Try running with `headless=False` in `_scraper_worker.py` to debug visually.
- Ensure Chromium is installed: `python -m playwright install chromium`

### Encoding errors on Windows

The scraper uses UTF-8 encoding. If you see encoding errors, run with:

```bash
set PYTHONUTF8=1
python -m streamlit run app.py
```

### macOS: Playwright system dependencies

On macOS, if Chromium fails to launch, install system dependencies:

```bash
python -m playwright install-deps
```

## License

MIT
