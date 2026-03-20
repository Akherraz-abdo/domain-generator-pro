import streamlit as st
import pandas as pd
import subprocess
import os

# --- Step 1: Initialize Playwright ---
# This must run before we try to use Playwright
def ensure_playwright_browsers():
    try:
        # Check if chromium is already there
        import playwright
        # We try to install only if necessary to save time/memory
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Browser installation failed: {e}")

if 'browser_ready' not in st.session_state:
    with st.spinner("Setting up browser engine..."):
        ensure_playwright_browsers()
        st.session_state['browser_ready'] = True

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# --- Step 2: The UI ---
st.title("🔍 Expired Domain Finder")

ed_user = st.sidebar.text_input("Username")
ed_pass = st.sidebar.text_input("Password", type="password")
query = st.text_input("Keyword Search")

def scrape(user, password, q):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page = context.new_page()
        stealth_sync(page)

        try:
            # Login
            page.goto("https://www.expireddomains.net/login/")
            page.fill('input[name="login"]', user)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)

            # Search
            page.goto(f"https://www.expireddomains.net/domain-name-search/?q={q}")
            
            if page.locator("table.base1").is_visible():
                rows = page.locator("table.base1 tr").all()
                data = []
                for row in rows[1:21]: # Get top 20
                    cols = row.locator("td").all_inner_texts()
                    if len(cols) > 5:
                        data.append({"Domain": cols[0], "Backlinks": cols[1], "Status": cols[-1]})
                browser.close()
                return data
            else:
                browser.close()
                return "Blocked or No Results"
        except Exception as e:
            browser.close()
            return str(e)

if st.button("Run Search"):
    if not ed_user or not ed_pass:
        st.warning("Enter login info.")
    else:
        with st.spinner("Searching..."):
            res = scrape(ed_user, ed_pass, query)
            if isinstance(res, list):
                st.table(res)
            else:
                st.error(f"Result: {res}")
