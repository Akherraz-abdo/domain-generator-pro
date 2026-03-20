import streamlit as st
import os
import subprocess
import sys

# --- BOOTSTRAP: Ensure Playwright is installed ---
def install_playwright():
    try:
        import playwright
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "playwright-stealth"])
    
    # Check if browsers are installed, if not, install chromium
    # Streamlit Cloud needs this to run playwright
    subprocess.run(["playwright", "install", "chromium"])

# Run the installer
if 'playwright_installed' not in st.session_state:
    with st.spinner("Initializing Browser Engine (this may take a minute)..."):
        install_playwright()
        st.session_state['playwright_installed'] = True

# --- Now Import Everything ---
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import pandas as pd

st.set_page_config(page_title="Free Expired Domain Scraper", layout="wide")
st.title("🔍 Advanced Expired Domain Finder")

# --- Sidebar ---
st.sidebar.header("Login Credentials")
ed_user = st.sidebar.text_input("Username")
ed_pass = st.sidebar.text_input("Password", type="password")

def scrape_expired_domains(user, password, query):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Apply stealth
        stealth_sync(page)

        try:
            # 1. Login
            page.goto("https://www.expireddomains.net/login/", wait_until="networkidle")
            page.fill('input[name="login"]', user)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
            
            # 2. Search
            search_url = f"https://www.expireddomains.net/domain-name-search/?q={query}"
            page.goto(search_url, wait_until="networkidle")
            
            # 3. Check for Cloudflare/Table
            if page.locator("table.base1").is_visible():
                rows = page.locator("table.base1 tr").all()
                data = []
                for row in rows[1:]:
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
                # Debugging: Save screenshot to see what went wrong
                page.screenshot(path="error.png")
                browser.close()
                return "Blocked by Cloudflare or No results found."
                
        except Exception as e:
            browser.close()
            return f"Error: {str(e)}"

# --- UI Logic ---
query = st.text_input("Keyword", placeholder="e.g. tech")

if st.button("Start Scraping"):
    if not ed_user or not ed_pass:
        st.error("Please provide credentials in the sidebar.")
    else:
        with st.spinner("Scanning ExpiredDomains.net..."):
            results = scrape_expired_domains(ed_user, ed_pass, query)
            
            if isinstance(results, list):
                st.success(f"Found {len(results)} domains.")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                st.download_button("Download CSV", df.to_csv(index=False), "domains.csv")
            else:
                st.error(results)
                if os.path.exists("error.png"):
                    st.image("error.png", caption="What the scraper saw")
