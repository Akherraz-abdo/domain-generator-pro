import streamlit as st
import requests
import re
import whois
import socket
import pandas as pd
from collections import Counter

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #2ecc71; color: white; border-radius: 8px; font-weight: bold; height: 3em; }
    .available-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 8px solid #2ecc71;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .domain-text { font-size: 22px; color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 KASMI DOMAIN NEWS & FREE VERIFIER")
st.write("Trending News Aggregator + Built-in WHOIS Availability Checker (No API Required)")

# --- SIDEBAR: NEWS API KEYS ---
with st.sidebar:
    st.header("🔑 News API Keys")
    gn_key = st.text_input("GNews Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    napi_key = st.text_input("NewsAPI Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")
    m_key = st.text_input("MediaStack Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
    curr_key = st.text_input("Currents Key", value=st.secrets.get("CURRENTS_KEY", ""), type="password")

    st.header("⚙️ Domain Settings")
    tld = st.selectbox("Extension", ["com", "ai", "io", "net", "org", "biz"])
    max_checks = st.slider("Max Availability Checks", 5, 20, 10, help="WHOIS checking takes time, keep this low for speed.")

# --- NEWS AGGREGATOR ---
def fetch_news():
    headlines = []
    # Try all 4 sources
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
            r = requests.get(f"http://api.mediastack.com/v1/news?access_key={m_key}&languages=en", timeout=5).json()
            headlines.extend([a['title'] for a in r.get('data', [])])
        except: pass
    if curr_key:
        try:
            headers = {'Authorization': curr_key}
            r = requests.get("https://api.currentsapi.services/v1/latest-news?language=en&category=technology", headers=headers, timeout=5).json()
            headlines.extend([a['title'] for a in r.get('news', [])])
        except: pass
    return list(set(headlines))

# --- DOMAIN AVAILABILITY LOGIC (No API Key Needed) ---
def is_domain_available(domain):
    """
    Checks availability using DNS resolution + WHOIS lookup.
    No API Key required.
    """
    # Step 1: DNS Check (Very fast)
    try:
        socket.gethostbyname(domain)
        return False # If it resolves to an IP, it's taken.
    except socket.gaierror:
        # Step 2: WHOIS Check (Double check if DNS fails)
        try:
            w = whois.whois(domain)
            # If WHOIS has no registrar or creation date, it's likely available
            if not w.registrar and not w.creation_date:
                return True
            return False
        except Exception:
            # If WHOIS errors out, it's often because the domain doesn't exist
            return True

# --- KEYWORD & CANDIDATE GENERATION ---
def get_domain_candidates(headlines):
    text = " ".join(headlines).lower()
    words = re.findall(r'\b[a-z]{4,}\b', text)
    stop_words = {'today', 'latest', 'news', 'with', 'from', 'that', 'this', 'says'}
    keywords = [w for w in words if w not in stop_words]
    top = [item[0] for item in Counter(keywords).most_common(max_checks)]
    
    # Create combinations
    candidates = []
    for i in range(len(top)):
        candidates.append(f"{top[i]}.{tld}") # Single word
        if i < len(top) - 1:
            candidates.append(f"{top[i]}{top[i+1]}.{tld}") # Combo
    return list(set(candidates))

# --- MAIN UI ---
if st.button("🚀 SCAN NEWS & FIND AVAILABLE DOMAINS"):
    if not any([gn_key, napi_key, m_key, curr_key]):
        st.error("Please enter at least one News API Key in the sidebar.")
    else:
        with st.status("Searching the Web...", expanded=True) as status:
            st.write("📡 Fetching news from 4 sources...")
            news_list = fetch_news()
            
            if not news_list:
                st.error("Could not fetch news headlines.")
            else:
                st.write(f"✅ Found {len(news_list)} headlines.")
                candidates = get_domain_candidates(news_list)
                
                st.write(f"🔎 Verifying {len(candidates[:max_checks])} domains via WHOIS...")
                available_domains = []
                
                # Progress Bar for checking
                progress_bar = st.progress(0)
                for i, d in enumerate(candidates[:max_checks]):
                    if is_domain_available(d):
                        available_domains.append(d)
                    progress_bar.progress((i + 1) / max_checks)
                
                status.update(label="Scanning Complete!", state="complete")

                # --- RESULTS DISPLAY ---
                if available_domains:
                    st.success(f"💎 Found {len(available_domains)} Available Domains!")
                    for d in available_domains:
                        st.markdown(f"""
                        <div class="available-card">
                            <span class="domain-text">{d}</span><br>
                            <small>✅ Available for registration</small><br><br>
                            <a href="https://www.namecheap.com/domains/registration-results/?domain={d}" target="_blank">Register Now →</a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No available domains found. Trending keywords are highly competitive today.")

st.divider()
st.caption("KASMI DOMAIN NEWS - WHOIS Verifier Edition | No API required for checking.")
