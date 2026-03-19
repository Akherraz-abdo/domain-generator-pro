import streamlit as st
import requests
import re
import whois
import socket
import trafilatura
import pandas as pd
from collections import Counter

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DEEP NEWS", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #003366; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; }
    .available-card { 
        background-color: white; padding: 20px; border-radius: 12px; border-left: 10px solid #1e88e5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;
    }
    .keyword-pill { background: #e3f2fd; color: #0d47a1; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; margin: 2px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 KASMI DEEP DOMAIN NEWS")
st.write("Aggregating 4 News APIs + Scraping Article Content for Niche Domain Discovery.")

# --- SIDEBAR: CONFIG ---
with st.sidebar:
    st.header("🔑 News API Keys")
    gn_key = st.text_input("GNews Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    napi_key = st.text_input("NewsAPI Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")
    m_key = st.text_input("MediaStack Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
    curr_key = st.text_input("Currents Key", value=st.secrets.get("CURRENTS_KEY", ""), type="password")

    st.divider()
    st.header("⚙️ Deep Scrape Settings")
    scrape_limit = st.slider("Articles to Scrape Deeply", 3, 10, 5, help="More articles = slower performance.")
    tld = st.selectbox("TLD", ["com", "ai", "io", "net", "org", "co"])
    max_domains = st.slider("Max Availability Checks", 5, 15, 8)

# --- NEWS & DEEP SCRAPING LOGIC ---
def fetch_news_urls():
    """Fetches titles and URLs from all 4 sources."""
    articles = [] # List of dicts: {'title': ..., 'url': ...}
    
    # 1. GNews
    if gn_key:
        try:
            r = requests.get(f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gn_key}", timeout=5).json()
            for a in r.get('articles', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass
    # 2. NewsAPI
    if napi_key:
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={napi_key}", timeout=5).json()
            for a in r.get('articles', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass
    # 3. MediaStack
    if m_key:
        try:
            r = requests.get(f"http://api.mediastack.com/v1/news?access_key={m_key}&languages=en&limit=10", timeout=5).json()
            for a in r.get('data', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass
    # 4. Currents
    if curr_key:
        try:
            headers = {'Authorization': curr_key}
            r = requests.get("https://api.currentsapi.services/v1/latest-news?language=en&category=technology", headers=headers, timeout=5).json()
            for a in r.get('news', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass
    
    return articles

def scrape_article_content(url):
    """Visits a URL and extracts the main text content."""
    try:
        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded)
    except:
        return ""

# --- AVAILABILITY LOGIC (WHOIS) ---
def is_available(domain):
    try:
        # Check DNS first (Fast)
        socket.gethostbyname(domain)
        return False
    except:
        try:
            # Check WHOIS (Accurate)
            w = whois.whois(domain)
            return not w.registrar and not w.creation_date
        except:
            return True

# --- KEYWORD ENGINE ---
def extract_deep_keywords(text):
    words = re.findall(r'\b[a-z]{5,12}\b', text.lower()) # Focus on 5-12 letter words
    stop_words = {'today', 'latest', 'news', 'people', 'would', 'could', 'should', 'about', 'their', 'there'}
    filtered = [w for w in words if w not in stop_words]
    return [item[0] for item in Counter(filtered).most_common(20)]

# --- MAIN APP ---
if st.button("🔍 START DEEP ANALYTICS & FIND DOMAINS"):
    if not any([gn_key, napi_key, m_key, curr_key]):
        st.error("Please add at least one News API Key.")
    else:
        with st.status("Initializing Deep Scrape...", expanded=True) as status:
            # Step 1: Get URLs
            st.write("📡 Collecting headlines and article links...")
            articles = fetch_news_urls()
            
            if not articles:
                st.error("No news found.")
            else:
                # Step 2: Deep Scrape
                st.write(f"📝 Deep-fetching content from top {scrape_limit} articles...")
                combined_text = ""
                for i, art in enumerate(articles[:scrape_limit]):
                    st.write(f"  → Scraping: {art['title'][:50]}...")
                    content = scrape_article_content(art['url'])
                    combined_text += f" {art['title']} {content}"
                
                # Step 3: Extract Keywords
                st.write("🧠 Analyzing text for high-value keywords...")
                keywords = extract_deep_keywords(combined_text)
                
                # Step 4: Generate & Check
                st.write(f"🔎 Verifying {max_domains} domains via WHOIS...")
                available_ones = []
                
                # Generate combinations
                candidates = []
                for i in range(len(keywords)):
                    candidates.append(f"{keywords[i]}.{tld}")
                    if i < len(keywords) - 1:
                        candidates.append(f"{keywords[i]}{keywords[i+1]}.{tld}")
                
                # Perform Check
                for d in candidates[:max_domains]:
                    if is_available(d):
                        available_ones.append(d)
                
                status.update(label="Deep Analytics Complete!", state="complete")

        # --- OUTPUT ---
        st.write("### 🔥 Trending Keywords Found (Deep Scrape):")
        kw_html = "".join([f"<span class='keyword-pill'>{k}</span>" for k in keywords[:10]])
        st.markdown(kw_html, unsafe_allow_html=True)

        st.divider()

        if available_ones:
            st.success(f"💎 Found {len(available_ones)} Available Domains!")
            for d in available_ones:
                st.markdown(f"""
                <div class="available-card">
                    <span style="font-size: 22px; color: #1e88e5; font-weight: bold;">{d}</span><br>
                    <small>✅ Status: UNREGISTERED</small><br><br>
                    <a href="https://www.namecheap.com/domains/registration-results/?domain={d}" target="_blank" 
                       style="background: #1e88e5; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px;">
                       Register on Namecheap →
                    </a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("All trending domains found in this cycle are already taken. Try changing the TLD in the sidebar.")

st.divider()
st.caption("KASMI DEEP NEWS 2026 | Powered by Trafilatura & WHOIS Protocols")
