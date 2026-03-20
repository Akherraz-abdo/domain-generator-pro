import streamlit as st
from apify_client import ApifyClient
import pandas as pd
import time

# --- Page Config ---
st.set_page_config(page_title="Expired Domain Finder", layout="wide")
st.title("🔍 Expired Domain Search Pro")

# --- Sidebar: Configuration ---
st.sidebar.header("Settings")
apify_token = st.sidebar.text_input("Apify API Token", type="password")
ed_user = st.sidebar.text_input("ExpiredDomains.net Username")
ed_pass = st.sidebar.text_input("ExpiredDomains.net Password", type="password")

# --- Main UI: Search Filters ---
col1, col2 = st.columns(2)
with col1:
    search_query = st.text_input("Keyword (e.g., 'tech', 'crypto')", value="api")
with col2:
    max_items = st.number_input("Max Domains to Fetch", min_value=1, max_value=500, value=20)

if st.button("Search Domains"):
    if not apify_token or not ed_user or not ed_pass:
        st.error("Please provide your Apify and ExpiredDomains credentials in the sidebar.")
    else:
        with st.spinner("Logging into ExpiredDomains and fetching data..."):
            try:
                # 1. Initialize Apify Client
                client = ApifyClient(apify_token)

                # 2. Prepare Actor Input
                # Note: These fields match the 'ib4ngz/expired-domains-scraper' requirements
                run_input = {
                    "username": ed_user,
                    "password": ed_pass,
                    "query": search_query,
                    "maxItems": max_items,
                    "proxyConfiguration": {"useApifyProxy": True}
                }

                # 3. Run the Actor
                run = client.actor("ib4ngz/expired-domains-scraper").call(run_input=run_input)

                # 4. Fetch Results from Dataset
                dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                
                if dataset_items:
                    df = pd.DataFrame(dataset_items)
                    
                    # Display Results
                    st.success(f"Found {len(df)} domains!")
                    
                    # Standardize columns (optional but recommended)
                    # ExpiredDomains provides: domain, bl (backlinks), ab (age), etc.
                    st.dataframe(df, use_container_width=True)
                    
                    # Download Button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", csv, "expired_domains.csv", "text/csv")
                else:
                    st.warning("No domains found for this query.")

            except Exception as e:
                st.error(f"An error occurred: {e}")

st.markdown("---")
st.caption("Built with Streamlit & Apify. Use responsibly according to ExpiredDomains.net TOS.")
