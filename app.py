import streamlit as st
import requests
import re
import xml.etree.ElementTree as ET
import pandas as pd
from collections import Counter

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS & VERIFIER", page_icon="🚀", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { background-color: #ff6600; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3em; }
    .available-box { border: 2px solid #28a745; padding: 20px; border-radius: 10px; background-color: white; margin-bottom: 15px; }
    .domain-name { color: #28a745; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 KASMI DOMAIN NEWS + VERIFIER")
st.subheader("Extract Trends from Global News & Check Namecheap Availability")

# --- SIDEBAR: ALL API KEYS ---
with st.sidebar:
    st.header("🔑 News Sources")
    gn_key = st.text_input("GNews Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    napi_key = st.text_input("NewsAPI Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")
    m_key = st.text_input("MediaStack Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
    curr_key = st.text_input("Currents Key", value=st.secrets.get("CURRENTS_KEY", ""), type="password")

    st.header("🛒 Namecheap Verifier")
    nc_user = st.text_input("Namecheap Username", value=st.secrets.get("NC_USER", ""))
    nc_api_key = st.text_input("Namecheap API Key", value=st.secrets.get("NC_API_KEY", ""), type="password")
    nc_ip = st.text_input("Your Whitelisted IP", value=st.secrets.get("NC_IP", ""))
    
    st.header("⚙️ Settings")
    tld = st.selectbox("Extension", ["com", "ai", "io", "net", "org", "co"])
    depth = st.slider("Keyword Count", 5, 20, 10)

# --- FUNCTION: FETCH NEWS FROM ALL 4 SOURCES ---
def fetch_aggregated_news():
    headlines = []
    
    if gn_key:
        try:
            r = requests.get(f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gn_key}", timeout=5).json()
            headlines.extend([a['title'] for a in r.get('articles', [])])
        except: pass
    if napi_key:
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={napi_key}", timeout=5).json()
            headlines.extend([a['title'] for a in r.get('articles', [])])
        except: pass
    if m_key:
        try:
            r = requests.get(f"http://api.mediastack.com/v1/news?access_key={m_key}&languages=en&categories=technology", timeout=5).json()
            headlines.extend([a['title'] for a in r.get('data', [])])
        except: pass
    if curr_key:
        try:
            headers = {'Authorization': curr_key}
            r = requests.get("https://api.currentsapi.services/v1/latest-news?language=en&category=technology", headers=headers, timeout=5).json()
            headlines.extend([a['title'] for a in r.get('news', [])])
        except: pass

    return list(set(headlines))

# --- FUNCTION: GENERATE DOMAIN CANDIDATES ---
def get_candidates(headlines):
    text = " ".join(headlines).lower()
    words = re.findall(r'\b[a-z]{4,}\b', text)
    stop_words = {'today', 'latest', 'news', 'with', 'from', 'that', 'this', 'will', 'says'}
    keywords = [w for w in words if w not in stop_words]
    top_keywords = [item[0] for item in Counter(keywords).most_common(depth)]
    
    candidates = []
    for i in range(len(top_keywords)):
        # Strategy 1: The Keyword itself
        candidates.append(f"{top_keywords[i]}.{tld}")
        # Strategy 2: Pair with next keyword
        if i < len(top_keywords) - 1:
            candidates.append(f"{top_keywords[i]}{top_keywords[i+1]}.{tld}")
        # Strategy 3: Trend suffix
        candidates.append(f"{top_keywords[i]}flow.{tld}")
        candidates.append(f"{top_keywords[i]}hub.{tld}")
    
    return list(set(candidates))

# --- FUNCTION: NAMECHEAP VERIFIER ---
def check_namecheap(domain_list):
    if not nc_user or not nc_api_key:
        st.error("Namecheap credentials missing!")
        return []

    # Using Sandbox for safety by default, change to api.namecheap.com for production
    url = "https://api.namecheap.com/xml.response" 
    params = {
        "ApiUser": nc_user,
        "ApiKey": nc_api_key,
        "UserName": nc_user,
        "Command": "namecheap.domains.check",
        "ClientIp": nc_ip,
        "DomainList": ",".join(domain_list[:50]) # Namecheap limit is 50
    }

    try:
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        ns = {'ns': 'http://api.namecheap.com/xml.response'}
        
        results = root.findall('.//ns:DomainCheckResult', ns)
        available = []
        for res in results:
            if res.attrib.get('Available') == 'true':
                available.append(res.attrib.get('Domain'))
        return available
    except Exception as e:
        st.error(f"Check failed: {e}")
        return []

# --- MAIN APP INTERFACE ---
if st.button("🔍 SCAN NEWS & CHECK AVAILABILITY"):
    if not any([gn_key, napi_key, m_key, curr_key]):
        st.warning("Please provide at least one News API Key.")
    elif not nc_api_key:
        st.warning("Namecheap API Key is required to filter results.")
    else:
        with st.status("Initializing Systems...", expanded=True) as status:
            # Step 1: Fetch News
            st.write("📡 Aggregating news from 4 sources...")
            news = fetch_aggregated_news()
            
            if not news:
                st.error("No news found. Check your API Keys.")
                status.update(label="Failed", state="error")
            else:
                st.write(f"✅ Found {len(news)} headlines.")
                
                # Step 2: Generate Candidates
                st.write("💡 Brainstorming domain combinations...")
                candidates = get_candidates(news)
                
                # Step 3: Namecheap Verification
                st.write(f"🔎 Checking {len(candidates)} domains on Namecheap...")
                available_only = check_namecheap(candidates)
                
                status.update(label="Scan Complete!", state="complete")

                # Step 4: Display ONLY Available
                if available_only:
                    st.success(f"🚀 Found {len(available_only)} Available Domains!")
                    for d in available_only:
                        st.markdown(f"""
                        <div class="available-box">
                            <div class="domain-name">{d}</div>
                            <p>Status: <b>AVAILABLE</b></p>
                            <a href="https://www.namecheap.com/domains/registration-results/?domain={d}" target="_blank">Register Now →</a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Zero available domains found. All trending keywords are currently taken.")

st.divider()
st.caption("KASMI DOMAIN NEWS - Integrated Verifier | No AI Required | 2026 Edition")
