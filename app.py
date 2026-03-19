import streamlit as st
import requests
import time
import os
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN NEWS", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1 { color: #1E3A8A; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 8px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 KASMI DOMAIN NEWS")
st.write("Generating high-value domain ideas from real-time news.")

# --- 1. API KEYS SETUP ---
with st.sidebar:
    st.header("🔑 API Configuration")
    # Pull from Secrets first, then allow manual override
    gemini_key = st.text_input("Gemini API Key", value=st.secrets.get("GEMINI_API_KEY", ""), type="password")
    gnews_key = st.text_input("GNews Key (Optional)", value=st.secrets.get("GNEWS_KEY", ""), type="password")

    st.header("⚙️ Settings")
    tld = st.selectbox("Extension", ["com", "ai", "io", "co", "net", "org"])
    num_domains = st.slider("Number of Domains", 5, 20, 10)
    max_words = st.selectbox("Max Words", [1, 2, 3], index=1)

# --- 2. THE SMART MODEL PICKER (Prevents 404) ---
def get_best_model(client):
    """Finds the best available model to avoid 404 errors."""
    try:
        models = [m.name for m in client.models.list() if 'generateContent' in m.supported_methods]
        # Priority list (1.5 Flash is best for Free Tier quota)
        priority = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
        
        for p in priority:
            for m in models:
                if p in m:
                    return m.split('/')[-1] # Returns 'gemini-1.5-flash'
        return models[0].split('/')[-1]
    except:
        return "gemini-1.5-flash" # Absolute fallback

# --- 3. NEWS FETCHING ---
def fetch_news():
    headlines = []
    if gnews_key:
        try:
            url = f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gnews_key}"
            r = requests.get(url, timeout=10).json()
            for art in r.get('articles', []):
                headlines.append(f"- {art['title']}")
        except:
            pass
    return "\n".join(headlines)

# --- 4. DOMAIN GENERATION (Prevents 429) ---
def generate_domains(client, model_id, context):
    prompt = f"""
    Analyze these news headlines:
    {context if context else 'Latest tech and business trends'}
    
    Suggest {num_domains} available-style domain names ending in .{tld}.
    Rules: Max {max_words} words, catchy, brandable.
    Format: A Markdown table with columns 'Domain', 'Target Audience', and 'Why it works'.
    """
    
    # Check if we should use Google Search tool (saves quota if we have news)
    tools = [types.Tool(google_search=types.GoogleSearch())] if not context else None

    # RETRY LOGIC for 429 Errors
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a domain name expert and market analyst.",
                    tools=tools,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                st.warning(f"⚠️ Quota hit. Waiting {10 * (attempt+1)}s to retry...")
                time.sleep(10 * (attempt+1))
            else:
                raise e

# --- 5. MAIN APP INTERFACE ---
if st.button("Generate Domain Report ✨"):
    if not gemini_key:
        st.error("❌ Please enter your Gemini API Key in the sidebar.")
    else:
        try:
            # Initialize Client
            client = genai.Client(api_key=gemini_key)
            
            with st.status("Working...", expanded=True) as status:
                # Step 1: Find Model
                st.write("🔍 Finding best AI engine...")
                active_model = get_best_model(client)
                st.write(f"✅ Using Engine: `{active_model}`")
                
                # Step 2: Fetch News
                st.write("📰 Scanning headlines...")
                news_data = fetch_news()
                
                # Step 3: Generate
                st.write("🧠 Brainstorming domains...")
                report = generate_domains(client, active_model, news_data)
                
                status.update(label="Complete!", state="complete")

            st.success("### Suggested Domain Names")
            st.markdown(report)
            
            st.divider()
            st.caption("Made with ❤️ by Youness KASMI | Ensure you check availability on a registrar like Namecheap.")

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
