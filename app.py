import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

st.set_page_config(page_title="Expired Domain Finder", layout="wide")
st.title("🔍 Expired Domain Search")

# Credentials
st.sidebar.header("Login Credentials")
ed_user = st.sidebar.text_input("Username")
ed_pass = st.sidebar.text_input("Password", type="password")

def run_scraper(user, password, query):
    # This command is needed ONLY the first time or if binaries are missing
    import subprocess
    subprocess.run(["playwright", "install", "chromium"])
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a realistic User Agent is critical
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)

        try:
            # 1. Login
            page.goto("https://www.expireddomains.net/login/", wait_until="domcontentloaded")
            page.fill('input[name="login"]', user)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000) # Wait for login to process

            # 2. Search
            search_url = f"https://www.expireddomains.net/domain-name-search/?q={query}"
            page.goto(search_url, wait_until="networkidle")
            
            # 3. Extract Data
            if page.locator("table.base1").is_visible():
                rows = page.locator("table.base1 tr").all()
                data = []
                for row in rows[1:]: # Skip header
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
                # If we get here, Cloudflare likely blocked the cloud IP
                content = page.content()
                browser.close()
                if "Cloudflare" in content or "Verify you are human" in content:
                    return "BLOCKED_BY_CLOUDFLARE"
                return "NO_RESULTS"

        except Exception as e:
            browser.close()
            return f"Error: {str(e)}"

# UI
query = st.text_input("Enter Keyword")
if st.button("Search"):
    if not ed_user or not ed_pass:
        st.error("Enter login details in the sidebar.")
    else:
        with st.spinner("Accessing ExpiredDomains.net..."):
            result = run_scraper(ed_user, ed_pass, query)
            
            if result == "BLOCKED_BY_CLOUDFLARE":
                st.error("Cloudflare detected the Streamlit server. This happens because many people use these servers for scraping.")
                st.info("Try running this locally on your own computer instead of Streamlit Cloud.")
            elif result == "NO_RESULTS":
                st.warning("No domains found for this keyword.")
            elif isinstance(result, list):
                st.success(f"Found {len(result)} domains!")
                st.dataframe(pd.DataFrame(result))
            else:
                st.error(result)
