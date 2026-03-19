import streamlit as st
import requests
import pandas as pd
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS", page_icon="🌐", layout="wide")

# Custom CSS to match your branding
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1 { color: #1E3A8A; font-family: 'Arial'; }
    .stButton>button { background-color: #1E3A8A; color: white; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 KASMI DOMAIN NEWS")
st.subheader("Discover Trending Domain Names from Today's News")

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.header("🔑 API Configuration")
    st.info("Keys are pulled from Streamlit Secrets or entered below.")
    
    # Use Secrets if available, otherwise manual input
    gemini_key = st.text_input("Gemini API Key (Required)", 
                              value=st.secrets.get("GEMINI_API_KEY", ""), type="password")
    
    with st.expander("Optional News API Keys"):
        mediastack_key = st.text_input("MediaStack Key", value=st.secrets.get("MEDIASTACK_KEY", ""), type="password")
        gnews_key = st.text_input("GNews Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
        newsapi_key = st.text_input("NewsAPI.org Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")

    st.header("⚙️ Generation Settings")
    time_range = st.selectbox("News Time Range", ["day", "week", "month"])
    fetch_depth = st.radio("Article Fetch Depth", ["Light (Titles)", "Deep (Full Content)"], index=0)
    max_words = st.slider("Max Words in Domain", 1, 4, 2)
    tld = st.selectbox("Top-Level Domain (TLD)", ["com", "ai", "io", "co", "net", "org"])
    num_domains = st.number_input("Number of Domains", 1, 20, 10)

# --- HELPER FUNCTIONS ---

def fetch_trending_news():
    """Fetches news from various sources based on provided keys."""
    headlines = []
    
    # Example: GNews Fetching
    if gnews_key:
        try:
            url = f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gnews_key}"
            response = requests.get(url).json()
            for article in response.get('articles', []):
                headlines.append(f"{article['title']}: {article['description']}")
        except:
            pass
            
    # Fallback/Default: If no news keys, Gemini can use its built-in Google Search tool
    return headlines

def generate_domains(news_context, client):
    """Uses Gemini to generate domain ideas based on news."""
    
    prompt = f"""
    Based on these trending news stories:
    {news_context}
    
    Generate {num_domains} creative and brandable domain names ending in .{tld}.
    Constraints:
    - Maximum {max_words} words per domain.
    - Focus on high-value, trending topics from the news.
    - Provide a short reasoning for each.
    
    Return the result as a table format.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a domain name expert and brand strategist.",
            tools=[types.Tool(google_search=types.GoogleSearch())] if not news_context else None
        )
    )
    return response.text

# --- MAIN LOGIC ---
if st.button("Generate Domains ✨"):
    if not gemini_key:
        st.error("Please provide a Gemini API Key in the sidebar.")
    else:
        try:
            client = genai.Client(api_key=gemini_key)
            
            with st.spinner("Scanning news and brainstorming domains..."):
                # 1. Get News
                news = fetch_trending_news()
                context = "\n".join(news) if news else "Use your internal Google Search tool to find today's top tech and business news."
                
                # 2. Generate with AI
                result_raw = generate_domains(context, client)
                
                # 3. Display Results
                st.success("Analysis Complete!")
                st.markdown(result_raw)
                
                # 4. Availability Check Helper
                st.info("💡 Note: Availability check is manual. Copy your favorite domain and check on Namecheap or GoDaddy.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")

footer = """<div style='text-align: center; padding: 20px;'>Made with ❤️ by Youness KASMI</div>"""
st.markdown(footer, unsafe_allow_html=True)
