import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time

st.set_page_config(page_title="Free Expired Domain Scraper", layout="wide")
st.title("🔍 Advanced Expired Domain Finder")

# --- Sidebar ---
st.sidebar.header("Login Credentials")
ed_user = st.sidebar.text_input("Username")
ed_pass = st.sidebar.text_input("Password", type="password")

def scrape_expired_domains(user, password, query):
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Apply stealth to bypass Cloudflare
        stealth_sync(page)

        try:
            # 1. Login
            st.info("Logging in...")
            page.goto("https://www.expireddomains.net/login/", wait_until="networkidle")
            page.fill('input[name="login"]', user)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            
            # Wait to see if login was successful
            page.wait_for_timeout(3000)
            
            # 2. Search
            st.info(f"Searching for '{query}'...")
            search_url = f"https://www.expireddomains.net/domain-name-search/?q={query}"
            page.goto(search_url, wait_until="networkidle")
            
            # 3. Parse Table
            # Look for the table with class 'base1'
            if page.locator("table.base1").is_visible():
                rows = page.locator("table.base1 tr").all()
                data = []
                
                # Headers are in the first row
                for row in rows[1:]:  # Skip header
                    cols = row.locator("td").all_inner_texts()
                    if len(cols) > 5:
                        data.append({
                            "Domain": cols[0],
                            "Backlinks": cols[1],
                            "Birth": cols[3],
                            "Status": cols[-1]
                        })
                
                browser.close()
                return data
            else:
                browser.close()
                return "No Table Found"
                
        except Exception as e:
            browser.close()
            return f"Error: {str(e)}"

# --- UI Logic ---
query = st.text_input("Keyword", placeholder="e.g. crypto")

if st.button("Start Scraping"):
    if not ed_user or not ed_pass:
        st.error("Please provide credentials.")
    else:
        with st.spinner("Bypassing Cloudflare (this may take 15-30 seconds)..."):
            results = scrape_expired_domains(ed_user, ed_pass, query)
            
            if isinstance(results, list):
                st.success(f"Success! Found {len(results)} domains.")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                st.download_button("Download CSV", df.to_csv(index=False), "domains.csv")
            else:
                st.error(f"Failed: {results}")

st.info("💡 Tip: If it fails, try logging into ExpiredDomains.net in your own browser first to ensure your account isn't locked.")
