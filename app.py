import streamlit as st
import whois
import time
import random
import re
import requests

# --- 1. HIGH-END SaaS FRONT END ---
st.set_page_config(page_title="SubjectGen AI Pro", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #020617;
        color: #f1f5f9;
    }
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
    }
    .domain-name { font-size: 1.25rem; font-weight: 800; color: #ffffff; }
    .status-badge { background: #064e3b; color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
    .buy-link { background: #6366f1; color: white !important; padding: 10px 24px; border-radius: 12px; text-decoration: none; font-weight: 700; }
    
    .main-title { font-size: 3rem; font-weight: 800; background: linear-gradient(to right, #ffffff, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RESEARCH ENGINE (WIKIPEDIA API) ---
def fetch_subject_keywords(subject):
    """Searches Wikipedia for the subject and extracts top keywords."""
    try:
        # Search for the page
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={subject}&format=json"
        search_res = requests.get(search_url).json()
        if not search_res['query']['search']: return []
        
        # Get the summary of the first result
        page_title = search_res['query']['search'][0]['title']
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
        summary_res = requests.get(summary_url).json()
        extract = summary_res.get('extract', '')
        
        # Extract meaningful words (4-10 letters, no common stop words)
        words = re.findall(r'\b[a-zA-Z]{4,10}\b', extract.lower())
        stop_words = {'also', 'from', 'this', 'that', 'with', 'their', 'were', 'which', 'they'}
        return list(set([w for w in words if w not in stop_words]))
    except:
        return []

# --- 3. DOMAIN ENGINE ---
PREFIXES = ["get", "try", "meta", "smart", "cloud", "fast", "easy", "vibe", "zen", "alpha", "pro", "neo"]
SUFFIXES = ["hub", "ly", "ify", "app", "hq", "lab", "io", "base", "flow", "stack", "pulse", "link"]

def check_domain(domain):
    try:
        w = whois.whois(domain)
        return w.registrar is None
    except:
        return True

# --- 4. APP LAYOUT ---
st.markdown('<h1 class="main-title">SubjectGen AI</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8; font-size:1.1rem;">Enter a subject to research and find available domains instantly.</p>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    subject = st.text_input("Enter a Topic (e.g. Artificial Intelligence, Coffee, Space)", "")
    
with col2:
    tld = st.selectbox("Extension", [".com", ".net", ".io", ".ai", ".app", ".org"])

st.sidebar.markdown("### ⚙️ Engine Settings")
limit = st.sidebar.slider("Scan Limit", 10, 50, 20)
auto_research = st.sidebar.toggle("Auto-Research Subject (Wikipedia)", True)

if st.button("🔥 Research & Generate Domains"):
    if not subject:
        st.error("Please enter a subject.")
    else:
        with st.spinner(f"Researching '{subject}' on the web..."):
            # 1. Start with User Keywords
            keywords = [subject.lower().replace(" ", "")]
            
            # 2. Add Research Keywords
            if auto_research:
                web_keywords = fetch_subject_keywords(subject)
                keywords.extend(web_keywords)
                st.info(f"Research found {len(web_keywords)} related terms (e.g., {', '.join(web_keywords[:5])})")

            # 3. Build List
            candidates = set()
            for kw in keywords:
                candidates.add(kw)
                for p in PREFIXES: candidates.add(f"{p}{kw}")
                for s in SUFFIXES: candidates.add(f"{kw}{s}")
                # Cross-keyword combinations
                if len(keywords) > 1:
                    partner = random.choice(keywords)
                    if partner != kw: candidates.add(f"{kw}{partner}")

            raw_list = list(candidates)
            random.shuffle(raw_list)
            
            st.write(f"### 🔎 Scanning for available gems...")
            
            progress_bar = st.progress(0)
            found = 0
            
            for i in range(min(len(raw_list), limit)):
                domain_name = f"{raw_list[i]}{tld}"
                progress_bar.progress((i + 1) / limit)
                
                if check_domain(domain_name):
                    found += 1
                    buy_url = f"https://www.namecheap.com/domains/registration/results/?domain={domain_name}"
                    st.markdown(f"""
                        <div class="domain-card">
                            <div>
                                <span class="domain-name">{domain_name}</span><br>
                                <span class="status-badge">Available</span>
                            </div>
                            <a href="{buy_url}" target="_blank" class="buy-link">Register</a>
                        </div>
                    """, unsafe_allow_html=True)
                time.sleep(0.1)

            if found == 0:
                st.warning("No available domains found. Try a different extension or subject.")
