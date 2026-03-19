import streamlit as st
import requests
import re
import whois
import socket
import trafilatura
import random
import pandas as pd
from collections import Counter

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DYNAMIC NEWS", page_icon="🔥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #e63946; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; }
    .available-card { 
        background-color: white; padding: 20px; border-radius: 12px; border-left: 10px solid #e63946;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;
    }
    .keyword-pill { background: #f1faee; color: #1d3557; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; margin: 2px; display: inline-block; border: 1px solid #a8dadc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 KASMI DYNAMIC DOMAIN NEWS")
st.write("Randomized Deep-Scraping Engine: Every run is unique.")

# --- SIDEBAR: CONFIG ---
with st.sidebar:
    st.header("🔑 News API Keys")
    gn_key = st.text_input("GNews Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    napi_key = st.text_input("NewsAPI Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")
    m_key = st.text_input("MediaStack Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
    curr_key = st.text_input("Currents Key", value=st.secrets.get("CURRENTS_KEY", ""), type="password")

    st.divider()
    st.header("🎯 Targeting")
    user_topic = st.text_input("Custom Topic (Leave blank for random)", "")
    tld = st.selectbox("TLD", ["com", "ai", "io", "net", "org", "co"])
    
    st.header("⚙️ Engine")
    scrape_limit = st.slider("Articles to Scrape", 3, 10, 5)
    max_checks = st.slider("Availability Checks", 5, 20, 10)

# --- NICHES FOR RANDOMIZATION ---
NICHES = [
    "Artificial Intelligence", "SaaS Business", "Green Energy", "Quantum Computing",
    "Space Exploration", "Cybersecurity", "Electric Vehicles", "Biohacking", 
    "Remote Work Tools", "Metaverse", "Robotics", "Fintech", "HealthTech", 
    "E-commerce Trends", "Gaming Hardware", "Web3", "Climate Change Solutions"
]

# --- NEWS & DEEP SCRAPING LOGIC ---
def fetch_news_urls(query):
    """Fetches titles and URLs using specific queries to ensure fresh results."""
    articles = []
    
    # Randomize the page to get different results from the same query
    random_page = random.randint(1, 3)

    # 1. GNews (Using /search instead of /top-headlines for more variety)
    if gn_key:
        try:
            url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=10&apikey={gn_key}"
            r = requests.get(url, timeout=5).json()
            for a in r.get('articles', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass
    
    # 2. NewsAPI (Using /everything for deeper archives)
    if napi_key:
        try:
            url = f"https://newsapi.org/v2/everything?q={query}&language=en&pageSize=10&sortBy=publishedAt&apiKey={napi_key}"
            r = requests.get(url, timeout=5).json()
            for a in r.get('articles', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass

    # 3. MediaStack
    if m_key:
        try:
            url = f"http://api.mediastack.com/v1/news?access_key={m_key}&languages=en&keywords={query}&limit=10"
            r = requests.get(url, timeout=5).json()
            for a in r.get('data', []): articles.append({'title': a['title'], 'url': a['url']})
        except: pass

    return articles

def scrape_article_content(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded)
    except: return ""

# --- AVAILABILITY LOGIC (WHOIS) ---
def is_available(domain):
    try:
        socket.gethostbyname(domain)
        return False
    except:
        try:
            w = whois.whois(domain)
            return not w.registrar and not w.creation_date
        except: return True

# --- KEYWORD ENGINE ---
def extract_deep_keywords(text):
    words = re.findall(r'\b[a-z]{5,12}\b', text.lower())
    stop_words = {'today', 'latest', 'news', 'people', 'would', 'could', 'should', 'about', 'their', 'business', 'technology'}
    filtered = [w for w in words if w not in stop_words]
    return [item[0] for item in Counter(filtered).most_common(25)]

# --- MAIN APP ---
if st.button("🚀 EXECUTE DYNAMIC DEEP SCAN"):
    # 1. Pick a Topic
    target_topic = user_topic if user_topic else random.choice(NICHES)
    
    if not any([gn_key, napi_key, m_key, curr_key]):
        st.error("Please add at least one News API Key.")
    else:
        with st.status(f"Scanning News for '{target_topic}'...", expanded=True) as status:
            # 2. Fetch URLs
            st.write(f"📡 Querying APIs for fresh news about: **{target_topic}**")
            articles = fetch_news_urls(target_topic)
            
            if not articles:
                st.error("No articles found for this topic. Try another keyword.")
            else:
                # RANDOMIZE article order so every run uses different text
                random.shuffle(articles)
                
                # 3. Deep Scrape
                st.write(f"📝 Scraping content from {scrape_limit} random articles...")
                combined_text = ""
                for i, art in enumerate(articles[:scrape_limit]):
                    st.write(f"  → Processing: {art['title'][:60]}...")
                    content = scrape_article_content(art['url'])
                    combined_text += f" {art['title']} {content}"
                
                # 4. Extract Keywords
                keywords = extract_deep_keywords(combined_text)
                random.shuffle(keywords) # Mix up the order of domains generated
                
                # 5. Generate & Check
                st.write(f"🔎 Verifying {max_checks} unique domain combinations...")
                available_ones = []
                
                candidates = []
                for i in range(len(keywords) - 1):
                    # Variety of patterns
                    candidates.append(f"{keywords[i]}.{tld}")
                    candidates.append(f"{keywords[i]}{keywords[i+1]}.{tld}")
                    candidates.append(f"{keywords[i]}labs.{tld}")
                
                # Remove duplicates and shuffle candidates
                candidates = list(set(candidates))
                random.shuffle(candidates)
                
                for d in candidates[:max_checks]:
                    if is_available(d):
                        available_ones.append(d)
                
                status.update(label="Deep Scan Finished!", state="complete")

        # --- OUTPUT ---
        st.write(f"### 🧪 Industry Keywords Found in '{target_topic}':")
        kw_html = "".join([f"<span class='keyword-pill'>{k}</span>" for k in keywords[:12]])
        st.markdown(kw_html, unsafe_allow_html=True)

        st.divider()

        if available_ones:
            st.success(f"💎 Found {len(available_ones)} Available Domains!")
            cols = st.columns(2)
            for idx, d in enumerate(available_ones):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class="available-card">
                        <span style="font-size: 20px; color: #e63946; font-weight: bold;">{d}</span><br>
                        <small>✅ Status: AVAILABLE</small><br><br>
                        <a href="https://www.namecheap.com/domains/registration-results/?domain={d}" target="_blank" 
                           style="background: #e63946; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 0.8em;">
                           Register Now →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No available domains found this time. Try clicking 'Execute' again to scrape different articles!")

st.divider()
st.caption("KASMI DYNAMIC NEWS | Randomization Engine Active | WHOIS Verification")
