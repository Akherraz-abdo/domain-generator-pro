import streamlit as st
import requests
import re
import pandas as pd
from collections import Counter

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #007bff; color: white; border-radius: 5px; height: 3em; font-weight: bold;}
    .keyword-tag { background-color: #e9ecef; padding: 5px 10px; border-radius: 15px; margin: 5px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 KASMI DOMAIN NEWS")
st.subheader("Algorithmic Domain Discovery (No-AI Engine)")

# --- SIDEBAR: API KEYS ---
with st.sidebar:
    st.header("🔑 News API Configuration")
    st.info("The app will extract keywords from these sources to build domains.")
    
    gn_key = st.text_input("GNews API Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    napi_key = st.text_input("NewsAPI.org Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")
    m_key = st.text_input("MediaStack Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
    curr_key = st.text_input("Currents API Key", value=st.secrets.get("CURRENTS_KEY", ""), type="password")

    st.header("⚙️ Domain Settings")
    tld = st.selectbox("Extension", ["com", "ai", "io", "co", "net", "org"])
    max_words = st.slider("Words per Domain", 1, 3, 2)
    min_word_length = st.slider("Minimum Keyword Length", 3, 6, 4)

# --- NEWS FETCHING ENGINE ---
def fetch_all_headlines():
    all_text = ""
    sources_count = 0
    
    # 1. GNews
    if gn_key:
        try:
            r = requests.get(f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gn_key}", timeout=5).json()
            all_text += " ".join([a['title'] for a in r.get('articles', [])])
            sources_count += 1
        except: pass

    # 2. NewsAPI
    if napi_key:
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={napi_key}", timeout=5).json()
            all_text += " ".join([a['title'] for a in r.get('articles', [])])
            sources_count += 1
        except: pass

    # 3. MediaStack
    if m_key:
        try:
            r = requests.get(f"http://api.mediastack.com/v1/news?access_key={m_key}&languages=en&categories=technology", timeout=5).json()
            all_text += " ".join([a['title'] for a in r.get('data', [])])
            sources_count += 1
        except: pass

    # 4. Currents
    if curr_key:
        try:
            headers = {'Authorization': curr_key}
            r = requests.get("https://api.currentsapi.services/v1/latest-news?language=en&category=technology", headers=headers, timeout=5).json()
            all_text += " ".join([a['title'] for a in r.get('news', [])])
            sources_count += 1
        except: pass

    return all_text.lower(), sources_count

# --- KEYWORD EXTRACTION LOGIC (The "Brain") ---
def extract_trending_keywords(text):
    # Remove punctuation and numbers
    words = re.findall(r'\b[a-z]{' + str(min_word_length) + r',}\b', text)
    
    # Stopwords (Words to ignore)
    stop_words = {
        'the', 'and', 'with', 'from', 'that', 'this', 'news', 'today', 'latest', 
        'will', 'says', 'how', 'why', 'top', 'best', 'new', 'for', 'about', 'video'
    }
    
    filtered_words = [w for w in words if w not in stop_words]
    return Counter(filtered_words).most_common(30)

# --- MAIN APP LOGIC ---
if st.button("🚀 Scrape News & Generate Domains"):
    if not any([gn_key, napi_key, m_key, curr_key]):
        st.error("Please provide at least one API Key in the sidebar.")
    else:
        with st.spinner("Scanning Global News Sources..."):
            raw_text, count = fetch_all_headlines()
            
            if not raw_text:
                st.error("Could not fetch news. Check your API keys.")
            else:
                st.success(f"Successfully aggregated news from {count} sources.")
                
                # Extract Keywords
                top_keywords = extract_trending_keywords(raw_text)
                
                # Display Keywords found
                st.write("### 🔥 Trending Keywords Found:")
                kw_cols = st.columns(5)
                for i, (word, freq) in enumerate(top_keywords[:15]):
                    kw_cols[i % 5].markdown(f"<span class='keyword-tag'>{word} ({freq})</span>", unsafe_allow_html=True)

                # Generate Domain Names
                st.write("### 💎 Suggested Domain Portfolio")
                
                domains = []
                words_only = [k[0] for k in top_keywords]
                
                # Combination Logic
                for i in range(len(words_only) - 1):
                    # Single word domain
                    domains.append({
                        "Domain Name": f"{words_only[i]}.{tld}",
                        "Type": "Premium Keyword",
                        "Source Keyword": words_only[i].capitalize()
                    })
                    
                    # Double word domain
                    if max_words >= 2:
                        domains.append({
                            "Domain Name": f"{words_only[i]}{words_only[i+1]}.{tld}",
                            "Type": "Brandable Combo",
                            "Source Keyword": f"{words_only[i]} + {words_only[i+1]}"
                        })
                    
                    # Industry focused (Keyword + AI / Keyword + Tech)
                    if tld != 'ai':
                        domains.append({
                            "Domain Name": f"{words_only[i]}ai.{tld}",
                            "Type": "Trend Pivot",
                            "Source Keyword": f"{words_only[i]} + AI"
                        })

                # Display in a clean Table
                df = pd.DataFrame(domains).head(20)
                st.table(df)

st.divider()
st.caption("KASMI DOMAIN NEWS - Algorithmic Discovery Version | Created by Youness KASMI")
