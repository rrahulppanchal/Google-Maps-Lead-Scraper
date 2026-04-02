from datetime import datetime

import streamlit as st

from scraper.query_refiner import refine_query
from scraper.maps_scraper import scrape_google_maps
from scraper.data_enricher import enrich_businesses
from scraper.exporter import to_dataframe, to_csv_bytes

st.set_page_config(page_title="Scraper", page_icon="🗺️", layout="wide")

st.title("Scraper")
st.caption("Just find data for the you usecase")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for AI query refinement")
    max_results = st.slider("Max Results", min_value=5, max_value=100, value=20, step=5)
    use_ai_refine = st.checkbox("Use AI to refine search query", value=True)
    st.divider()
    st.markdown("**How it works:**")
    st.markdown(
        "1. Enter a search query\n"
        "2. AI refines it for Google Maps\n"
        "3. Playwright scrapes business listings\n"
        "4. Websites are visited for emails\n"
        "5. Download leads as CSV"
    )

# --- Main area ---
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input(
        "Search Query",
        placeholder="e.g., best salons in ahmedabad, restaurants in mumbai",
    )
with col2:
    st.write("")  # Spacing
    st.write("")
    scrape_btn = st.button("🔍 Scrape", type="primary", use_container_width=True)


def run_scraper():
    status = st.status("Starting scraper...", expanded=True)
    progress_bar = st.progress(0)

    # Step 1: Refine query
    if use_ai_refine and api_key:
        status.update(label="Refining search query with AI...")
        try:
            refined_queries = refine_query(search_query, api_key)
            st.info(f"**AI-refined queries:** {', '.join(refined_queries)}")
            main_query = refined_queries[0] if refined_queries else search_query
        except Exception as e:
            st.warning(f"AI refinement failed ({e}), using original query.")
            main_query = search_query
    else:
        main_query = search_query
        if use_ai_refine and not api_key:
            st.warning("No API key provided. Using original query without AI refinement.")

    progress_bar.progress(10)

    # Step 2: Scrape Google Maps
    status.update(label=f"Scraping Google Maps for: {main_query}")
    scrape_log = st.empty()

    def scrape_progress(msg):
        scrape_log.text(msg)

    businesses = scrape_google_maps(main_query, max_results=max_results, progress_callback=scrape_progress)

    progress_bar.progress(60)

    if not businesses:
        status.update(label="No results found.", state="error")
        st.error("No businesses found. Try a different search query.")
        return

    st.success(f"Found **{len(businesses)}** businesses from Google Maps")

    # Step 3: Enrich data
    status.update(label="Enriching data (visiting websites for emails)...")
    enrich_log = st.empty()

    def enrich_progress(msg):
        enrich_log.text(msg)

    enriched = enrich_businesses(businesses, progress_callback=enrich_progress)
    progress_bar.progress(90)

    # Step 4: Display results
    status.update(label="Done!", state="complete")
    progress_bar.progress(100)

    df = to_dataframe(enriched)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Stats
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Leads", len(df))
    col_b.metric("With Email", len(df[df["email"] != ""]))
    col_c.metric("With Phone", len(df[df["phone"] != ""]))

    # Download
    csv_bytes = to_csv_bytes(enriched)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="📥 Download CSV",
        data=csv_bytes,
        file_name=f"leads_{timestamp}.csv",
        mime="text/csv",
        type="primary",
    )


if scrape_btn:
    if not search_query.strip():
        st.error("Please enter a search query.")
    else:
        run_scraper()
