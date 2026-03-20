import streamlit as st
import requests
import pandas as pd

# 1. Get your API Key/Secret from https://developer.godaddy.com/keys
GODADDY_KEY = st.sidebar.text_input("GoDaddy API Key")
GODADDY_SECRET = st.sidebar.text_input("GoDaddy API Secret", type="password")

def get_godaddy_domains(query):
    url = f"https://api.godaddy.com/v1/domains/suggest?query={query}&waitMs=1000"
    headers = {
        "Authorization": f"sso-key {GODADDY_KEY}:{GODADDY_SECRET}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

st.title("GoDaddy Official Domain Finder")
query = st.text_input("Keyword", "coffee")

if st.button("Search"):
    results = get_godaddy_domains(query)
    # GoDaddy returns a list of domain objects
    df = pd.DataFrame(results)
    st.write(df)
