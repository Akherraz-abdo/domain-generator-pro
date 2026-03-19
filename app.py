import streamlit as st
import requests
import re
import xml.etree.ElementTree as ET
import pandas as pd
from collections import Counter

# --- PAGE CONFIG ---
st.set_page_config(page_title="KASMI DOMAIN CHECKER", page_icon="🔍", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { background-color: #ff6600; color: white; border-radius: 5px; height: 3em; font-weight: bold; width: 100%;}
    .available-card { border-left: 5px solid #28a745; padding: 15px; background: white; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 KASMI DOMAIN NEWS & CHECKER")
st.write("Fetching live news trends and verifying Namecheap availability...")

# --- SIDEBAR: API KEYS ---
with st.sidebar:
    st.header("🔑 Namecheap Credentials")
    nc_user = st.text_input("Namecheap Username", value=st.secrets.get("NC_USER", ""))
    nc_api_key = st.text_input("Namecheap API Key", value=st.secrets.get("NC_API_KEY", ""), type="password")
    nc_ip = st.text_input("Your Whitelisted IP", value=st.secrets.get("NC_IP", ""), help="The IP address you whitelisted in Namecheap settings.")
    use_sandbox = st.checkbox("Use Sandbox Mode", value=True, help="Test with Namecheap's Sandbox (requires separate sandbox account/key)")
    
    st.divider()
    st.header("⚙️ News Settings")
    gn_key = st.text_input("GNews Key (Optional)", value=st.secrets.get("GNEWS_KEY", ""), type="password")
    tld = st.selectbox("Extension", ["com", "ai", "io", "net", "org"])

# --- NAMECHEAP AVAILABILITY CHECKER ---
def check_availability(domain_list):
    """Checks a list of domains against Namecheap API (Batch mode)."""
    base_url = "https://api.sandbox.namecheap.com/xml.response" if use_sandbox else "https://api.namecheap.com/xml.response"
    
    params = {
        "ApiUser": nc_user,
        "ApiKey": nc_api_key,
        "UserName": nc_user,
        "Command": "namecheap.domains.check",
        "ClientIp": nc_ip,
        "DomainList": ",".join(domain_list)
    }

    try:
        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.content)
        
        # Namecheap uses XML namespaces
        ns = {'ns': 'http://api.namecheap.com/xml.response'}
        results = root.findall('.//ns:DomainCheckResult', ns)
        
        available_domains = []
        for res in results:
            if res.attrib.get('Available') == 'true':
                available_domains.append({
                    "Domain": res.attrib.get('Domain'),
                    "Price": res.attrib.get('PremiumRegistrationPrice', 'Standard')
                })
        return available_domains
    except Exception as e:
        st.error(f"Namecheap API Error: {e}")
        return []

# --- NEWS & KEYWORD LOGIC ---
def get_news_keywords():
    headlines = ""
    if gn_key:
        try:
            r = requests.get(f"https://gnews.io/api/v4/top-headlines?category=technology&lang=en&apikey={gn_key}").json()
            headlines = " ".join([a['title'] for a in r.get('articles', [])])
        except: pass
    
    if not headlines:
        return ["tech", "cloud", "data", "smart", "bio", "green"] # Fallback

    words = re.findall(r'\b[a-z]{4,}\b', headlines.lower())
    stop_words = {'today', 'latest', 'news', 'with', 'from', 'that', 'this'}
    filtered = [w for w in words if w not in stop_words]
    return [item[0] for item in Counter(filtered).most_common(15)]

# --- MAIN LOGIC ---
if st.button("🚀 Find & Verify Available Domains"):
    if not nc_user or not nc_api_key or not nc_ip:
        st.error("❌ Namecheap Username, API Key, and Whitelisted IP are required.")
    else:
        with st.status("Analyzing Market Trends...", expanded=True) as status:
            # 1. Get Keywords from News
            st.write("📰 Scraping latest news...")
            keywords = get_news_keywords()
            
            # 2. Generate Candidate List
            st.write("💡 Brainstorming domains...")
            candidates = []
            for i in range(len(keywords) - 1):
                candidates.append(f"{keywords[i]}.{tld}")
                candidates.append(f"{keywords[i]}{keywords[i+1]}.{tld}")
            
            # 3. Check Namecheap (Batch check to save time)
            st.write(f"🔎 Verifying {len(candidates)} domains on Namecheap...")
            available = check_availability(candidates[:50]) # API limit is 50 per call
            
            status.update(label="Scanning Finished!", state="complete")

        # --- OUTPUT ONLY AVAILABLE ---
        if available:
            st.success(f"✅ Found {len(available)} available domains!")
            for item in available:
                with st.container():
                    st.markdown(f"""
                    <div class="available-card">
                        <h3>{item['Domain']}</h3>
                        <p>Status: <b>Available</b> | Price: {item['Price']}</p>
                        <a href="https://www.namecheap.com/domains/registration-results/?domain={item['Domain']}" target="_blank">Register on Namecheap →</a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No available domains found from this news cycle. Try a different TLD.")

st.divider()
st.caption("KASMI DOMAIN NEWS - Namecheap Verified | Ensure your IP is whitelisted in Namecheap Dashboard.")
