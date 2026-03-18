import streamlit as st
import google.generativeai as genai
import whois
import time
import random
import re

# --- 1. PRO SaaS UI CONFIG ---
st.set_page_config(page_title="Gemini Domain AI", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #020617; color: #f1f5f9; }
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #020617); }
    
    .domain-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: 0.3s;
    }
    .domain-card:hover { border-color: #6366f1; transform: translateY(-2px); }
    .domain-name { font-size: 1.3rem; font-weight: 800; color: #ffffff; }
    .status-badge { background: #064e3b; color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
    .buy-link { background: #6366f1; color: white !important; padding: 10px 24px; border-radius: 12px; text-decoration: none; font-weight: 700; }
    .main-title { font-size: 3.5rem; font-weight: 800; background: linear-gradient(to right, #ffffff, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GEMINI AI SETUP ---
def generate_names_with_gemini(api_key, subject, style, tld):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Act as a professional brand naming expert. 
        Generate 30 unique, catchy, and brandable domain names for the subject: '{subject}'.
        Style: {style}.
        Target Extension: {tld}.
        Rules:
        1. Do NOT include the extension {tld} in the names.
        2. No hyphens or spaces.
        3. Provide ONLY a comma-separated list of names.
        4. Focus on short, memorable names.
        """
        
        response = model.generate_content(prompt)
        # Clean the response and split into a list
        raw_names = response.text.replace(" ", "").split(",")
        return [re.sub(r'[^a-zA-Z0-9]', '', name) for name in raw_names]
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return []

# --- 3. DOMAIN CHECKER ---
def check_domain(domain):
    try:
        w = whois.whois(domain)
        return w.registrar is None
    except:
        return True

# --- 4. APP INTERFACE ---
st.markdown('<h1 class="main-title">Gemini Domain AI</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8; font-size:1.2rem; margin-bottom:2rem;">The Smartest AI-Powered Domain Discovery Tool</p>', unsafe_allow_html=True)

# Sidebar for API Key and Settings
st.sidebar.title("🔐 Setup")
gemini_api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
st.sidebar.info("Get a free key at: [aistudio.google.com](https://aistudio.google.com/)")

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Engine Settings")
name_style = st.sidebar.selectbox("Brand Style", ["Modern & Techy", "Classic & Professional", "Playful & Creative", "Short & Abstract"])
scan_limit = st.sidebar.slider("Scan Limit", 5, 30, 15)

# Main Inputs
col1, col2 = st.columns([2, 1])
with col1:
    subject_input = st.text_input("Describe your business or project:", placeholder="e.g. A luxury sustainable coffee brand for digital nomads")
with col2:
    tld_input = st.selectbox("Extension", [".com", ".ai", ".io", ".net", ".app", ".org", ".co"])

if st.button("🚀 Generate Smart Domains"):
    if not gemini_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar.")
    elif not subject_input:
        st.warning("Please describe your project.")
    else:
        with st.spinner("Gemini is brainstorming names..."):
            names = generate_names_with_gemini(gemini_api_key, subject_input, name_style, tld_input)
            
            if names:
                st.write(f"### 🔎 Checking availability for the best ideas...")
                progress_bar = st.progress(0)
                found = 0
                
                # We limit the check to the user's scan_limit to avoid WHOIS bans
                for i, name in enumerate(names[:scan_limit]):
                    full_domain = f"{name.lower()}{tld_input}"
                    progress_bar.progress((i + 1) / scan_limit)
                    
                    if check_domain(full_domain):
                        found += 1
                        buy_url = f"https://www.namecheap.com/domains/registration/results/?domain={full_domain}"
                        st.markdown(f"""
                            <div class="domain-card">
                                <div>
                                    <span class="domain-name">{full_domain}</span><br>
                                    <span class="status-badge">Available</span>
                                </div>
                                <a href="{buy_url}" target="_blank" class="buy-link">Register</a>
                            </div>
                        """, unsafe_allow_html=True)
                    time.sleep(0.2) # Small delay for stability

                if found == 0:
                    st.info("Gemini suggested great names, but they seem to be taken. Try a different 'Style' in the sidebar!")
                else:
                    st.success(f"Search complete! Found {found} available brandable domains.")
