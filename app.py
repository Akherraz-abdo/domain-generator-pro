import streamlit as st
import requests
import time
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS", page_icon="🌐", layout="wide")

# Custom CSS to match your branding
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1 { color: #1E3A8A; font-family: 'Arial'; }
    .stButton>button { background-color: #1E3A8A; color: white; width: 100%; border-radius: 5px; padding: 10px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 KASMI DOMAIN NEWS")
st.subheader("Discover Trending Domain Names from Today's News")

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.header("🔑 API Configuration")
    st.info("Keys are pulled from Streamlit Secrets or entered below.")
    
    gemini_key = st.text_input("Gemini API Key (Required)", 
                              value=st.secrets.get("GEMINI_API_KEY", ""), type="password")
    
    with st.expander("Optional News API Keys"):
        gnews_key = st.text_input("GNews Key", value=st.secrets.get("GNEWS_KEY", ""), type="password")
        newsapi_key = st.text_input("NewsAPI.org Key", value=st.secrets.get("NEWSAPI_KEY", ""), type="password")

    st.header("⚙️ Generation Settings")
    time_range = st.selectbox("News Time Range", ["day", "week", "month"])
    max_words = st.slider("Max Words in Domain", 1, 4, 2)
    tld = st.selectbox("Top-Level Domain (TLD)",["com", "ai", "io", "co", "net", "org"])
    num_domains = st.number_input("Number of Domains", 1, 20, 10)

# --- HELPER FUNCTIONS ---
def fetch_trending_news():
    """Fetches news from various sources based on provided keys."""
    headlines =[]
    if gnews_key:
        try:
            url = f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gnews_key}"
            response = requests.get(url).json()
            for article in response.get('articles',[]):
                headlines.append(f"- {article['title']}: {article['description']}")
        except:
            pass
    elif newsapi_key:
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={newsapi_key}"
            response = requests.get(url).json()
            for article in response.get('articles',[]):
                headlines.append(f"- {article['title']}: {article.get('description', '')}")
        except:
            pass
    return headlines

def generate_domains_with_retry(news_context, client, retries=2):
    """Generates domains with automatic retry for 429 Rate Limit errors."""
    
    prompt = f"""
    Based on these trending news stories:
    {news_context}
    
    Generate {num_domains} creative, brandable domain names ending in .{tld}.
    Constraints:
    - Maximum {max_words} words per domain.
    - Focus on high-value, trending topics from the news.
    - Provide a short reasoning for each.
    
    Format the output EXACTLY as a Markdown table with columns: Suggested Domain | Reasoning from AI | Availability Check
    (Leave the Availability column as 'Manual Check').
    """
    
    # Optimize Quota: Only use Google Search if we didn't get any news from the external APIs
    use_search = True if "Use your internal Google Search" in news_context else False
    tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else None
    
    for attempt in range(retries):
        try:
            # FIX: Switched to gemini-1.5-flash to bypass the limit:0 error on the Free Tier
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a domain name expert and brand strategist.",
                    tools=tools,
                    temperature=0.7,
                )
            )
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            # FIX: Auto-Retry logic if you hit a rate limit
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < retries - 1:
                    st.warning(f"⚠️ Google API is busy. Auto-retrying in 10 seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(10)
                else:
                    raise Exception("Google API Quota Exhausted. Please check your billing plan or try again tomorrow.")
            else:
                raise e # Throw normal errors (like invalid API keys)

# --- MAIN LOGIC ---
if st.button("Generate Domains ✨"):
    if not gemini_key:
        st.error("❌ Please provide a Gemini API Key in the sidebar.")
    else:
        try:
            client = genai.Client(api_key=gemini_key)
            
            with st.spinner("1️⃣ Scanning the latest news..."):
                news = fetch_trending_news()
                
                if news:
                    # Send top 10 articles to save tokens
                    context = "\n".join(news[:10]) 
                    st.success(f"Fetched {len(news)} articles from News APIs!")
                else:
                    context = "Use your internal Google Search tool to find today's top tech and business news."
                    st.info("No News API keys provided. Relying on Gemini's internal web search...")
            
            with st.spinner("2️⃣ Brainstorming domain names (this might take a few seconds)..."):
                result_raw = generate_domains_with_retry(context, client)
                
                st.success("✅ Analysis Complete!")
                st.markdown(result_raw)
                
                st.info("💡 Note: Availability check is manual. Copy your favorite domain and check on Namecheap or GoDaddy.")
                
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

# Footer
st.markdown("<hr><div style='text-align: center; color: gray;'>Made with ❤️ by Youness KASMI</div>", unsafe_allow_html=True)
