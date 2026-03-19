import streamlit as st
import requests
import time
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 5px; width: 100%; }
    .api-box { padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 KASMI DOMAIN NEWS")
st.write("Discover Trending Domain Names from Today's News using Multi-API Aggregation.")

# --- SIDEBAR: API CONFIGURATION ---
with st.sidebar:
    st.header("🔑 API Keys")
    st.caption("Register at the links below to get your keys.")
    
    # News Sources
    m_key = st.text_input("MediaStack API Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
    gn_key = st.text_input("GNews API Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    napi_key = st.text_input("NewsAPI.org Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")
    curr_key = st.text_input("Currents API Key", value=st.secrets.get("CURRENTS_KEY", ""), type="password")
    
    # Gemini (Required for the Brainstorming part)
    gemini_key = st.text_input("Gemini API Key (Required)", value=st.secrets.get("GEMINI_API_KEY", ""), type="password")

    st.header("⚙️ Generation Settings")
    tld = st.selectbox("TLD", ["com", "ai", "io", "co", "net", "org"])
    max_words = st.slider("Max Words", 1, 4, 2)
    num_domains = st.number_input("Count", 5, 20, 10)

# --- NEWS FETCHING LOGIC ---
def get_all_news():
    headlines = []
    
    # 1. GNews
    if gn_key:
        try:
            res = requests.get(f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gn_key}", timeout=5).json()
            headlines.extend([a['title'] for a in res.get('articles', [])])
        except: st.warning("GNews failed to connect.")

    # 2. NewsAPI.org
    if napi_key:
        try:
            res = requests.get(f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={napi_key}", timeout=5).json()
            headlines.extend([a['title'] for a in res.get('articles', [])])
        except: st.warning("NewsAPI failed to connect.")

    # 3. MediaStack
    if m_key:
        try:
            res = requests.get(f"http://api.mediastack.com/v1/news?access_key={m_key}&languages=en&categories=technology", timeout=5).json()
            headlines.extend([a['title'] for a in res.get('data', [])])
        except: st.warning("MediaStack failed to connect.")

    # 4. Currents
    if curr_key:
        try:
            headers = {'Authorization': curr_key}
            res = requests.get("https://api.currentsapi.services/v1/latest-news?language=en&category=technology", headers=headers, timeout=5).json()
            headlines.extend([a['title'] for a in res.get('news', [])])
        except: st.warning("Currents API failed to connect.")

    return list(set(headlines)) # Remove duplicates

# --- DOMAIN GENERATION ---
def brainstorm_domains(news_list):
    if not gemini_key:
        return "Please provide a Gemini Key to generate reasoning."
    
    # We use a very stable model string to avoid 404
    client = genai.Client(api_key=gemini_key)
    model_name = "gemini-1.5-flash" # High quota, very stable
    
    prompt = f"""
    Based on these headlines: {str(news_list[:15])}
    Suggest {num_domains} brandable domains ending in .{tld}.
    Max {max_words} words. 
    Provide a table with: Domain Name | AI Reasoning | Market Potential (1-10)
    """
    
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "❌ AI Quota Full. I found the news but can't brainstorm right now. Please wait 60 seconds."
        return f"❌ AI Error: {e}"

# --- MAIN UI ---
if st.button("Generate Domains from News"):
    if not any([m_key, gn_key, napi_key, curr_key]):
        st.error("Please provide at least one News API Key in the sidebar.")
    elif not gemini_key:
        st.error("Gemini Key is required for the Brainstorming step.")
    else:
        with st.status("Aggregating News Sources...", expanded=True) as status:
            st.write("📡 Connecting to News APIs...")
            news = get_all_news()
            
            if not news:
                st.error("No news found. Check your API keys or internet connection.")
            else:
                st.write(f"✅ Found {len(news)} trending topics.")
                st.write("🧠 AI is brainstorming domains...")
                results = brainstorm_domains(news)
                status.update(label="Complete!", state="complete")
                
                st.success("### Suggested Domain Names")
                st.markdown(results)
                
                with st.expander("See Raw News Headlines Used"):
                    for h in news:
                        st.write(f"• {h}")

st.divider()
st.caption("KASMI DOMAIN NEWS - Built for GitHub & Streamlit")
