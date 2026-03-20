import streamlit as st
import pandas as pd
import zipfile
import requests
import io

st.set_page_config(page_title="Domain Hunter Pro", layout="wide")

st.title("🎯 Domain Hunter Pro")
st.subheader("Official GoDaddy Expired Inventory Search")

# 1. Provide the Link to the Data
st.info("Step 1: Go to [GoDaddy Inventory](https://www.godaddy.com/auctions/container/inventory-files) and download the 'Expired Auctions (all_expiry.csv.zip)' file.")

# 2. File Uploader
uploaded_file = st.file_uploader("Step 2: Upload the 'all_expiry.csv.zip' file here", type=["zip"])

if uploaded_file is not None:
    with st.spinner("Processing thousands of domains..."):
        # Unzip and Read the CSV
        with zipfile.ZipFile(uploaded_file) as z:
            # Get the name of the csv file inside the zip
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                # Read CSV (GoDaddy files are large, we use low_memory=False)
                df = pd.DataFrame()
                # We only need specific columns to save memory
                cols_to_use = ['domainName', 'bidCount', 'currentPrice', 'auctionEndTime', 'valuation']
                
                try:
                    df = pd.read_csv(f, use_cols=lambda c: c in cols_to_use if cols_to_use else True)
                except:
                    # Fallback if columns are named differently
                    df = pd.read_csv(f)

        # UI Filters
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            keyword = st.text_input("Search Keyword", placeholder="e.g. tech, crypto, coffee")
        with col2:
            max_price = st.number_input("Max Price ($)", value=1000)
        with col3:
            min_val = st.number_input("Min Valuation ($)", value=0)

        # Filtering Logic
        if keyword:
            filtered_df = df[df['domainName'].str.contains(keyword, case=False, na=False)]
        else:
            filtered_df = df

        if 'currentPrice' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['currentPrice'] <= max_price]
        
        if 'valuation' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['valuation'] >= min_val]

        # Results
        st.success(f"Found {len(filtered_df)} domains matching your criteria.")
        
        # Sort by best value
        if 'valuation' in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by='valuation', ascending=False)

        st.dataframe(filtered_df, use_container_width=True)

        # Download button for filtered results
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download My List", csv, "my_domains.csv", "text/csv")
else:
    st.warning("Waiting for you to upload the GoDaddy Inventory Zip file.")

st.markdown("""
---
**Why this works:**  
This app doesn't 'scrape' - it processes raw inventory data.  
1. **No Bans:** You won't get blocked by Cloudflare.  
2. **More Data:** You get the full GoDaddy list (usually 100,000+ domains).  
3. **Speed:** It's much faster than waiting for a scraper to click through pages.
""")
