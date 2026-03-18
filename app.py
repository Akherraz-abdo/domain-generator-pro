import streamlit as st
import whois
import time
import random
import re

# --- 1. HIGH-END SaaS FRONT END (CSS INJECTION) ---
st.set_page_config(page_title="DomainGen AI Pro", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #020617;
        color: #f1f5f9;
    }

    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #020617);
    }

    /* Professional Card for Domains */
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
        transition: all 0.3s ease;
    }

    .domain-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
        background: rgba(30, 41, 59, 0.9);
    }

    .domain-name {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
    }

    .status-badge {
        background: #064e3b;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .buy-link {
        background: #6366f1;
        color: white !important;
        padding: 10px 24px;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.9rem;
        transition: 0.2s;
    }

    .buy-link:hover {
        background: #4f46e5;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }

    /* Input Styling */
    .stTextInput input {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        color: white !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #ffffff, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE POWER ENGINE (DICTIONARIES) ---
PREFIXES = ["get", "try", "use", "join", "pure", "meta", "hyper", "neo", "smart", "open", "cloud", "fast", "easy", "top", "prime", "base", "next", "vibe", "sky", "zen", "alpha"]
SUFFIXES = ["hub", "ly", "ify", "app", "hq", "lab", "studio", "io", "base", "flow", "stack", "grid", "node", "pulse", "logic", "mint", "layer", "way", "bit", "box", "link", "desk"]
ING_VERBS = ["coding", "scaling", "sharing", "building", "moving", "thinking", "growing", "mining", "making", "streaming", "tracking", "trading", "paying", "mapping", "gaming"]
POWER_WORDS = ["expert", "master", "ninja", "vault", "secure", "global", "direct", "rapid", "elite", "prime", "level", "core"]

def check_domain(domain):
    try:
        w = whois.whois(domain)
        if w.registrar is None: return True
        return False
    except:
        return True

# --- 3. THE APP LAYOUT ---
st.markdown('<h1 class="main-title">DomainGen Pro</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#94a3b8; font-size:1.2rem; margin-bottom:2rem;">AI-Driven Domain Combiner with WHOIS Verification</p>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_input("", placeholder="Enter keywords (e.g. coffee, crypto, fitness)...")
    
with col2:
    tld = st.selectbox("", [".com", ".net", ".io", ".ai", ".app", ".org", ".co"])

# Advanced Options Sidebar
st.sidebar.markdown("### 🛠️ Generation Engine")
limit = st.sidebar.slider("Scan Limit", 10, 100, 30)
use_ing = st.sidebar.toggle("Include -ING Verbs", True)
use_pre = st.sidebar.toggle("Include Prefixes", True)
use_suf = st.sidebar.toggle("Include Suffixes", True)

if st.button("🚀 Generate Ton of Domains"):
    if not user_input:
        st.error("Please enter keywords.")
    else:
        keywords = [k.strip().lower() for k in user_input.split(",")]
        candidates = set()

        for kw in keywords:
            if not kw: continue
            # Basic
            candidates.add(kw)
            # Combinations
            if use_pre:
                for p in PREFIXES: candidates.add(f"{p}{kw}")
            if use_suf:
                for s in SUFFIXES: candidates.add(f"{kw}{s}")
            if use_ing:
                for v in ING_VERBS:
                    candidates.add(f"{v}{kw}")
                    candidates.add(f"{kw}{v}")
            # Power
            for pw in POWER_WORDS:
                candidates.add(f"{pw}{kw}")
                candidates.add(f"{kw}{pw}")

        raw_list = list(candidates)
        random.shuffle(raw_list)
        
        st.write(f"### 🔎 Scanning {limit} of {len(raw_list)} variations...")
        
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
                        <a href="{buy_url}" target="_blank" class="buy-link">Register Domain</a>
                    </div>
                """, unsafe_allow_html=True)
            
            # Anti-rate limit
            time.sleep(0.1)

        if found == 0:
            st.warning("No available domains found in this batch. Try adding more keywords!")
        else:
            st.success(f"Search Complete! Found {found} gems.")