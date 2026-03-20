import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- Page Config ---
st.set_page_config(page_title="Free Expired Domain Finder", layout="wide")
st.title("🔍 Free Expired Domain Search")

# --- Sidebar: Credentials ---
st.sidebar.header("Login Credentials")
st.sidebar.info("You must use your expireddomains.net login to see detailed data.")
ed_user = st.sidebar.text_input("Username")
ed_pass = st.sidebar.text_input("Password", type="password")

# --- Function to Scrape ---
def get_domains(user, password, query):
    # Create a scraper that bypasses Cloudflare
    scraper = cloudscraper.create_scraper()
    
    # 1. Login Logic
    login_url = "https://www.expireddomains.net/login/"
    login_data = {
        'login': user,
        'password': password,
        'redirect': '/backorder-expired-domains/'
    }
    
    # We use a session to keep the login cookies
    response = scraper.post(login_url, data=login_data)
    
    if "Login failed" in response.text:
        return "error_login"

    # 2. Search Logic
    # We search the 'Expired Domains' section with a keyword
    search_url = f"https://www.expireddomains.net/domain-name-search/?q={query}"
    response = scraper.get(search_url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Parse Table
    table = soup.find('table', class_='base1')
    if not table:
        return "no_results"

    domains = []
    rows = table.find_all('tr')[1:]  # Skip header
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 1:
            domains.append({
                "Domain": cols[0].text.strip(),
                "BL": cols[1].text.strip(), # Backlinks
                "DP": cols[2].text.strip(), # Domain Pop
                "AB": cols[3].text.strip(), # Birth year
                "Status": cols[-1].text.strip()
            })
            
    return domains

# --- UI ---
search_query = st.text_input("Enter Keyword (e.g. 'coffee')", value="")

if st.button("Find Domains"):
    if not ed_user or not ed_pass:
        st.warning("Please enter your ExpiredDomains.net username and password in the sidebar.")
    elif not search_query:
        st.warning("Please enter a keyword.")
    else:
        with st.spinner("Bypassing Cloudflare and fetching data..."):
            results = get_domains(ed_user, ed_pass, search_query)
            
            if results == "error_login":
                st.error("Login failed. Check your username/password.")
            elif results == "no_results":
                st.warning("No domains found or site structure changed.")
            elif isinstance(results, list):
                df = pd.DataFrame(results)
                st.success(f"Found {len(df)} domains!")
                st.dataframe(df, use_container_width=True)
                
                # Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "domains.csv", "text/csv")

st.markdown("---")
st.caption("Note: This tool uses `cloudscraper` to access data freely. If it stops working, the website has likely updated its security.")
